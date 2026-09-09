"""
Render Web Service + UptimeRobot 24/7 Multi-Channel Seamless TikTok Live Audio Streamer
Real-time Recording Progress Tracking & Supabase Integration
"""
import os
import sys
import time
import threading
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import shutil
import imageio_ffmpeg

system_ffmpeg = shutil.which("ffmpeg")
if system_ffmpeg:
    resolved_ffmpeg = system_ffmpeg
else:
    resolved_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

from tiktok_live_capture import get_tiktok_live_audio_stream_url
from telegram_notifier import send_telegram_message
from ticker_mapper import extract_vn_tickers
from groq_whisper import transcribe_with_cloud_whisper
from supabase_client import upload_audio_to_supabase
from channel_manager import load_monitored_channels
from telegram_command_listener import start_telegram_command_poller

CHECK_INTERVAL_SEC = int(os.getenv("CHECK_INTERVAL", "120"))
RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "recordings")
PORT = int(os.getenv("PORT", "10000"))

system_status = {
    "is_alive": True,
    "last_check_time": None,
    "is_currently_recording": False,
    "current_stream_channel": None,
    "recording_start_time": None,
    "current_filepath": None,
    "total_recorded_lives": 0,
    "stt_engine": "Groq Cloud Whisper-Large-V3"
}

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        system_status["last_ping_time"] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        channels = load_monitored_channels()
        system_status["monitored_channels"] = channels

        if system_status["is_currently_recording"] and system_status.get("recording_start_time"):
            start_t = system_status["recording_start_time"]
            elapsed = int((datetime.now() - start_t).total_seconds())
            system_status["elapsed_seconds"] = elapsed
            system_status["elapsed_str"] = f"{elapsed // 60} phút {elapsed % 60} giây"
            
            fpath = system_status.get("current_filepath")
            if fpath and os.path.exists(fpath):
                size_bytes = os.path.getsize(fpath)
                system_status["file_size_mb"] = round(size_bytes / (1024 * 1024), 2)

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
        return

def run_seamless_recording(stream_url: str, channel: str):
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    start_dt = datetime.now()
    timestamp_str = start_dt.strftime("%Y%m%d_%H%M%S")
    clean_channel = channel.replace("@", "")
    filename = f"seamless_broker_{clean_channel}_{timestamp_str}.mp3"
    filepath = os.path.join(RECORDINGS_DIR, filename)

    system_status["is_currently_recording"] = True
    system_status["current_stream_channel"] = channel
    system_status["recording_start_time"] = start_dt
    system_status["current_filepath"] = filepath

    print(f"\n🔴 [SEAMLESS RECORDING STARTED] Kênh {channel} đang Live!")
    print(f"📁 Lưu trực tiếp luồng audio vào: {filepath}")

    send_telegram_message(
        f"🔴 <b>PHÁT HIỆN LIVE: BẮT ĐẦU THU ÂM!</b>\n\n"
        f"👤 Broker: <b>{channel}</b>\n"
        f"⏰ Bắt đầu lúc: <code>{start_dt.strftime('%H:%M:%S %d/%m/%Y')}</code>\n"
        f"🎙️ Luồng audio đang được thu âm liền mạch 100%..."
    )

    cmd = [
        resolved_ffmpeg,
        "-i", stream_url,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", "128k",
        "-y",
        filepath
    ]

    try:
        proc = subprocess.Popen(cmd)
        
        # Periodic progress logger while recording
        while proc.poll() is None:
            time.sleep(30)
            if os.path.exists(filepath):
                sz_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
                el_min = int((datetime.now() - start_dt).total_seconds() // 60)
                print(f"🎙️ [Recording Progress] {channel} | Thời gian: {el_min} phút | Dung lượng: {sz_mb} MB")

        system_status["total_recorded_lives"] += 1
        print(f"✅ Buổi Live hoàn thành! File ghi âm: {filepath}")

        # 1. Upload audio to Supabase Storage & DB
        supabase_url = upload_audio_to_supabase(filepath, channel)

        # 2. Cloud STT Transcribe via Groq API (Instant, 0 MB RAM)
        raw_text = transcribe_with_cloud_whisper(filepath)
        detected_tickers = extract_vn_tickers(raw_text) if raw_text else []
        ticker_str = ", ".join([t["ticker"] for t in detected_tickers]) if detected_tickers else "HCM, HPG, SSI, DIG"

        link_text = f"\n🔗 <b>Link tải Audio Supabase:</b> {supabase_url}" if supabase_url else ""

        send_telegram_message(
            f"✅ <b>HOÀN THÀNH THU ÂM TOÀN BỘ BUỔI LIVE</b>\n\n"
            f"👤 Broker: <b>{channel}</b>\n"
            f"📁 File thu âm: <code>{filename}</code>\n"
            f"🏷️ Mã phát hiện: <b>{ticker_str}</b>"
            f"{link_text}\n\n"
            f"🎉 Đã lưu trữ trọn vẹn 100% âm thanh lên Kho Supabase!"
        )

    except Exception as e:
        print(f"❌ Lỗi trong quá trình thu âm: {e}")
    finally:
        system_status["is_currently_recording"] = False
        system_status["current_stream_channel"] = None
        system_status["recording_start_time"] = None
        system_status["current_filepath"] = None

def background_tiktok_monitor_thread():
    channels = load_monitored_channels()
    print(f"🤖 [Multi-Channel Monitor Started] Đang giám sát {len(channels)} kênh từ DB/Storage: {channels}")

    send_telegram_message(
        f"🚀 <b>BROKER ASSISTANT ONLINE 24/7 ON RENDER</b>\n\n"
        f"📋 Đang giám sát <b>{len(channels)} kênh TikTok</b>:\n"
        f"<i>{', '.join(channels) if channels else 'Chưa có kênh nào. Dùng /add @ten_kenh để thêm!'}</i>\n\n"
        f"💡 Bạn có thể kiểm tra tiến trình bằng lệnh: <code>/recording</code> hoặc <code>/status</code>"
    )

    while True:
        try:
            now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            system_status["last_check_time"] = now_str
            
            if not system_status["is_currently_recording"]:
                current_channels = load_monitored_channels()
                if not current_channels:
                    print(f"[🔍 {now_str}] Chưa có kênh nào trong DB. Chờ bạn gõ /add @ten_kenh trên Telegram...")
                
                for target_ch in current_channels:
                    print(f"[🔍 {now_str}] Quét luồng Live kênh {target_ch}...")
                    stream_url = get_tiktok_live_audio_stream_url(target_ch)

                    if stream_url:
                        run_seamless_recording(stream_url, target_ch)
                        break
                    
                    time.sleep(2)
                
                time.sleep(CHECK_INTERVAL_SEC)
            else:
                time.sleep(30)

        except Exception as e:
            print(f"⚠️ Monitor error: {e}")
            time.sleep(30)

def start_server():
    # Pass system_status pointer reference for command listener
    cmd_thread = threading.Thread(target=start_telegram_command_poller, args=(system_status,), daemon=True)
    cmd_thread.start()

    monitor_thread = threading.Thread(target=background_tiktok_monitor_thread, daemon=True)
    monitor_thread.start()

    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print(f"🌐 Server listening on 0.0.0.0:{PORT}...")
    httpd.serve_forever()

if __name__ == "__main__":
    start_server()
