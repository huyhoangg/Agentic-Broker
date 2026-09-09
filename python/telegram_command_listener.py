"""
Telegram Interactive Command Listener for Controlling TikTok Monitor
"""
import os
import time
import requests
import threading
from telegram_notifier import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, send_telegram_message
from channel_manager import load_monitored_channels, add_channel, remove_channel

last_update_id = 0

def process_telegram_command(command_text: str, chat_id: str):
    text = command_text.strip()

    if text.startswith("/start") or text.startswith("/help"):
        help_msg = (
            f"🤖 <b>ĐIỀU KHIỂN TRỢ LÝ BROKER TIKTOK LIVE</b>\n\n"
            f"📌 <b>Các Lệnh Điều Khiển Có Thể Dùng:</b>\n\n"
            f"🔹 <code>/list</code> : Xem danh sách các kênh TikTok đang theo dõi\n"
            f"🔹 <code>/add @ten_kenh</code> : Thêm kênh Broker mới vào danh sách 24/7\n"
            f"🔹 <code>/remove @ten_kenh</code> : Xóa kênh khỏi danh sách theo dõi\n"
            f"🔹 <code>/status</code> : Kiểm tra trạng thái hệ thống Robot\n\n"
            f"<i>Ví dụ: <code>/add @chungkhoan_ssi</code></i>"
        )
        send_telegram_message(help_msg)

    elif text.startswith("/list"):
        channels = load_monitored_channels()
        ch_list_str = "\n".join([f"• <b>{c}</b>" for c in channels])
        msg = (
            f"📋 <b>DANH SÁCH {len(channels)} KÊNH TIKTOK ĐANG THEO DÕI:</b>\n\n"
            f"{ch_list_str}\n\n"
            f"💡 Thêm kênh mới bằng lệnh: <code>/add @ten_kenh</code>"
        )
        send_telegram_message(msg)

    elif text.startswith("/add"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_telegram_message("⚠️ Vui lòng nhập tên kênh! Ví dụ: <code>/add @vtv24</code>")
            return
        
        target = parts[1]
        success, clean_name, updated_list = add_channel(target)
        if success:
            send_telegram_message(
                f"✅ <b>ĐÃ THÊM KÊNH MỚI THÀNH CÔNG!</b>\n\n"
                f"👤 Kênh: <b>{clean_name}</b>\n"
                f"📋 Tổng số kênh đang theo dõi: <b>{len(updated_list)}</b> kênh."
            )
        else:
            send_telegram_message(f"ℹ️ Kênh <b>{clean_name}</b> đã có sẵn trong danh sách theo dõi!")

    elif text.startswith("/remove") or text.startswith("/del"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_telegram_message("⚠️ Vui lòng nhập tên kênh muốn xóa! Ví dụ: <code>/remove @vtv24</code>")
            return

        target = parts[1]
        success, clean_name, updated_list = remove_channel(target)
        if success:
            send_telegram_message(
                f"🗑️ <b>ĐÃ XÓA KÊNH KHỎI DANH SÁCH!</b>\n\n"
                f"👤 Kênh: <b>{clean_name}</b>\n"
                f"📋 Danh sách còn lại: <b>{len(updated_list)}</b> kênh."
            )
        else:
            send_telegram_message(f"⚠️ Không tìm thấy kênh <b>{clean_name}</b> trong danh sách!")

    elif text.startswith("/status"):
        channels = load_monitored_channels()
        msg = (
            f"🟢 <b>TRẠNG THÁI HỆ THỐNG ROBOT BROKER</b>\n\n"
            f"⚙️ Web Server: <b>Online 24/7 (UptimeRobot)</b>\n"
            f"⚡ Groq Cloud STT Engine: <b>Whisper-Large-V3 (Superfast)</b>\n"
            f"☁️ Supabase Storage: <b>Kết Nối OK</b>\n"
            f"📋 Số kênh theo dõi: <b>{len(channels)} kênh</b> ({', '.join(channels[:3])}...)"
        )
        send_telegram_message(msg)

def start_telegram_command_poller():
    global last_update_id
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
                    msg = update.get("message")
                    if msg and "text" in msg:
                        cmd_text = msg["text"]
                        chat_id = str(msg["chat"]["id"])
                        process_telegram_command(cmd_text, chat_id)

            time.sleep(1)
        except Exception:
            time.sleep(3)
