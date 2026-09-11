"""Capture worker: claims DISCOVERED sessions, records ffmpeg segments,
uploads each chunk to Supabase Storage and registers PENDING audio_chunks."""
import glob
import logging
import os
import shutil
import signal
import subprocess
import sys
import threading
import time

from .. import config, db, storage, telegram
from ..heartbeat import Heartbeat

log = logging.getLogger("capture")
stop_event = threading.Event()

_ffmpeg = shutil.which("ffmpeg")


def find_ffmpeg() -> str:
    global _ffmpeg
    if _ffmpeg:
        return _ffmpeg
    import imageio_ffmpeg

    _ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    return _ffmpeg


def upload_pending_segments(session: dict, workdir: str, uploaded: set):
    """Upload every finished segment (all except the still-being-written last one)."""
    files = sorted(glob.glob(os.path.join(workdir, "part_*.mp3")))
    for path in files[:-1] if len(files) > 1 else []:
        if path in uploaded:
            continue
        seq = session["base_sequence"] + int(os.path.basename(path)[5:9])
        _register_chunk(session, path, seq)
        uploaded.add(path)


def _register_chunk(session: dict, path: str, seq: int):
    size = os.path.getsize(path)
    if size < 1024:
        log.warning("session #%s chunk %s too small (%sB), skipped", session["id"], seq, size)
        return
    storage_path = f"audio/{session['id']}/chunk_{seq:04d}.mp3"
    storage.upload_audio(path, storage_path)
    db.execute(
        """
        INSERT INTO audio_chunks (live_session_id, sequence, storage_path, size_bytes, status)
        VALUES (%s, %s, %s, %s, 'PENDING')
        ON CONFLICT (live_session_id, sequence) DO NOTHING
        """,
        (session["id"], seq, storage_path, size),
    )
    log.info("session #%s chunk %s registered (%s KB)", session["id"], seq, size // 1024)


def _finish_session(sid: int, has_chunks: bool, job_id, error: str | None = None):
    if has_chunks:
        db.execute(
            """
            UPDATE live_sessions
            SET status = 'ENDED', ended_at = NOW(), updated_at = NOW()
            WHERE id = %s AND status = 'CAPTURING'
            """,
            (sid,),
        )
        log.info("session #%s ended", sid)
    else:
        db.execute(
            """
            UPDATE live_sessions
            SET status = 'FAILED', error = %s, ended_at = NOW(), updated_at = NOW()
            WHERE id = %s AND status = 'CAPTURING'
            """,
            (error or "no audio captured (stream url expired?)", sid),
        )
        log.warning("session #%s failed", sid)
    if job_id:
        db.execute(
            "UPDATE jobs SET status = %s, finished_at = NOW(), error = %s WHERE id = %s",
            ("COMPLETED" if has_chunks else "FAILED", error, job_id),
        )


def run_capture(session: dict, handle: str, hb: Heartbeat):
    sid = session["id"]
    workdir = os.path.join(config.TMP_DIR, f"session_{sid}_{int(time.time())}")
    os.makedirs(workdir, exist_ok=True)
    uploaded: set = set()
    proc = None
    hb.set_task(f"capturing session {sid}")
    log.info("session #%s: capturing %s", sid, handle)
    telegram.send_message(
        f"🎙️ <b>BẮT ĐẦU THU ÂM</b>\n👤 <code>{handle}</code>\n🆔 Session: <code>#{sid}</code>\n"
        f"⏱️ Chunk: {config.CHUNK_SECONDS}s"
    )

    try:
        proc = subprocess.Popen(
            [
                find_ffmpeg(), "-y",
                "-i", session["stream_url"],
                "-vn",
                "-acodec", "libmp3lame",
                "-ab", "64k",
                "-ac", "1",
                "-f", "segment",
                "-segment_time", str(config.CHUNK_SECONDS),
                "-reset_timestamps", "1",
                os.path.join(workdir, "part_%04d.mp3"),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        while proc.poll() is None and not stop_event.is_set():
            time.sleep(5)
            try:
                upload_pending_segments(session, workdir, uploaded)
            except Exception as e:
                log.warning("session #%s segment sync error: %s", sid, e)

        if stop_event.is_set() and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

        # flush remaining (partial) segments
        for path in sorted(glob.glob(os.path.join(workdir, "part_*.mp3"))):
            if path not in uploaded:
                seq = session["base_sequence"] + int(os.path.basename(path)[5:9])
                _register_chunk(session, path, seq)

        has_chunks = db.fetch_one(
            "SELECT EXISTS(SELECT 1 FROM audio_chunks WHERE live_session_id = %s) AS ok", (sid,)
        )["ok"]
        _finish_session(sid, has_chunks, session.get("job_id"))

    except Exception as e:
        log.exception("session #%s capture error: %s", sid, e)
        _finish_session(sid, False, session.get("job_id"), error=f"capture error: {e}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        hb.set_task("idle")


def main():
    if threading.current_thread() is threading.main_thread():
        try:
            signal.signal(signal.SIGINT, lambda *_: stop_event.set())
            signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
        except (ValueError, OSError):
            pass

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s"
    )

    if not config.SUPABASE_URL:
        sys.exit("Missing SUPABASE_URL in environment")
    find_ffmpeg()

    wid = config.worker_id("capture")
    hb = Heartbeat("capture", wid)
    hb.start()
    log.info(
        "capture %s started (concurrency=%s, chunk=%ss)",
        wid, config.CAPTURE_CONCURRENCY, config.CHUNK_SECONDS,
    )

    threads: list[threading.Thread] = []
    while not stop_event.is_set():
        threads = [t for t in threads if t.is_alive()]
        if len(threads) < config.CAPTURE_CONCURRENCY:
            try:
                session = db.claim_session(wid)
            except Exception as e:
                log.exception("claim error: %s", e)
                session = None
            if session:
                src = db.fetch_one("SELECT handle FROM sources WHERE id = %s", (session["source_id"],))
                handle = src["handle"] if src else f"session#{session['id']}"
                t = threading.Thread(target=run_capture, args=(session, handle, hb), daemon=True)
                t.start()
                threads.append(t)
                continue
        stop_event.wait(config.CAPTURE_POLL_INTERVAL)

    for t in threads:
        t.join(timeout=60)
    hb.stop()
    log.info("capture stopped")


if __name__ == "__main__":
    main()
