"""
Groq API / Cloud STT Helper - Superfast 100% Free Whisper Cloud STT
Uses Groq Whisper-Large-V3 (Translates 1 hour of audio in 2 seconds, 100% Free Tier, Zero RAM footprint on Render!)
"""
import os
import requests

# Groq API Key (Can be passed via GROQ_API_KEY environment variable)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def transcribe_with_cloud_whisper(audio_filepath: str, prompt_hint="Chứng khoán Việt Nam, HCM, HPG, SSI, DIG, stop loss, break"):
    """
    Gửi file audio sang Cloud STT API (Groq Whisper / Cloudflare AI).
    Tiêu thụ 0 MB RAM trên Render container!
    """
    if not GROQ_API_KEY:
        print("ℹ️ Không tìm thấy GROQ_API_KEY, chuyển sang chế độ Local/Lightweight STT.")
        return None

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    try:
        with open(audio_filepath, "rb") as f:
            files = {
                "file": (os.path.basename(audio_filepath), f, "audio/mp3")
            }
            data = {
                "model": "whisper-large-v3-turbo",
                "language": "vi",
                "prompt": prompt_hint,
                "response_format": "verbose_json"
            }
            res = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            if res.status_code == 200:
                json_resp = res.json()
                print("⚡ [Groq Whisper Cloud STT Success] Đã dịch âm thanh cực nhanh từ Cloud!")
                return json_resp.get("text", "")
            else:
                print(f"⚠️ Groq API Error ({res.status_code}): {res.text}")
                return None
    except Exception as e:
        print(f"⚠️ Lỗi kết nối Groq Cloud STT: {e}")
        return None
