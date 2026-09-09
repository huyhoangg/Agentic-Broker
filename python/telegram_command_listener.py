"""
Telegram Interactive Command Listener with Real-Time Live Stream Process Manager
"""
import os
import time
import requests
import threading
from datetime import datetime
from telegram_notifier import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, send_telegram_message
from channel_manager import load_monitored_channels, add_channel, remove_channel
from tiktok_profile_fetcher import fetch_tiktok_channel_profile

last_update_id = 0
global_system_status = None

def process_telegram_command(command_text: str, chat_id: str):
    text = command_text.strip()

    if text.startswith("/start") or text.startswith("/help"):
        help_msg = (
            f"🤖 <b>ĐIỀU KHIỂN TRỢ LÝ BROKER TIKTOK LIVE</b>\n\n"
            f"📌 <b>Các Lệnh Điều Khiển Có Thể Dùng:</b>\n\n"
            f"🔹 <code>/recording</code> : Xem TIẾN TRÌNH thu âm trực tiếp (Realtime Progress)\n"
            f"🔹 <code>/report</code> : Ép trích xuất BÁO CÁO bóc tách cổ phiếu tức thì\n"
            f"🔹 <code>/stop</code> : DỪNG THU ÂM buổi Live hiện tại\n"
            f"🔹 <code>/list</code> : Xem danh sách các kênh TikTok đang theo dõi\n"
            f"🔹 <code>/add @ten_kenh</code> : Thêm kênh Broker mới (Ví dụ: <code>/add @chng.khon.cng.win</code>)\n"
            f"🔹 <code>/remove @ten_kenh</code> : Xóa kênh khỏi danh sách theo dõi\n"
            f"🔹 <code>/status</code> : Kiểm tra tổng quan hệ thống Robot\n\n"
            f"<i>Bấm nút tương tác ngay bên dưới thông báo Live hoặc gõ lệnh bất kỳ lúc nào!</i>"
        )
        send_telegram_message(help_msg)

    elif text.startswith("/recording") or text.startswith("/progress"):
        if global_system_status and global_system_status.get("is_currently_recording"):
            ch = global_system_status.get("current_stream_channel", "@broker")
            start_dt = global_system_status.get("recording_start_time")
            fpath = global_system_status.get("current_filepath")
            uploaded_parts = global_system_status.get("uploaded_parts", 0)
            
            elapsed_sec = int((datetime.now() - start_dt).total_seconds()) if start_dt else 0
            mins = elapsed_sec // 60
            secs = elapsed_sec % 60
            
            size_mb = "N/A"
            if fpath and os.path.exists(fpath):
                size_mb = f"{round(os.path.getsize(fpath) / (1024 * 1024), 2)} MB"

            buttons = {
                "inline_keyboard": [
                    [
                        {"text": "📝 Báo Cáo Tức Thì", "callback_data": "/report"},
                        {"text": "🛑 Dừng Thu Âm", "callback_data": "/stop"}
                    ]
                ]
            }

            msg = (
                f"🔴 <b>TIẾN TRÌNH THU ÂM LIVESTREAM TRỰC TIẾP</b>\n\n"
                f"👤 Broker: <b>{ch}</b>\n"
                f"⏰ Bắt đầu lúc: <code>{start_dt.strftime('%H:%M:%S %d/%m/%Y') if start_dt else 'N/A'}</code>\n"
                f"⏱️ Đã thu được: <b>{mins} phút {secs} giây</b>\n"
                f"🛡️ Phân đoạn Supabase đã lưu: <b>{uploaded_parts} phần (5-min MP3)</b>\n"
                f"🟢 Trạng thái: <b>Đang ghi âm 100% liền mạch...</b>\n\n"
                f"<i>Dùng <code>/report</code> để bóc tách mã ngay, hoặc <code>/stop</code> để dừng!</i>"
            )
            send_telegram_message(msg, reply_markup=buttons)
        else:
            channels = load_monitored_channels()
            msg = (
                f"💤 <b>HIỆN TẠI KHÔNG CÓ BUỔI LIVE NÀO ĐANG DIỄN RA</b>\n\n"
                f"📋 Robot đang ngầm giám sát <b>{len(channels)} kênh Broker</b>:\n"
                f"<i>{', '.join(channels) if channels else 'Chưa có kênh nào'}</i>\n\n"
                f"🟢 Ngay khi có Broker bật Live, hệ thống sẽ tự động nhắn tin cho bạn!"
            )
            send_telegram_message(msg)

    elif text.startswith("/stop") or text.startswith("/cancel"):
        if global_system_status and global_system_status.get("is_currently_recording"):
            ch = global_system_status.get("current_stream_channel", "@broker")
            global_system_status["stop_requested"] = True
            msg = (
                f"🛑 <b>ĐÃ GỬI LỆNH DỪNG THU ÂM!</b>\n\n"
                f"👤 Broker: <b>{ch}</b>\n"
                f"⏳ Hệ thống đang dừng luồng Live, hoàn tất lưu file MP3 cuối cùng & tải lên Supabase..."
            )
            send_telegram_message(msg)
        else:
            send_telegram_message("💤 Hiện tại không có buổi Live nào đang diễn ra để dừng!")

    elif text.startswith("/report") or text.startswith("/transcribe"):
        if global_system_status and global_system_status.get("is_currently_recording"):
            ch = global_system_status.get("current_stream_channel", "@broker")
            global_system_status["report_requested"] = True
            msg = (
                f"⚡ <b>ĐÃ YÊU CẦU BÁO CÁO TỨC THÌ!</b>\n\n"
                f"👤 Broker: <b>{ch}</b>\n"
                f"🧠 Groq Cloud Whisper đang trích xuất nội dung audio & phát hiện mã cổ phiếu..."
            )
            send_telegram_message(msg)
        else:
            send_telegram_message("💤 Hiện tại không có buổi Live nào đang diễn ra để tạo báo cáo tức thì.")

    elif text.startswith("/list"):
        channels = load_monitored_channels()
        if not channels:
            send_telegram_message("📋 Danh sách theo dõi hiện đang trống. Dùng <code>/add @ten_kenh</code> để thêm!")
            return

        ch_list_str = "\n".join([f"• <b>{c}</b>" for c in channels])
        msg = (
            f"📋 <b>DANH SÁCH {len(channels)} KÊNH TIKTOK ĐANG THEO DÕI:</b>\n\n"
            f"{ch_list_str}\n\n"
            f"💡 Thêm kênh mới: <code>/add @ten_kenh</code>"
        )
        send_telegram_message(msg)

    elif text.startswith("/add"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_telegram_message("⚠️ Vui lòng nhập tên kênh! Ví dụ: <code>/add @chng.khon.cng.win</code>")
            return
        
        target = parts[1].strip()
        send_telegram_message(f"⏳ Đang đọc thông tin chi tiết kênh <b>{target}</b> từ TikTok...")

        profile_info = fetch_tiktok_channel_profile(target)
        success, clean_name, updated_list = add_channel(target)

        live_status_str = "🔴 <b>ĐANG LIVESTREAM NÓNG!</b> (Đang mở luồng thu âm...)" if profile_info["is_live"] else "💤 Hiện chưa bật Live (Offline)"

        if success:
            card_msg = (
                f"✅ <b>ĐÃ THÊM KÊNH BROKER MỚI THÀNH CÔNG!</b>\n\n"
                f"👤 <b>Tên kênh:</b> {profile_info['display_name']}\n"
                f"🆔 <b>Username:</b> <code>{profile_info['username']}</code>\n"
                f"📊 <b>Trạng thái Live:</b> {live_status_str}\n"
                f"🔗 <b>Link TikTok:</b> <a href=\"{profile_info['profile_url']}\">Xem kênh</a>\n\n"
                f"📋 Tổng số kênh đang giám sát 24/7: <b>{len(updated_list)}</b> kênh.\n"
                f"💡 Gõ <code>/recording</code> để xem tiến trình thu âm!"
            )
            send_telegram_message(card_msg)
        else:
            card_msg = (
                f"ℹ️ <b>KÊNH ĐÃ CÓ SẴN TRONG DANH SÁCH GIÁM SÁT:</b>\n\n"
                f"👤 <b>Tên kênh:</b> {profile_info['display_name']}\n"
                f"🆔 <b>Username:</b> <code>{profile_info['username']}</code>\n"
                f"📊 <b>Trạng thái Live:</b> {live_status_str}"
            )
            send_telegram_message(card_msg)

    elif text.startswith("/remove") or text.startswith("/del"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_telegram_message("⚠️ Vui lòng nhập tên kênh muốn xóa! Ví dụ: <code>/remove @chng.khon.cng.win</code>")
            return

        target = parts[1]
        success, clean_name, updated_list = remove_channel(target)
        if success:
            send_telegram_message(
                f"🗑️ <b>ĐÃ XÓA KÊNH KHỎI DANH SÁCH GIÁM SÁT!</b>\n\n"
                f"👤 Kênh: <b>{clean_name}</b>\n"
                f"📋 Danh sách còn lại: <b>{len(updated_list)}</b> kênh."
            )
        else:
            send_telegram_message(f"⚠️ Không tìm thấy kênh <b>{clean_name}</b> trong danh sách!")

    elif text.startswith("/status"):
        channels = load_monitored_channels()
        is_rec = global_system_status.get("is_currently_recording") if global_system_status else False
        rec_status = f"🔴 ĐANG THU ÂM KÊNH {global_system_status.get('current_stream_channel')}" if is_rec else "💤 Sẵn sàng giám sát 24/7"

        msg = (
            f"🟢 <b>TRẠNG THÁI HỆ THỐNG ROBOT BROKER</b>\n\n"
            f"⚙️ Web Server: <b>Online 24/7 (Render + UptimeRobot)</b>\n"
            f"🎙️ Tiến trình Live: <b>{rec_status}</b>\n"
            f"⚡ Groq Cloud STT Engine: <b>Whisper-Large-V3 (Superfast 2s)</b>\n"
            f"☁️ Supabase Storage & DB: <b>Kết Nối OK</b>\n"
            f"📋 Số kênh theo dõi: <b>{len(channels)} kênh</b>"
        )
        send_telegram_message(msg)

def start_telegram_command_poller(sys_status_ptr=None):
    global last_update_id, global_system_status
    if sys_status_ptr:
        global_system_status = sys_status_ptr

    if not TELEGRAM_BOT_TOKEN:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"

    while True:
        try:
            params = {"offset": last_update_id + 1, "timeout": 5}
            res = requests.get(url, params=params, timeout=10).json()

            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    last_update_id = update["update_id"]

                    # 1. Xử lý Callback Query từ Nút bấm tương tác
                    if "callback_query" in update:
                        cb = update["callback_query"]
                        cb_id = cb["id"]
                        cb_data = cb.get("data", "")
                        chat_id = str(cb["message"]["chat"]["id"])

                        # Trả lời Telegram API để tắt icon loading trên nút
                        try:
                            requests.post(
                                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
                                json={"callback_query_id": cb_id},
                                timeout=3
                            )
                        except Exception:
                            pass

                        if cb_data:
                            process_telegram_command(cb_data, chat_id)

                    # 2. Xử lý Tin nhắn văn bản (Lệnh /command)
                    elif "message" in update and "text" in update["message"]:
                        msg = update["message"]
                        cmd_text = msg["text"]
                        chat_id = str(msg["chat"]["id"])
                        process_telegram_command(cmd_text, chat_id)

            time.sleep(1)
        except Exception:
            time.sleep(3)
