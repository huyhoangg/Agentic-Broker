import logging
import threading

import psycopg2
import psycopg2.extras

from . import config

log = logging.getLogger("db")

_local = threading.local()


def _connect():
    return psycopg2.connect(config.database_dsn())


def _get_conn():
    conn = getattr(_local, "conn", None)
    if conn is not None and not conn.closed:
        return conn
    conn = _connect()
    _local.conn = conn
    return conn


def _reset_conn():
    conn = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
    _local.conn = None


def _run(query, params, fetch):
    for attempt in range(2):
        conn = _get_conn()
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(query, params)
                    if fetch == "one":
                        return cur.fetchone()
                    if fetch == "all":
                        return cur.fetchall()
                    return cur.rowcount
        except psycopg2.Error as e:
            log.warning("db error (attempt %s): %s", attempt + 1, e)
            _reset_conn()
            if attempt == 1:
                raise
    return None


def fetch_all(query, params=None):
    return _run(query, params, "all") or []


def fetch_one(query, params=None):
    return _run(query, params, "one")


def execute(query, params=None):
    return _run(query, params, "rowcount")


def _claim(worker_id: str, select_sql: str, update_sql: str, extra_sql=None) -> dict | None:
    """Generic single-row claim inside one FOR UPDATE SKIP LOCKED transaction."""
    conn = _get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(select_sql)
                row = cur.fetchone()
                if not row:
                    return None
                cur.execute(update_sql, (worker_id, row["id"]))
                if extra_sql:
                    extra_sql(cur, row)
                return dict(row)
    except psycopg2.Error as e:
        _reset_conn()
        raise


def claim_session(worker_id: str) -> dict | None:
    """Capture worker: oldest DISCOVERED session -> CAPTURING."""

    def extra(cur, session):
        cur.execute(
            "SELECT COALESCE(MAX(sequence) + 1, 0) AS seq FROM audio_chunks WHERE live_session_id = %s",
            (session["id"],),
        )
        session["base_sequence"] = cur.fetchone()["seq"]
        cur.execute(
            """
            INSERT INTO jobs (type, entity_type, entity_id, worker_id, metadata)
            VALUES ('capture', 'live_session', %s, %s, %s)
            RETURNING id
            """,
            (session["id"], worker_id, psycopg2.extras.Json({"stream_url": (session.get("stream_url") or "")[:120]})),
        )
        session["job_id"] = cur.fetchone()["id"]

    return _claim(
        worker_id,
        """
        SELECT * FROM live_sessions
        WHERE status = 'DISCOVERED'
        ORDER BY created_at
        FOR UPDATE SKIP LOCKED
        LIMIT 1
        """,
        """
        UPDATE live_sessions
        SET status = 'CAPTURING', worker_id = %s, started_at = NOW(), updated_at = NOW()
        WHERE id = %s
        """,
        extra,
    )


def claim_chunk(worker_id: str) -> dict | None:
    """STT worker: oldest PENDING chunk -> PROCESSING."""

    def extra(cur, chunk):
        cur.execute(
            """
            INSERT INTO jobs (type, entity_type, entity_id, worker_id, attempt)
            VALUES ('transcribe', 'audio_chunk', %s, %s, %s)
            RETURNING id
            """,
            (chunk["id"], worker_id, chunk["attempts"]),
        )
        chunk["job_id"] = cur.fetchone()["id"]

    return _claim(
        worker_id,
        """
        SELECT * FROM audio_chunks
        WHERE status = 'PENDING'
        ORDER BY created_at
        FOR UPDATE SKIP LOCKED
        LIMIT 1
        """,
        """
        UPDATE audio_chunks
        SET status = 'PROCESSING', worker_id = %s, attempts = attempts + 1, started_at = NOW(), updated_at = NOW()
        WHERE id = %s
        """,
        extra,
    )
