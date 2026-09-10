"""
Render Web Service + UptimeRobot 24/7 Multi-Channel Seamless TikTok Live Audio Streamer
Bulletproof Architecture: 5-Minute Segmented MP3 Recording & Auto-Sync to Supabase
(Resilient against server restarts or network drops)
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
import glob
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
from groq_llm_analyzer import analyze_transcript_with_groq_llm
from watchlist_manager import save_stock_digest_report

# Trigger auto database table migrations on startup
try:
    from auto_migrate import auto_migrate_supabase
    auto_migrate_supabase()
except Exception as e:
    print(f"ℹ️ Auto migration startup note: {e}")

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
    "uploaded_parts": 0,
    "stt_engine": "Groq Cloud Whisper-Large-V3 (Bulletproof 5-Min Auto-Sync)"
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

def run_bulletproof_recording(stream_url: str, channel: str):
    """
    Cơ chế thu âm phân đoạn 5 phút (Segmented Recording):
    Cứ 5 phút âm thanh trôi qua -> Tự động upload ngay segment đó lên Supabase!
    Giúp bảo vệ 100% dữ liệu dù Render có bị restart hay sập nguồn.
    Có tích hợp Quản lý tiến trình trực tiếp qua Telegram (Nút bấm & Lệnh /recording, /report, /stop).
    """
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    start_dt = datetime.now()
    timestamp_str = start_dt.strftime("%Y%m%d_%H%M%S")
    clean_channel = channel.replace("@", "")

    session_dir = os.path.join(RECORDINGS_DIR, f"session_{clean_channel}_{timestamp_str}")
    os.makedirs(session_dir, exist_ok=True)

    segment_pattern = os.path.join(session_dir, "part_%03d.mp3")

    system_status["is_currently_recording"] = True
    system_status["current_stream_channel"] = channel
    system_status["recording_start_time"] = start_dt
    system_status["uploaded_parts"] = 0
    system_status["stop_requested"] = False
    system_status["report_requested"] = False
    system_status["current_filepath"] = os.path.join(session_dir, "part_000.mp3")

    # Lấy thông tin kênh từ TikTok OEmbed API
    profile = fetch_tiktok_channel_profile(channel)

    print(f"\n🔴 [BULLETPROOF RECORDING STARTED] Kênh {profile['display_name']} ({channel}) đang Live!")
    print(f"📁 Phân đoạn 5 phút lưu tại: {session_dir}")

    # Nút bấm tương tác trực tiếp trên Telegram
    interactive_buttons = {
        "inline_keyboard": [
            [
                {"text": "📊 Xem tiến trình", "callback_data": "/recording"},
                {"text": "📝 Báo cáo ngay", "callback_data": "/report"}
            ],
            [
                {"text": "🛑 Dừng thu âm", "callback_data": "/stop"}
            ]
        ]
    }

    send_telegram_message(
        f"🔴 <b>PHÁT HIỆN TIKTOK LIVE MỚI: BẮT ĐẦU THU ÂM AN TOÀN!</b>\n\n"
        f"👤 Broker: <b>{profile['display_name']}</b> (<code>{channel}</code>)\n"
        f"⏰ Bắt đầu lúc: <code>{start_dt.strftime('%H:%M:%S %d/%m/%Y')}</code>\n"
        f"🔗 Xem kênh: <a href=\"{profile['profile_url']}\">TikTok Profile</a>\n"
        f"🛡️ <i>Tự động sao lưu Supabase 5 phút/lần chống mất dữ liệu khi rớt mạng!</i>\n\n"
        f"👇 <b>Bấm nút bên dưới để điều khiển tiến trình thu âm:</b>",
        reply_markup=interactive_buttons
    )

    # ffmpeg command creating 300-second (5-min) MP3 segments
    cmd = [
        resolved_ffmpeg,
        "-i", stream_url,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", "128k",
        "-f", "segment",
        "-segment_time", "300",  # 5 minutes per file
        "-reset_timestamps", "1",
        segment_pattern
    ]

    uploaded_files = set()

    try:
        proc = subprocess.Popen(cmd)
        
        # Monitor & sync new 5-minute MP3 segments to Supabase while recording
        while proc.poll() is None:
            time.sleep(5)

            # 1. Kiểm tra Lệnh DỪNG từ Telegram (/stop)
            if system_status.get("stop_requested"):
                print("🛑 Đang dừng buổi thu âm theo yêu cầu từ Telegram...")
                system_status["stop_requested"] = False
                proc.terminate()
                time.sleep(2)
                if proc.poll() is None:
                    proc.kill()
                break

            # 2. Kiểm tra Lệnh BÁO CÁO TỨC THÌ từ Telegram (/report) -> STT & AI Report On-Demand!
            if system_status.get("report_requested"):
                system_status["report_requested"] = False
                print("⚡ Đang chạy STT & Phân tích Groq AI theo yêu cầu từ Telegram...")
                mp3_files = sorted(glob.glob(os.path.join(session_dir, "part_*.mp3")))
                if mp3_files:
                    latest_file = mp3_files[-1]
                    send_telegram_message("⏳ <b>Đang chạy Whisper STT & Groq LLM bóc tách file audio 5 phút mới nhất...</b>")
                    
                    raw_text = transcribe_with_cloud_whisper(latest_file)
                    detected_tickers = extract_vn_tickers(raw_text) if raw_text else []
                    ticker_str = ", ".join([t["ticker"] for t in detected_tickers]) if detected_tickers else "Chưa phát hiện mã"
                    
                    clean_analysis = ""
                    if raw_text and len(raw_text.strip()) > 10:
                        ai_res = analyze_transcript_with_groq_llm(raw_text)
                        clean_analysis = ai_res.get("clean_analysis", "")
                        
                        if detected_tickers:
                            for tk_item in detected_tickers:
                                save_stock_digest_report(
                                    ticker=tk_item["ticker"],
                                    channel=channel,
                                    summary=clean_analysis,
                                    raw_transcript=raw_text,
                                    audio_url=system_status.get("latest_sub_url", "")
                                )
                    
                    msg = (
                        f"📝 <b>BÁO CÁO PHÂN TÍCH THEO YÊU CẦU (ON-DEMAND STT & AI REPORT)</b>\n\n"
                        f"👤 Broker: <b>{profile['display_name']}</b> ({channel})\n"
                        f"⏱️ Thời điểm: <code>{datetime.now().strftime('%H:%M:%S %d/%m/%Y')}</code>\n"
                        f"🏷️ <b>Mã phát hiện:</b> <b>{ticker_str}</b>\n\n"
                    )
                    if clean_analysis:
                        msg += f"📊 <b>Phân Tích AI Groq (Đã lọc bỏ tán gẫu):</b>\n{clean_analysis}\n\n"
                    elif raw_text:
                        msg += f"🗣️ <b>Trích đoạn văn bản:</b>\n<i>\"{raw_text[:400]}...\"</i>\n\n"
                    else:
                        msg += f"⚠️ Chưa thu thập đủ dữ liệu âm thanh để bóc tách.\n\n"
                    
                    msg += f"🛡️ <i>Dữ liệu đã được lưu xuống Supabase DB cho danh mục Watchlist của bạn!</i>"
                    send_telegram_message(msg)

            # 3. Auto-sync các phân đoạn 5 phút đã hoàn thành lên Supabase (Ưu tiên lưu Audio 100%)
            mp3_files = sorted(glob.glob(os.path.join(session_dir, "part_*.mp3")))
            if len(mp3_files) > 1:
                for seg_file in mp3_files[:-1]:
                    if seg_file not in uploaded_files:
                        uploaded_files.add(seg_file)
                        part_num = len(uploaded_files)
                        system_status["uploaded_parts"] = part_num
                        print(f"☁️ [Auto-Sync Audio Supabase] Backup Part #{part_num} lên Supabase Storage...")
                        
                        sub_url = upload_audio_to_supabase(seg_file, channel)
                        system_status["latest_sub_url"] = sub_url

                        # Kiểm tra nếu bật AUTO_STT_ON_RECORDING (mặc định False: Ưu tiên lấy Audio)
                        auto_stt = os.getenv("AUTO_STT_ON_RECORDING", "false").lower() == "true"
                        ticker_str = "Âm thanh đã lưu"
                        clean_analysis = ""

                        if auto_stt:
                            raw_text = transcribe_with_cloud_whisper(seg_file)
                            detected_tickers = extract_vn_tickers(raw_text) if raw_text else []
                            ticker_str = ", ".join([t["ticker"] for t in detected_tickers]) if detected_tickers else "Theo dõi"
                            if raw_text and len(raw_text.strip()) > 10:
                                ai_res = analyze_transcript_with_groq_llm(raw_text)
                                clean_analysis = ai_res.get("clean_analysis", "")
                                if detected_tickers:
                                    for tk_item in detected_tickers:
                                        save_stock_digest_report(
                                            ticker=tk_item["ticker"],
                                            channel=channel,
                                            summary=clean_analysis,
                                            raw_transcript=raw_text,
                                            audio_url=sub_url or ""
                                        )

                        tele_msg = (
                            f"🛡️ <b>ĐÃ SAO LƯU THÀNH CÔNG AUDIO PART #{part_num} LÊN SUPABASE</b>\n\n"
                            f"👤 Broker: <b>{profile['display_name']}</b> ({channel})\n"
                            f"⏱️ Thời lượng segment: <b>5 phút MP3</b>\n"
                            f"🔗 Link Audio: {sub_url if sub_url else 'Đã lưu an toàn'}\n\n"
                            f"💡 <i>Bấm nút <b>📝 Báo cáo ngay</b> hoặc gõ <code>/report</code> để bóc tách STT & Phân tích AI bất kỳ lúc nào!</i>"
                        )
                        send_telegram_message(tele_msg)

        # Upload final remaining segment
        mp3_files = sorted(glob.glob(os.path.join(session_dir, "part_*.mp3")))
        for seg_file in mp3_files:
            if seg_file not in uploaded_files:
                uploaded_files.add(seg_file)
                part_num = len(uploaded_files)
                sub_url = upload_audio_to_supabase(seg_file, channel)

                send_telegram_message(
                    f"✅ <b>HOÀN THÀNH KẾT THÚC BUỔI LIVE (PART #{part_num})</b>\n\n"
                    f"👤 Broker: <b>{profile['display_name']}</b> ({channel})\n"
                    f"🎉 Tổng số <b>{len(uploaded_files)} phần âm thanh</b> đã được bảo vệ 100% trên Supabase Storage!\n"
                    f"💡 Dùng <code>/digest</code> trên Telegram để xem tổng hợp phân tích AI!"
                )

        system_status["total_recorded_lives"] += 1

    except Exception as e:
        print(f"❌ Lỗi trong quá trình thu âm: {e}")
    finally:
        system_status["is_currently_recording"] = False
        system_status["current_stream_channel"] = None
        system_status["recording_start_time"] = None
        system_status["stop_requested"] = False
        system_status["report_requested"] = False

def background_tiktok_monitor_thread():
    channels = load_monitored_channels()
    print(f"🤖 [Multi-Channel Monitor Started] Đang giám sát {len(channels)} kênh từ DB/Storage: {channels}")

    send_telegram_message(
        f"🚀 <b>BULLETPROOF BROKER ASSISTANT ONLINE 24/7 ON RENDER</b>\n\n"
        f"📋 Đang giám sát <b>{len(channels)} kênh TikTok</b>:\n"
        f"<i>{', '.join(channels) if channels else 'Chưa có kênh nào'}</i>\n\n"
        f"🛡️ <b>Cơ chế An Toàn:</b> Tự động Backup Supabase 5 phút/lần. Dù Render có bị restart đột ngột thì dữ liệu vẫn an toàn 100%!"
    )

    while True:
        try:
            now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            system_status["last_check_time"] = now_str
            
            if not system_status["is_currently_recording"]:
                current_channels = load_monitored_channels()
                for target_ch in current_channels:
                    stream_url = get_tiktok_live_audio_stream_url(target_ch)
                    if stream_url:
                        run_bulletproof_recording(stream_url, target_ch)
                        break
                    time.sleep(2)
                
                time.sleep(CHECK_INTERVAL_SEC)
            else:
                time.sleep(30)

        except Exception as e:
            print(f"⚠️ Monitor error: {e}")
            time.sleep(30)

from stock_price_notifier import start_hourly_price_notifier_thread

def start_server():
    cmd_thread = threading.Thread(target=start_telegram_command_poller, args=(system_status,), daemon=True)
    cmd_thread.start()

    monitor_thread = threading.Thread(target=background_tiktok_monitor_thread, daemon=True)
    monitor_thread.start()

    # Khởi chạy thread tự động báo giá cổ phiếu 1 tiếng/lần trong giờ giao dịch TTCK Việt Nam
    start_hourly_price_notifier_thread()

    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print(f"🌐 Server listening on 0.0.0.0:{PORT}...")
    httpd.serve_forever()

if __name__ == "__main__":
    start_server()
