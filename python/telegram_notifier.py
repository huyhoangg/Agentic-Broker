"""
Telegram Bot Notification Helper for TikTok Live Broker Assistant
"""
import os
import requests

# Try loading .env file if available
env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k] = v

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8643759548:AAF948HTbHKiD0YagFjSE2xpk8NkBqqKjlw")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6009632759")

def send_telegram_message(text: str):
    """
    Gửi tin nhắn thông báo tức thì qua Telegram Bot về điện thoại
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[Telegram Notice (Local)]: {text}")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"📲 [Telegram Success] Đã gửi tin nhắn tới Chat ID {TELEGRAM_CHAT_ID}")
            return True
        else:
            print(f"⚠️ Telegram API Error ({res.status_code}): {res.text}")
            return False
    except Exception as e:
        print(f"⚠️ Không thể gửi Telegram message: {e}")
        return False

if __name__ == "__main__":
    send_telegram_message("🔔 Test notification from Telegram Notifier Module!")
