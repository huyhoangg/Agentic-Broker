"""FastAPI control-plane API: sources CRUD + pipeline views + telemetry console."""
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .. import config, db, storage, tiktok

log = logging.getLogger("api")
app = FastAPI(title="Self-Broker API", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# `kill -USR1 <pid>` dumps all thread stacks to stderr — forensics for wedges.
import faulthandler
import signal as _signal

faulthandler.register(_signal.SIGUSR1)

ROOT_DIR = Path(__file__).resolve().parents[2]
PID_DIR = ROOT_DIR / "tmp"
WORKER_TYPES = ("scanner", "capture", "stt")

# Shared-secret auth for the standalone console (set CONSOLE_TOKEN to enable).
# Health stays open for Render health checks.
CONSOLE_TOKEN = os.getenv("CONSOLE_TOKEN", "")
OPEN_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


@app.middleware("http")
async def auth_guard(request, call_next):
    if CONSOLE_TOKEN and request.url.path not in OPEN_PATHS:
        supplied = request.headers.get("X-Console-Token") or request.query_params.get("token")
        if supplied != CONSOLE_TOKEN:
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
    return await call_next(request)


# Worker process control is only meaningful where the API can spawn processes
# (local machine). On Render, workers are separate services — disable it there.
WORKER_CONTROL = os.getenv("WORKER_CONTROL", "1") in ("1", "true", "yes")


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
    return db.fetch_all(
        """
        SELECT src.*,
               ls.id AS live_session_id, ls.status AS live_status, ls.created_at AS live_since
        FROM sources src
        LEFT JOIN live_sessions ls
               ON ls.source_id = src.id
              AND ls.status IN ('DISCOVERED', 'CAPTURING', 'FINALIZING')
        ORDER BY src.id
        """
    )


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
def chunk_audio(chunk_id: int, token: Optional[str] = None):
    # token also accepted as query param: <audio> tags cannot send headers
    if CONSOLE_TOKEN and token != CONSOLE_TOKEN:
        raise HTTPException(401, "unauthorized")
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


EMBEDDED_WORKERS = os.getenv("EMBEDDED_WORKERS", "1").lower() in ("1", "true", "yes")



@app.on_event("startup")
def startup_event():
    import threading
    from ..telegram import start_telegram_command_poller

    t = threading.Thread(target=start_telegram_command_poller, daemon=True)
    t.start()
    log.info("Started Telegram Bot Command Poller & Price Notifier thread.")

    if EMBEDDED_WORKERS:
        from ..scanner.__main__ import main as scanner_main
        from ..capture.__main__ import main as capture_main
        from ..stt.__main__ import main as stt_main

        threading.Thread(target=scanner_main, daemon=True, name="scanner-worker").start()
        threading.Thread(target=capture_main, daemon=True, name="capture-worker").start()
        threading.Thread(target=stt_main, daemon=True, name="stt-worker").start()
        log.info("Started Embedded Pipeline Workers (scanner, capture, stt).")



# --- script (worker process) control ---

def _pidfile(wtype: str) -> Path:
    return PID_DIR / f"worker_{wtype}.pid"


def _log_file(wtype: str) -> Path:
    return PID_DIR / f"worker_{wtype}.log"


def _alive(pid: Optional[int]) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _read_pid(wtype: str) -> Optional[int]:
    try:
        return int(_pidfile(wtype).read_text().strip())
    except Exception:
        return None


def _find_worker_pids(wtype: str) -> list[int]:
    """PIDs of live worker processes, matched by cmdline to avoid killing recycled PIDs."""
    try:
        out = subprocess.run(
            ["pgrep", "-f", f"python -m app.{wtype}"], capture_output=True, text=True, timeout=5
        )
        pids = []
        for raw in out.stdout.split():
            try:
                pid = int(raw)
            except ValueError:
                continue
            if pid == os.getpid():
                continue
            try:
                cmd = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True, timeout=5
                ).stdout
            except Exception:
                continue
            if f"-m app.{wtype}" in cmd:
                pids.append(pid)
        return pids
    except Exception:
        return []


def _terminate(pid: int, timeout: float = 10):
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.time() + timeout
    while _alive(pid) and time.time() < deadline:
        time.sleep(0.5)
    if _alive(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


@app.get("/scripts")
def list_scripts():
    rows = db.fetch_all(
        """
        SELECT id, type, status, current_task, last_heartbeat,
               EXTRACT(EPOCH FROM (NOW() - last_heartbeat))::int AS hb_age
        FROM workers WHERE type = ANY(%s) ORDER BY last_heartbeat DESC
        """,
        (list(WORKER_TYPES),),
    )
    out = {}
    for wtype in WORKER_TYPES:
        pid = _read_pid(wtype)
        out[wtype] = {
            "pid": pid,
            "alive": _alive(pid) or bool(_find_worker_pids(wtype)),
            "workers": [r for r in rows if r["type"] == wtype][:3],
        }
    return out


@app.post("/scripts/{wtype}/start")
def start_script(wtype: str):
    if not WORKER_CONTROL:
        raise HTTPException(403, "worker control disabled on this deployment")
    if wtype not in WORKER_TYPES:
        raise HTTPException(404, "unknown worker type")
    pid = _read_pid(wtype)
    if _alive(pid):
        raise HTTPException(409, f"{wtype} already running (pid {pid})")
    PID_DIR.mkdir(exist_ok=True)
    logf = open(_log_file(wtype), "ab")
    proc = subprocess.Popen(
        [sys.executable, "-m", f"app.{wtype}"],
        cwd=str(ROOT_DIR), stdout=logf, stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    _pidfile(wtype).write_text(str(proc.pid))
    log.info("started %s (pid %s)", wtype, proc.pid)
    return {"type": wtype, "pid": proc.pid, "status": "started"}


@app.post("/scripts/{wtype}/stop")
def stop_script(wtype: str):
    if wtype not in WORKER_TYPES:
        raise HTTPException(404, "unknown worker type")
    pids = set(_find_worker_pids(wtype))
    pid = _read_pid(wtype)
    if _alive(pid):
        pids.add(pid)
    for p in pids:
        _terminate(p)
    _pidfile(wtype).unlink(missing_ok=True)
    db.execute(
        "UPDATE workers SET status = 'STOPPED', current_task = NULL WHERE type = %s AND status = 'HEALTHY'",
        (wtype,),
    )
    log.info("stopped %s", wtype)
    return {"type": wtype, "status": "stopped", "killed": sorted(pids)}


@app.post("/scripts/{wtype}/restart")
def restart_script(wtype: str):
    stop_script(wtype)
    time.sleep(1)
    return start_script(wtype)


@app.get("/scripts/{wtype}/log")
def script_log(wtype: str, lines: int = 80):
    if wtype not in WORKER_TYPES:
        raise HTTPException(404, "unknown worker type")
    try:
        content = _log_file(wtype).read_text(errors="replace").splitlines()
        return {"log": "\n".join(content[-lines:])}
    except FileNotFoundError:
        return {"log": ""}


# --- audio management ---

@app.get("/audio")
def list_audio(limit: int = 60, session_id: Optional[int] = None):
    rows = db.fetch_all(
        """
        SELECT c.id, c.live_session_id, c.sequence, c.status, c.attempts, c.size_bytes,
               c.storage_path, c.error, c.created_at,
               s.handle, ls.status AS session_status,
               (t.id IS NOT NULL) AS has_transcript
        FROM audio_chunks c
        JOIN live_sessions ls ON ls.id = c.live_session_id
        JOIN sources s ON s.id = ls.source_id
        LEFT JOIN transcripts t ON t.audio_chunk_id = c.id
        WHERE (%s::bigint IS NULL OR c.live_session_id = %s)
        ORDER BY c.id DESC
        LIMIT %s
        """,
        (session_id, session_id, limit),
    )
    stats = db.fetch_one(
        "SELECT COUNT(*) AS total, COALESCE(SUM(size_bytes), 0) AS total_bytes FROM audio_chunks"
    )
    return {"stats": stats, "chunks": rows}


@app.delete("/audio/{chunk_id}")
def delete_chunk(chunk_id: int):
    row = db.fetch_one("SELECT storage_path FROM audio_chunks WHERE id = %s", (chunk_id,))
    if not row:
        raise HTTPException(404, "chunk not found")
    storage.delete(row["storage_path"])
    db.execute("DELETE FROM audio_chunks WHERE id = %s", (chunk_id,))
    log.info("deleted chunk %s (%s)", chunk_id, row["storage_path"])
    return {"deleted": chunk_id}


# --- raw storage browse (incl. legacy folders) ---

@app.get("/storage")
def browse_storage(prefix: str = "", limit: int = 200):
    import requests as rq

    url = f"{config.SUPABASE_URL}/storage/v1/object/list/{config.SUPABASE_BUCKET}"
    res = rq.post(
        url,
        headers={"Authorization": f"Bearer {config.SUPABASE_KEY}", "apikey": config.SUPABASE_KEY},
        json={"prefix": prefix, "limit": limit, "sortBy": {"column": "created_at", "order": "desc"}},
        timeout=15,
    )
    if res.status_code != 200:
        raise HTTPException(502, f"storage list failed: {res.status_code}")
    return res.json()


CONSOLE_DIR = Path(__file__).resolve().parent / "console"

if CONSOLE_DIR.exists():
    app.mount("/console", StaticFiles(directory=CONSOLE_DIR, html=True), name="console")

    @app.get("/console", include_in_schema=False)
    def redirect_console_no_slash():
        return RedirectResponse(url="/console/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
