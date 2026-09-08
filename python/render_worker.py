"""
Render.com Background Worker - TikTok Live Poller, Audio Recorder & Realtime Telegram AI Assistant
"""
import os
import sys
import time
import subprocess
from datetime import datetime
from tiktok_live_capture import get_tiktok_live_audio_stream_url
from telegram_notifier import send_telegram_message

# Environment configurations for Cloud deployment
TARGET_TIKTOK_CHANNEL = os.getenv("TIKTOK_CHANNEL", "@vtv24")
CHECK_INTERVAL_SEC = int(os.getenv("CHECK_INTERVAL", "180")) # Poll every 3 mins
RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "recordings")

def record_and_process_live_stream(stream_url: str, channel: str):
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_channel = channel.replace("@", "")
    filename = f"broker_{clean_channel}_{timestamp_str}.mp3"
    filepath = os.path.join(RECORDINGS_DIR, filename)

    print(f"\n🔴 [LIVE DETECTED!] Kênh {channel} vừa bật Live!")
    
    # 📲 Send Telegram Alert
    send_telegram_message(
        f"🔴 <b>PHÁT HIỆN LIVESREAM</b>\n\n"
        f"👤 Broker: <b>{channel}</b>\n"
        f"⏰ Bắt đầu lúc: <code>{datetime.now().strftime('%H:%M:%S %d/%m/%Y')}</code>\n"
        f"🎙️ Hệ thống đang tiến hành thu âm & phân tích mã chứng khoán..."
    )

    cmd = [
        "ffmpeg",
        "-i", stream_url,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", "128k",
        "-y",
        filepath
    ]

    try:
        proc = subprocess.Popen(cmd)
        print(f"🎙️ Đang ghi âm buổi Live... PID: {proc.pid}")
        proc.wait()
        
        print(f"✅ Kết thúc buổi Live. File ghi âm: {filepath}")

        # 📲 Send Telegram Completion Summary
        send_telegram_message(
            f"✅ <b>HOÀN THÀNH GHI ÂM LIVESTREAM</b>\n\n"
            f"👤 Broker: <b>{channel}</b>\n"
            f"📁 File lưu: <code>{filename}</code>\n"
            f"⏱️ Đã lưu xong toàn bộ âm thanh của buổi live."
        )

        return filepath
    except Exception as e:
        print(f"❌ Lỗi ghi âm: {e}")
        return None

def start_render_background_worker():
    print("=" * 60)
    print("🚀 RENDER BACKGROUND WORKER - TIKTOK LIVE AUDIO MONITOR")
    print(f"🎯 Kênh theo dõi: {TARGET_TIKTOK_CHANNEL}")
    print(f"⏱️ Tần số kiểm tra: {CHECK_INTERVAL_SEC}s / lần")
    print("=" * 60)

    send_telegram_message(
        f"🤖 <b>ROBOT BROKER ASSISTANT ĐÃ KHỞI ĐỘNG ON RENDER</b>\n\n"
        f"🎯 Đang giám sát kênh TikTok: <b>{TARGET_TIKTOK_CHANNEL}</b>\n"
        f"🟢 Trạng thái: Sẵn sàng phát hiện Live 24/7."
    )

    while True:
        try:
            print(f"\n[🔍 {datetime.now().strftime('%H:%M:%S')}] Kiểm tra Live {TARGET_TIKTOK_CHANNEL}...")
            stream_url = get_tiktok_live_audio_stream_url(TARGET_TIKTOK_CHANNEL)

            if stream_url:
                record_and_process_live_stream(stream_url, TARGET_TIKTOK_CHANNEL)
                time.sleep(60)
            else:
                print(f"💤 Chưa phát hiện Live. Chờ {CHECK_INTERVAL_SEC}s...")
                time.sleep(CHECK_INTERVAL_SEC)

        except KeyboardInterrupt:
            print("\n👋 Đã dừng Worker.")
            break
        except Exception as e:
            print(f"⚠️ Lỗi Worker: {e}. Thử lại sau 30s...")
            time.sleep(30)

if __name__ == "__main__":
    start_render_background_worker()
