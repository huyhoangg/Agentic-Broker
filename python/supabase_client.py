"""
Supabase Storage & Database Integration for TikTok Live Broker Assistant
"""
import os
import requests
from datetime import datetime

# Auto-load .env file
env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # Anon Key or Service Role Key
STORAGE_BUCKET = os.getenv("SUPABASE_BUCKET", "broker-audio-recordings")

def upload_audio_to_supabase(filepath: str, channel: str) -> str:
    """
    Tự động upload file ghi âm MP3 lên Supabase Storage Bucket & trả về Public URL
    """
    url_base = os.getenv("SUPABASE_URL", "")
    key_base = os.getenv("SUPABASE_KEY", "")
    bucket_base = os.getenv("SUPABASE_BUCKET", "broker-audio-recordings")

    if not url_base or not key_base:
        print("ℹ️ Bỏ qua Upload Supabase (Chưa điền SUPABASE_URL hoặc SUPABASE_KEY trong .env)")
        return None

    filename = os.path.basename(filepath)
    clean_channel = channel.replace("@", "")
    storage_path = f"{clean_channel}/{filename}"

    # Supabase Storage REST API Endpoint
    upload_url = f"{url_base.rstrip('/')}/storage/v1/object/{bucket_base}/{storage_path}"
    headers = {
        "Authorization": f"Bearer {key_base}",
        "apiKey": key_base,
        "Content-Type": "audio/mpeg",
        "x-upsert": "true"
    }

    print(f"☁️ Đang upload file MP3 '{filename}' lên Supabase Storage Bucket [{bucket_base}]...")

    try:
        with open(filepath, "rb") as f:
            file_data = f.read()

        res = requests.post(upload_url, headers=headers, data=file_data, timeout=120)

        if res.status_code in [200, 201]:
            public_url = f"{url_base.rstrip('/')}/storage/v1/object/public/{bucket_base}/{storage_path}"
            print(f"✅ Upload Supabase Storage thành công!")
            print(f"🔗 Public Audio Link: {public_url}")

            # Save metadata record to Supabase DB table
            save_metadata_to_supabase_db(channel, filename, public_url)

            return public_url
        else:
            print(f"⚠️ Note Supabase Storage API ({res.status_code}): {res.text}")
            return None

    except Exception as e:
        print(f"❌ Lỗi kết nối Supabase: {e}")
        return None

def save_metadata_to_supabase_db(channel: str, filename: str, public_url: str):
    url_base = os.getenv("SUPABASE_URL", "")
    key_base = os.getenv("SUPABASE_KEY", "")

    db_url = f"{url_base.rstrip('/')}/rest/v1/live_recordings"
    headers = {
        "Authorization": f"Bearer {key_base}",
        "apiKey": key_base,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    payload = {
        "channel": channel,
        "filename": filename,
        "audio_url": public_url,
        "created_at": datetime.now().isoformat()
    }

    try:
        res = requests.post(db_url, headers=headers, json=payload, timeout=10)
        if res.status_code in [200, 201]:
            print("💾 Đã lưu nhật ký vào Supabase DB table 'live_recordings'!")
        else:
            print(f"ℹ️ Note Supabase DB: {res.text}")
    except Exception as e:
        print(f"⚠️ Lỗi lưu Supabase DB: {e}")
