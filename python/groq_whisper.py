"""
Groq API / Cloud STT Helper - Superfast 100% Free Whisper Cloud STT
Uses Groq Whisper-Large-V3 (Translates 1 hour of audio in 2 seconds, 100% Free Tier, Zero RAM footprint on Render!)
"""
import os
import re
import requests

# Auto-load .env file
env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

def clean_hallucinated_text(raw_text: str) -> str:
    """
    Làm sạch các đoạn ký tự rác lặp lại do Whisper sinh ra khi gặp nhạc nền hoặc nhiễu âm thanh
    """
    if not raw_text:
        return ""
    
    # Loại bỏ chuỗi ký tự đơn/đôi vô nghĩa nối tiếp nhau (e.g. "th n c nh mua ng h nay l")
    cleaned = re.sub(r'(?:\b[a-zA-Z]{1,2}\s+){3,}[a-zA-Z]{1,2}\b', '', raw_text)
    # Loại bỏ khoảng trắng thừa
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def transcribe_with_cloud_whisper(audio_filepath: str, prompt_hint="Chứng khoán Việt Nam, HCM, HPG, SSI, DIG, stop loss, break"):
    """
    Gửi file audio sang Cloud STT API (Groq Whisper / Cloudflare AI).
    Tiêu thụ 0 MB RAM trên Render container!
    """
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key:
        print("ℹ️ Không tìm thấy GROQ_API_KEY, chuyển sang chế độ Local/Lightweight STT.")
        return None

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {groq_key}"
    }

    for attempt in range(1, 4):
        try:
            with open(audio_filepath, "rb") as f:
                files = {
                    "file": (os.path.basename(audio_filepath), f, "audio/mp3")
                }
                data = {
                    "model": "whisper-large-v3-turbo",
                    "language": "vi",
                    "temperature": 0.0,
                    "prompt": prompt_hint,
                    "response_format": "verbose_json"
                }
                res = requests.post(url, headers=headers, files=files, data=data, timeout=90)
                if res.status_code == 200:
                    json_resp = res.json()
                    print("⚡ [Groq Whisper Cloud STT Success] Đã dịch âm thanh cực nhanh từ Cloud!")
                    raw_txt = json_resp.get("text", "")
                    return clean_hallucinated_text(raw_txt)
                else:
                    print(f"⚠️ Groq API Error ({res.status_code}): {res.text}")
                    if attempt < 3:
                        import time
                        time.sleep(2)
        except Exception as e:
            print(f"⚠️ Lỗi kết nối Groq Cloud STT (Lần {attempt}/3): {e}")
            if attempt < 3:
                import time
                time.sleep(2)

    return None
