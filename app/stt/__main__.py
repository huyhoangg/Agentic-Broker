"""STT worker: claims PENDING chunks, transcribes via Groq Whisper, saves transcripts."""
import logging
import os
import signal
import sys
import threading
import time

from .. import config, db, storage
from ..heartbeat import Heartbeat
from . import engines

log = logging.getLogger("stt")
stop_event = threading.Event()


def process_chunk(chunk: dict, hb: Heartbeat):
    cid = chunk["id"]
    hb.set_task(f"transcribing chunk {cid}")
    log.info("chunk %s: transcribing (attempt %s)", cid, chunk["attempts"])

    try:
        audio = storage.download(chunk["storage_path"])
        os.makedirs(config.TMP_DIR, exist_ok=True)
        tmp_path = os.path.join(config.TMP_DIR, f"chunk_{cid}.mp3")
        with open(tmp_path, "wb") as f:
            f.write(audio)

        text = engines.transcribe(tmp_path)
        os.remove(tmp_path)

        if text is None:
            raise RuntimeError("groq stt returned no text")

        transcript = db.fetch_one(
            """
            INSERT INTO transcripts (audio_chunk_id, live_session_id, text, stt_model, language)
            VALUES (%s, %s, %s, %s, 'vi')
            ON CONFLICT (audio_chunk_id) DO NOTHING
            RETURNING id
            """,
            (cid, chunk["live_session_id"], text, config.WHISPER_MODEL),
        )

        if config.ANALYZE_WITH_LLM and transcript:
            hb.set_task(f"analyzing chunk {cid}")
            analysis = engines.analyze(text)
            if analysis:
                db.execute(
                    "UPDATE transcripts SET analysis = %s, analyzed_at = NOW() WHERE id = %s",
                    (analysis, transcript["id"]),
                )

        db.execute(
            """
            UPDATE audio_chunks
            SET status = 'COMPLETED', transcribed_at = NOW(), updated_at = NOW(), error = NULL
            WHERE id = %s
            """,
            (cid,),
        )
        db.execute(
            "UPDATE jobs SET status = 'COMPLETED', finished_at = NOW() WHERE id = %s",
            (chunk.get("job_id"),),
        )
        log.info("chunk %s completed: %s", cid, text[:80])

    except Exception as e:
        log.exception("chunk %s failed: %s", cid, e)
        if chunk["attempts"] >= config.STT_MAX_ATTEMPTS:
            db.execute(
                "UPDATE audio_chunks SET status = 'FAILED', error = %s, updated_at = NOW() WHERE id = %s",
                (str(e), cid),
            )
        else:
            db.execute(
                "UPDATE audio_chunks SET status = 'PENDING', worker_id = NULL, updated_at = NOW() WHERE id = %s",
                (cid,),
            )
        db.execute(
            "UPDATE jobs SET status = 'FAILED', finished_at = NOW(), error = %s WHERE id = %s",
            (str(e), chunk.get("job_id")),
        )
    finally:
        hb.set_task("idle")


def main():
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s"
    )

    if not config.SUPABASE_URL:
        sys.exit("Missing SUPABASE_URL in environment")
    if not config.GROQ_API_KEY:
        sys.exit("Missing GROQ_API_KEY in environment")

    wid = config.worker_id("stt")
    hb = Heartbeat("stt", wid)
    hb.start()
    log.info("stt %s started", wid)

    while not stop_event.is_set():
        try:
            chunk = db.claim_chunk(wid)
        except Exception as e:
            log.exception("claim error: %s", e)
            chunk = None
        if chunk:
            process_chunk(chunk, hb)
            continue
        stop_event.wait(config.STT_POLL_INTERVAL)

    hb.stop()
    log.info("stt stopped")


if __name__ == "__main__":
    main()
