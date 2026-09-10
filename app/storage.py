import logging
import time

import requests

from . import config

log = logging.getLogger("storage")


def _headers(upsert=True):
    headers = {
        "Authorization": f"Bearer {config.SUPABASE_KEY}",
        "apikey": config.SUPABASE_KEY,
    }
    if upsert:
        headers["x-upsert"] = "true"
    return headers


def upload_audio(local_path: str, storage_path: str, content_type="audio/mpeg") -> str:
    """Upload with backoff retry — Supabase Storage rate-limits (429/5xx) under load."""
    url = f"{config.SUPABASE_URL}/storage/v1/object/{config.SUPABASE_BUCKET}/{storage_path}"
    delays = (2, 5, 15, 30)
    for attempt, wait in enumerate((0,) + delays):
        if wait:
            time.sleep(wait)
        try:
            headers = _headers(upsert=True)
            headers["Content-Type"] = content_type
            with open(local_path, "rb") as f:
                res = requests.post(url, headers=headers, data=f, timeout=300)
            if res.status_code in (200, 201):
                return storage_path
            if res.status_code not in (429, 500, 502, 503, 504, 544):
                res.raise_for_status()
            log.warning(
                "upload %s -> %s (attempt %s/%s)", storage_path, res.status_code, attempt + 1, len(delays)
            )
        except requests.HTTPError:
            raise
        except Exception as e:
            log.warning("upload %s error: %s (attempt %s/%s)", storage_path, e, attempt + 1, len(delays))
    raise RuntimeError(f"upload failed after {len(delays)} retries: {storage_path}")


def download(storage_path: str) -> bytes:
    url = f"{config.SUPABASE_URL}/storage/v1/object/{config.SUPABASE_BUCKET}/{storage_path}"
    res = requests.get(url, headers=_headers(upsert=False), timeout=300)
    res.raise_for_status()
    return res.content


def signed_url(storage_path: str, expires: int = 300) -> str:
    """Short-lived signed URL so the browser can stream audio directly."""
    url = f"{config.SUPABASE_URL}/storage/v1/object/sign/{config.SUPABASE_BUCKET}/{storage_path}"
    res = requests.post(url, headers=_headers(upsert=False), json={"expiresIn": expires}, timeout=10)
    res.raise_for_status()
    return f"{config.SUPABASE_URL}/storage/v1{res.json()['signedURL']}"


def delete(storage_path: str):
    url = f"{config.SUPABASE_URL}/storage/v1/object/{config.SUPABASE_BUCKET}/{storage_path}"
    res = requests.delete(url, headers=_headers(upsert=False), timeout=60)
    if res.status_code not in (200, 204):
        log.warning("delete %s -> %s %s", storage_path, res.status_code, res.text[:200])
