import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


# --- Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "broker-agent")
SUPABASE_DB_HOST = os.getenv("SUPABASE_DB_HOST", "aws-0-ap-southeast-2.pooler.supabase.com")
# 6543 = Supavisor transaction pooler (high client limit; session pooler on 5432 caps at 15 clients)
SUPABASE_DB_PORT = _int("SUPABASE_DB_PORT", 6543)
SUPABASE_PW = os.getenv("SUPABASE_PW", "")

# --- Groq ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- Workers ---
WORKER_ID = os.getenv("WORKER_ID") or ""
PORT = _int("PORT", 8000)
CHECK_INTERVAL = _int("CHECK_INTERVAL", 120)
CAPTURE_POLL_INTERVAL = _float("CAPTURE_POLL_INTERVAL", 5)
CAPTURE_CONCURRENCY = _int("CAPTURE_CONCURRENCY", 3)
STT_POLL_INTERVAL = _float("STT_POLL_INTERVAL", 5)
STT_MAX_ATTEMPTS = _int("STT_MAX_ATTEMPTS", 3)
CHUNK_SECONDS = _int("CHUNK_SECONDS", 300)
HEARTBEAT_INTERVAL = _int("HEARTBEAT_INTERVAL", 15)
WORKER_STALE_SECONDS = _int("WORKER_STALE_SECONDS", 90)
CHUNK_STALE_MINUTES = _int("CHUNK_STALE_MINUTES", 10)
DISCOVERED_TIMEOUT_MINUTES = _int("DISCOVERED_TIMEOUT_MINUTES", 30)
TMP_DIR = os.getenv("TMP_DIR", "tmp")
SOURCE_HANDLES = [h.strip() for h in os.getenv("SOURCE_HANDLES", "").split(",") if h.strip()]
ANALYZE_WITH_LLM = os.getenv("ANALYZE_WITH_LLM", "true").lower() in ("1", "true", "yes")
NOTIFY_TELEGRAM = os.getenv("NOTIFY_TELEGRAM", "true").lower() in ("1", "true", "yes")

# Local Postgres DSN (Supavisor transaction pooler). Works everywhere, incl. IPv4-only hosts.
def database_dsn() -> str:
    ref = SUPABASE_URL.split("//")[-1].split(".")[0] if SUPABASE_URL else ""
    user = os.getenv("SUPABASE_DB_USER") or f"postgres.{ref}"
    return (
        f"host={SUPABASE_DB_HOST} port={SUPABASE_DB_PORT} dbname=postgres "
        f"user={user} password={SUPABASE_PW} connect_timeout=10 "
        "keepalives=1 keepalives_idle=30 keepalives_interval=10 keepalives_count=3 "
        "options='-c statement_timeout=15000'"
    )


def worker_id(worker_type: str) -> str:
    import socket
    import os as _os

    return WORKER_ID or f"{worker_type}-{socket.gethostname()}-{_os.getpid()}"
