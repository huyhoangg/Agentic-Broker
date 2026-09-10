"""Scanner worker: detect live sources, register sessions, run recovery sweeps."""
import logging
import signal
import sys
import time

from .. import config, db, telegram, tiktok
from ..heartbeat import Heartbeat

log = logging.getLogger("scanner")

running = True


def _stop(signum, frame):
    global running
    running = False


def seed_sources():
    for handle in config.SOURCE_HANDLES:
        if not handle.startswith("@"):
            handle = f"@{handle}"
        row = db.fetch_one(
            """
            INSERT INTO sources (platform, handle)
            VALUES ('tiktok', %s)
            ON CONFLICT (platform, handle) DO NOTHING
            RETURNING id
            """,
            (handle,),
        )
        if row:
            log.info("seeded source %s", handle)


def scan_sources() -> int:
    sources = db.fetch_all("SELECT id, handle FROM sources WHERE is_active = TRUE ORDER BY id")
    for src in sources:
        if not running:
            break
        handle = src["handle"]
        stream_url = tiktok.resolve_live_stream_url(handle)
        if not stream_url:
            log.info("%s: offline", handle)
            continue

        session = db.fetch_one(
            """
            INSERT INTO live_sessions (source_id, stream_url)
            VALUES (%s, %s)
            ON CONFLICT (source_id)
                WHERE status IN ('DISCOVERED', 'CAPTURING', 'FINALIZING')
            DO NOTHING
            RETURNING id
            """,
            (src["id"], stream_url),
        )
        if session:
            log.info("%s: LIVE -> session #%s created", handle, session["id"])
            telegram.send_message(
                f"🔴 <b>PHÁT HIỆN LIVE MỚI</b>\n"
                f"👤 Kênh: <code>{handle}</code>\n"
                f"🆔 Session: <code>#{session['id']}</code>\n"
                f"⏳ Đang chờ capture worker..."
            )
        else:
            log.info("%s: live, session already active", handle)


def recover() -> dict:
    result = db.fetch_one(
        "SELECT * FROM recover_pipeline(%s, %s, %s, %s)",
        (
            config.CHUNK_STALE_MINUTES,
            config.STT_MAX_ATTEMPTS,
            config.WORKER_STALE_SECONDS,
            config.DISCOVERED_TIMEOUT_MINUTES,
        ),
    )
    if result and any(
        result[k] for k in ("recovered_chunks", "recovered_sessions", "abandoned_sessions", "completed_sessions")
    ):
        log.info("recovery: %s", dict(result))

    # notify newly completed sessions
    done = db.fetch_all(
        """
        UPDATE live_sessions s
        SET chunk_count = (SELECT COUNT(*) FROM audio_chunks c WHERE c.live_session_id = s.id)
        WHERE s.status = 'COMPLETED' AND s.chunk_count = 0 AND s.updated_at > NOW() - INTERVAL '2 minutes'
        RETURNING s.id, s.chunk_count, s.source_id
        """
    )
    for row in done:
        src = db.fetch_one("SELECT handle FROM sources WHERE id = %s", (row["source_id"],))
        log.info("session #%s completed (%s chunks)", row["id"], row["chunk_count"])
        if src:
            telegram.send_message(
                f"✅ <b>HOÀN THÀNH PIPELINE</b>\n"
                f"👤 Kênh: <code>{src['handle']}</code>\n"
                f"🆔 Session: <code>#{row['id']}</code>\n"
                f"🎵 Chunks: <b>{row['chunk_count']}</b>"
            )
    return dict(result) if result else {}


def main():
    global running
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s"
    )

    if not config.SUPABASE_URL:
        sys.exit("Missing SUPABASE_URL in environment")

    wid = config.worker_id("scanner")
    hb = Heartbeat("scanner", wid)
    hb.set_task("starting")
    hb.start()
    log.info("scanner %s started (interval=%ss)", wid, config.CHECK_INTERVAL)

    try:
        seed_sources()
    except Exception as e:
        log.warning("seed sources failed: %s", e)

    while running:
        try:
            hb.set_task("scanning sources")
            scan_sources()
            hb.set_task("recovery sweep")
            recover()
        except Exception as e:
            log.exception("loop error: %s", e)
        hb.set_task("idle")
        for _ in range(int(config.CHECK_INTERVAL)):
            if not running:
                break
            time.sleep(1)

    hb.stop()
    log.info("scanner stopped")


if __name__ == "__main__":
    main()
