"""FastAPI control-plane API: sources CRUD + pipeline views + telemetry console."""
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .. import config, db, storage, tiktok

log = logging.getLogger("api")
app = FastAPI(title="Self-Broker API", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

CONSOLE_DIR = Path(__file__).resolve().parent / "console"


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/console/")


class SourceIn(BaseModel):
    handle: str
    platform: str = "tiktok"
    is_active: bool = True


class SourcePatch(BaseModel):
    is_active: Optional[bool] = None
    display_name: Optional[str] = None


@app.get("/health")
def health():
    workers = db.fetch_all(
        """
        SELECT id, type, status, current_task, last_heartbeat,
               EXTRACT(EPOCH FROM (NOW() - last_heartbeat))::int AS seconds_since_heartbeat
        FROM workers ORDER BY type, id
        """
    )
    counts = db.fetch_one(
        """
        SELECT
          (SELECT COUNT(*) FROM sources WHERE is_active) AS active_sources,
          (SELECT COUNT(*) FROM live_sessions WHERE status = 'CAPTURING') AS capturing,
          (SELECT COUNT(*) FROM audio_chunks WHERE status = 'PENDING') AS chunks_pending,
          (SELECT COUNT(*) FROM audio_chunks WHERE status = 'PROCESSING') AS chunks_processing,
          (SELECT COUNT(*) FROM audio_chunks WHERE status = 'FAILED') AS chunks_failed,
          (SELECT COUNT(*) FROM transcripts) AS transcripts_total
        """
    )
    return {"status": "ok", "pipeline": counts, "workers": workers}


# --- sources ---

@app.get("/sources")
def list_sources():
    return db.fetch_all("SELECT * FROM sources ORDER BY id")


@app.post("/sources", status_code=201)
def create_source(body: SourceIn):
    handle = body.handle.strip()
    if not handle.startswith("@"):
        handle = f"@{handle}"
    row = db.fetch_one(
        """
        INSERT INTO sources (platform, handle, display_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (platform, handle) DO UPDATE SET updated_at = NOW()
        RETURNING *
        """,
        (body.platform.lower(), handle, body.display_name or tiktok.fetch_display_name(handle)),
    )
    return row


@app.patch("/sources/{source_id}")
def patch_source(source_id: int, body: SourcePatch):
    row = db.fetch_one(
        """
        UPDATE sources SET
            is_active = COALESCE(%s, is_active),
            display_name = COALESCE(%s, display_name),
            updated_at = NOW()
        WHERE id = %s
        RETURNING *
        """,
        (body.is_active, body.display_name, source_id),
    )
    if not row:
        raise HTTPException(404, "source not found")
    return row


@app.delete("/sources/{source_id}")
def delete_source(source_id: int):
    deleted = db.execute("DELETE FROM sources WHERE id = %s", (source_id,))
    if not deleted:
        raise HTTPException(404, "source not found")
    return {"deleted": source_id}


# --- pipeline views ---

@app.get("/sessions")
def list_sessions(status: Optional[str] = None, limit: int = 50):
    rows = db.fetch_all(
        """
        SELECT s.*, src.handle,
               (SELECT COUNT(*) FROM audio_chunks c WHERE c.live_session_id = s.id) AS chunk_count,
               (SELECT COUNT(*) FROM audio_chunks c WHERE c.live_session_id = s.id AND c.status = 'COMPLETED') AS chunks_completed,
               (SELECT COUNT(*) FROM audio_chunks c WHERE c.live_session_id = s.id AND c.status IN ('PENDING','PROCESSING')) AS chunks_backlog,
               (SELECT COUNT(*) FROM transcripts t WHERE t.live_session_id = s.id) AS transcript_count
        FROM live_sessions s
        JOIN sources src ON src.id = s.source_id
        WHERE (%s::text IS NULL OR s.status = %s)
        ORDER BY s.created_at DESC
        LIMIT %s
        """,
        (status, status, limit),
    )
    return rows


@app.get("/sessions/{session_id}")
def session_detail(session_id: int):
    session = db.fetch_one("SELECT * FROM live_sessions WHERE id = %s", (session_id,))
    if not session:
        raise HTTPException(404, "session not found")
    chunks = db.fetch_all(
        "SELECT * FROM audio_chunks WHERE live_session_id = %s ORDER BY sequence", (session_id,)
    )
    transcripts = db.fetch_all(
        """
        SELECT t.*, c.sequence, c.storage_path
        FROM transcripts t
        JOIN audio_chunks c ON c.id = t.audio_chunk_id
        WHERE t.live_session_id = %s
        ORDER BY c.sequence
        """,
        (session_id,),
    )
    return {"session": session, "chunks": chunks, "transcripts": transcripts}


@app.get("/transcripts")
def list_transcripts(session_id: Optional[int] = None, q: Optional[str] = None, limit: int = 200):
    return db.fetch_all(
        """
        SELECT t.*, c.sequence, c.storage_path, s.handle
        FROM transcripts t
        JOIN audio_chunks c ON c.id = t.audio_chunk_id
        JOIN live_sessions ls ON ls.id = t.live_session_id
        JOIN sources s ON s.id = ls.source_id
        WHERE (%s::bigint IS NULL OR t.live_session_id = %s)
          AND (%s::text IS NULL OR t.text ILIKE '%%' || %s || '%%')
        ORDER BY t.id DESC
        LIMIT %s
        """,
        (session_id, session_id, q, q, limit),
    )


@app.post("/chunks/{chunk_id}/retry")
def retry_chunk(chunk_id: int):
    row = db.fetch_one(
        """
        UPDATE audio_chunks
        SET status = 'PENDING', attempts = 0, error = NULL, worker_id = NULL, updated_at = NOW()
        WHERE id = %s AND status = 'FAILED'
        RETURNING id
        """,
        (chunk_id,),
    )
    if not row:
        raise HTTPException(404, "no FAILED chunk with this id")
    return {"retried": chunk_id}


@app.post("/sessions/{session_id}/retry")
def retry_session_chunks(session_id: int):
    count = db.execute(
        """
        UPDATE audio_chunks
        SET status = 'PENDING', attempts = 0, error = NULL, worker_id = NULL, updated_at = NOW()
        WHERE live_session_id = %s AND status = 'FAILED'
        """,
        (session_id,),
    )
    return {"retried": count}


@app.get("/chunks/{chunk_id}/audio")
def chunk_audio(chunk_id: int):
    row = db.fetch_one(
        "SELECT storage_path FROM audio_chunks WHERE id = %s", (chunk_id,)
    )
    if not row:
        raise HTTPException(404, "chunk not found")
    try:
        url = storage.signed_url(row["storage_path"], expires=300)
    except Exception:
        raise HTTPException(502, "storage sign failed")
    return RedirectResponse(url=url)


@app.post("/recover")
def trigger_recover():
    from ..scanner.__main__ import recover

    return recover()


@app.get("/jobs")
def list_jobs(status: Optional[str] = None, limit: int = 100):
    return db.fetch_all(
        """
        SELECT * FROM jobs
        WHERE (%s::text IS NULL OR status = %s)
        ORDER BY started_at DESC
        LIMIT %s
        """,
        (status, status, limit),
    )


@app.get("/workers")
def list_workers():
    return db.fetch_all("SELECT * FROM workers ORDER BY type, id")


app.mount("/console", StaticFiles(directory=CONSOLE_DIR, html=True), name="console")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
