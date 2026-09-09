"""
Database-backed Multi-Channel Manager for TikTok Live Broker Assistant (Supabase DB & Local Cache)
"""
import os
import json
import requests

CHANNELS_FILE = os.path.join(os.path.dirname(__file__), "..", "monitored_channels.json")

def get_supabase_credentials():
    url_base = os.getenv("SUPABASE_URL", "")
    key_base = os.getenv("SUPABASE_KEY", "")
    return url_base.strip(), key_base.strip()

def fetch_channels_from_supabase_db():
    url_base, key_base = get_supabase_credentials()
    if not url_base or not key_base:
        return None

    db_url = f"{url_base.rstrip('/')}/rest/v1/monitored_channels?select=channel_name"
    headers = {
        "Authorization": f"Bearer {key_base}",
        "apiKey": key_base
    }

    try:
        res = requests.get(db_url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                channels = [item["channel_name"] for item in data if "channel_name" in item]
                return channels
    except Exception as e:
        print(f"ℹ️ Note Supabase DB Channels Fetch: {e}")

    return None

def sync_channel_to_supabase_db(channel_name: str, action: str):
    """
    Action: 'add' hoặc 'remove' trên Supabase DB table 'monitored_channels'
    """
    url_base, key_base = get_supabase_credentials()
    if not url_base or not key_base:
        return

    headers = {
        "Authorization": f"Bearer {key_base}",
        "apiKey": key_base,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    if action == "add":
        db_url = f"{url_base.rstrip('/')}/rest/v1/monitored_channels"
        payload = {"channel_name": channel_name}
        try:
            requests.post(db_url, headers=headers, json=payload, timeout=5)
        except Exception:
            pass

    elif action == "remove":
        db_url = f"{url_base.rstrip('/')}/rest/v1/monitored_channels?channel_name=eq.{channel_name}"
        try:
            requests.delete(db_url, headers=headers, timeout=5)
        except Exception:
            pass

def load_monitored_channels():
    # 1. Thử lấy từ Supabase DB
    db_channels = fetch_channels_from_supabase_db()
    if db_channels is not None and len(db_channels) > 0:
        save_local_channels_cache(db_channels)
        return db_channels

    # 2. Local JSON Cache fallback
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass

    return []

def save_local_channels_cache(channels_list):
    try:
        with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
            json.dump(channels_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def add_channel(channel_name: str):
    clean = channel_name.strip()
    if not clean.startswith("@"):
        clean = "@" + clean

    channels = load_monitored_channels()
    if clean.lower() not in [c.lower() for c in channels]:
        channels.append(clean)
        save_local_channels_cache(channels)
        sync_channel_to_supabase_db(clean, "add")
        return True, clean, channels
    return False, clean, channels

def remove_channel(channel_name: str):
    clean = channel_name.strip()
    if not clean.startswith("@"):
        clean = "@" + clean
        
    channels = load_monitored_channels()
    new_list = [c for c in channels if c.lower() != clean.lower()]
    if len(new_list) < len(channels):
        save_local_channels_cache(new_list)
        sync_channel_to_supabase_db(clean, "remove")
        return True, clean, new_list
    return False, clean, channels
