"""
Telegram Interactive Command Listener with TikTok Profile Details
"""
import os
import time
import requests
import threading
from telegram_notifier import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, send_telegram_message
from channel_manager import load_monitored_channels, add_channel, remove_channel
from tiktok_profile_fetcher import fetch_tiktok_channel_profile

last_update_id = 0

def process_telegram_command(command_text: str, chat_id: str):
    text = command_text.strip()

    if text.startswith("/start") or text.startswith("/help"):
        help_msg = (
            f"🤖 <b>ĐIỀU KHIỂN TRỢ LÝ BROKER TIKTOK LIVE</b>\n\n"
            f"📌 <b>Các Lệnh Điều Khiển Có Thể Dùng:</b>\n\n"
            f"🔹 <code>/list</code> : Xem danh sách các kênh TikTok đang theo dõi\n"
            f"🔹 <code>/add @ten_kenh</code> : Thêm kênh Broker mới (Ví dụ: <code>/add @chng.khon.cng.win</code>)\n"
            f"🔹 <code>/remove @ten_kenh</code> : Xóa kênh khỏi danh sách theo dõi\n"
            f"🔹 <code>/status</code> : Kiểm tra trạng thái hệ thống Robot\n\n"
            f"<i>Gõ <code>/add @chng.khon.cng.win</code> để thử ngay!</i>"
        )
        send_telegram_message(help_msg)

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

        # 1. Fetch channel metadata (Display name & Live status)
        profile_info = fetch_tiktok_channel_profile(target)
        
        # 2. Add channel to DB
        success, clean_name, updated_list = add_channel(target)

        live_status_str = "🔴 <b>ĐANG LIVESTREAM NÓNG!</b>" if profile_info["is_live"] else "💤 Hiện chưa bật Live (Offline)"

        if success:
            card_msg = (
                f"✅ <b>ĐÃ THÊM KÊNH BROKER MỚI THÀNH CÔNG!</b>\n\n"
                f"👤 <b>Tên kênh:</b> {profile_info['display_name']}\n"
                f"🆔 <b>Username:</b> <code>{profile_info['username']}</code>\n"
                f"📊 <b>Trạng thái Live:</b> {live_status_str}\n"
                f"🔗 <b>Link TikTok:</b> <a href=\"{profile_info['profile_url']}\">Xem kênh</a>\n\n"
                f"📋 Tổng số kênh đang giám sát 24/7: <b>{len(updated_list)}</b> kênh."
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
        msg = (
            f"🟢 <b>TRẠNG THÁI HỆ THỐNG ROBOT BROKER</b>\n\n"
            f"⚙️ Web Server: <b>Online 24/7 (Render + UptimeRobot)</b>\n"
            f"⚡ Groq Cloud STT Engine: <b>Whisper-Large-V3 (Superfast 2s)</b>\n"
            f"☁️ Supabase Storage & DB: <b>Kết Nối OK</b>\n"
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
