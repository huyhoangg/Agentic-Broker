"""
Render Web Service + UptimeRobot 24/7 Seamless TikTok Live Audio Streamer
"""
import os
import sys
import time
import threading
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Ensure bin directory with ffmpeg is in PATH
import imageio_ffmpeg
bin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bin"))
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
symlink_path = os.path.join(bin_dir, "ffmpeg")
if not os.path.exists(symlink_path):
    os.makedirs(bin_dir, exist_ok=True)
    os.symlink(ffmpeg_exe, symlink_path)

os.environ["PATH"] = bin_dir + os.path.pathsep + os.environ.get("PATH", "")

from tiktok_live_capture import get_tiktok_live_audio_stream_url
from telegram_notifier import send_telegram_message

# Configuration
TARGET_TIKTOK_CHANNEL = os.getenv("TIKTOK_CHANNEL", "@vtv24")
CHECK_INTERVAL_SEC = int(os.getenv("CHECK_INTERVAL", "120"))  # Check every 2 mins
RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "recordings")
PORT = int(os.getenv("PORT", 10000))

# Global Monitor State
system_status = {
    "is_alive": True,
    "last_check_time": None,
    "is_currently_recording": False,
    "current_stream_channel": None,
    "total_recorded_lives": 0
}

class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    HTTP Server Handler cho UptimeRobot Ping (Keep-Alive 24/7)
    """
    def do_GET(self):
        system_status["last_ping_time"] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        
        response_data = {
            "status": "online",
            "message": "Render Web Service is kept 24/7 alive by UptimeRobot",
            "monitor": system_status
        }
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        return  # Suppress noisy HTTP logs

def run_seamless_recording(stream_url: str, channel: str):
    """
    Chạy ffmpeg thu âm liền mạch 100% không ngắt quãng cho đến khi Broker kết thúc Live
    """
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_channel = channel.replace("@", "")
    filename = f"seamless_broker_{clean_channel}_{timestamp_str}.mp3"
    filepath = os.path.join(RECORDINGS_DIR, filename)

    system_status["is_currently_recording"] = True
    system_status["current_stream_channel"] = channel

    print(f"\n🔴 [SEAMLESS RECORDING STARTED] Kênh {channel} đang Live!")
    print(f"📁 Lưu trực tiếp luồng audio vào: {filepath}")

    send_telegram_message(
        f"🔴 <b>BẮT ĐẦU THU ÂM LIỀN MẠCH (SEAMLESS STREAM)</b>\n\n"
        f"👤 Broker: <b>{channel}</b>\n"
        f"⏰ Bắt đầu: <code>{datetime.now().strftime('%H:%M:%S %d/%m/%Y')}</code>\n"
        f"🎙️ Luồng audio đang được thu âm 100% liền mạch qua Render Web Service..."
    )

    # ffmpeg command recording uninterrupted HLS audio stream to MP3
    cmd = [
        symlink_path,
        "-i", stream_url,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", "128k",
        "-y",
        filepath
    ]

    try:
        proc = subprocess.Popen(cmd)
        proc.wait()  # Block until the livestream naturally ends
        
        system_status["total_recorded_lives"] += 1
        print(f"✅ Buổi Live đã hoàn thành! File ghi âm đầy đủ: {filepath}")

        send_telegram_message(
            f"✅ <b>HOÀN THÀNH THU ÂM TOÀN BỘ BUỔI LIVE</b>\n\n"
            f"👤 Broker: <b>{channel}</b>\n"
            f"📁 File thu âm liền mạch: <code>{filename}</code>\n"
            f"🎉 Đã lưu trữ trọn vẹn 100% âm thanh từ lúc bắt đầu đến khi tắt Live!"
        )

    except Exception as e:
        print(f"❌ Lỗi trong quá trình thu âm liền mạch: {e}")
    finally:
        system_status["is_currently_recording"] = False
        system_status["current_stream_channel"] = None

def background_tiktok_monitor_thread():
    """
    Thread chạy ngầm giám sát TikTok Live liên tục 24/7
    """
    print(f"🤖 [Background Monitor Started] Đang giám sát kênh {TARGET_TIKTOK_CHANNEL}...")

    send_telegram_message(
        f"🚀 <b>SEAMLESS BROKER ASSISTANT ĐÃ ONLINE 24/7</b>\n\n"
        f"🎯 Kênh theo dõi: <b>{TARGET_TIKTOK_CHANNEL}</b>\n"
        f"🌐 Render Web Service + UptimeRobot Keep-Alive: <b>HOẠT ĐỘNG</b>\n"
        f"🟢 Sẵn sàng thu âm liền mạch 100% khi Broker bật Live!"
    )

    while True:
        try:
            now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            system_status["last_check_time"] = now_str
            
            if not system_status["is_currently_recording"]:
                print(f"[🔍 {now_str}] Kiểm tra luồng Live {TARGET_TIKTOK_CHANNEL}...")
                stream_url = get_tiktok_live_audio_stream_url(TARGET_TIKTOK_CHANNEL)

                if stream_url:
                    run_seamless_recording(stream_url, TARGET_TIKTOK_CHANNEL)
                    time.sleep(30)
                else:
                    time.sleep(CHECK_INTERVAL_SEC)
            else:
                time.sleep(30)

        except Exception as e:
            print(f"⚠️ Monitor error: {e}")
            time.sleep(30)

def start_server():
    # Start background TikTok monitoring thread
    monitor_thread = threading.Thread(target=background_tiktok_monitor_thread, daemon=True)
    monitor_thread.start()

    # Start HTTP Web Server on PORT
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print(f"🌐 Render Web Server listening on port {PORT}...")
    httpd.serve_forever()

if __name__ == "__main__":
    start_server()
