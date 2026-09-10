"""
Telegram Interactive Command Listener with Watchlist & Live Stream Process Manager
"""
import os
import time
import requests
import threading
from datetime import datetime
from telegram_notifier import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, send_telegram_message
from channel_manager import load_monitored_channels, add_channel, remove_channel
from tiktok_profile_fetcher import fetch_tiktok_channel_profile
from watchlist_manager import (
    get_user_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    get_recent_digest_for_watchlist
)
from stock_price_notifier import fetch_price_digest_for_tickers

last_update_id = 0
global_system_status = None

def process_telegram_command(command_text: str, chat_id: str):
    text = command_text.strip()

    if text.startswith("/start") or text.startswith("/help"):
        help_msg = (
            f"🤖 <b>ĐIỀU KHIỂN TRỢ LÝ BROKER TIKTOK LIVE & DANH MỤC</b>\n\n"
            f"📌 <b>Quản Lý Danh Mục Mã Cổ Phiếu Quan Tâm:</b>\n"
            f"🔹 <code>/watch CEO, SSI, HPG</code> : Thêm các mã cổ phiếu quan tâm vào Watchlist\n"
            f"🔹 <code>/watchlist</code> : Xem danh sách mã cổ phiếu bạn đang theo dõi\n"
            f"🔹 <code>/unwatch CEO</code> : Xóa mã cổ phiếu khỏi danh sách\n"
            f"🔹 <code>/price</code> : Xem bảng giá thị trường realtime cho Watchlist\n"
            f"🔹 <code>/digest</code> : Tổng hợp báo cáo AI mới nhất cho các mã trong Watchlist\n\n"
            f"📌 <b>Các Lệnh Giám Sát Livestream:</b>\n"
            f"🔹 <code>/recording</code> : Xem tiến trình thu âm trực tiếp\n"
            f"🔹 <code>/report</code> : Ép trích xuất báo cáo tức thì\n"
            f"🔹 <code>/stop</code> : Dừng thu âm buổi Live hiện tại\n"
            f"🔹 <code>/list</code> : Xem danh sách kênh TikTok đang theo dõi\n"
            f"🔹 <code>/add @ten_kenh</code> : Thêm kênh TikTok mới\n"
            f"🔹 <code>/remove @ten_kenh</code> : Xóa kênh TikTok\n"
            f"🔹 <code>/status</code> : Kiểm tra tổng quan hệ thống\n"
        )
        send_telegram_message(help_msg, chat_id=chat_id)

    # --- WATCHLIST MANAGEMENT COMMANDS ---
    elif text.startswith("/watch") or text.startswith("/addstock"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_telegram_message("⚠️ Vui lòng nhập mã cổ phiếu! Ví dụ: <code>/watch CEO, SSI, HPG</code>")
            return

        success, added, current_all = add_to_watchlist(chat_id, parts[1])
        if success:
            added_str = ", ".join([f"<b>{t}</b>" for t in added])
            all_str = ", ".join([f"<code>{t}</code>" for t in current_all])
            msg = (
                f"✅ <b>ĐÃ THÊM MÃ CỔ PHIẾU VÀO WATCHLIST CỦA BẠN!</b>\n\n"
                f"➕ Đã thêm: {added_str}\n"
                f"📋 <b>Danh mục Watchlist hiện tại ({len(current_all)} mã):</b>\n"
                f"{all_str}\n\n"
                f"🛡️ <i>Dữ liệu đã được lưu an toàn xuống Supabase DB! Mỗi khi Broker nhắc tới các mã này, hệ thống sẽ tự động tổng hợp & báo về cho bạn!</i>"
            )
            send_telegram_message(msg)
        else:
            send_telegram_message("⚠️ Không tìm thấy mã cổ phiếu hợp lệ!")

    elif text.startswith("/watchlist") or text.startswith("/myportfolio"):
        watchlist = get_user_watchlist(chat_id)
        if not watchlist:
            send_telegram_message(
                f"📋 <b>DANH MỤC WATCHLIST CỦA BẠN ĐANG TRỐNG</b>\n\n"
                f"💡 Hãy thêm mã cổ phiếu quan tâm bằng lệnh: <code>/watch CEO, SSI, HPG</code>"
            )
            return

        w_str = "\n".join([f"• <b>{t}</b>" for t in watchlist])
        msg = (
            f"📋 <b>DANH MỤC {len(watchlist)} MÃ CỔ PHIẾU ĐANG THEO DÕI:</b>\n\n"
            f"{w_str}\n\n"
            f"💡 Thêm mã mới: <code>/watch <mã></code> | Xóa mã: <code>/unwatch <mã></code>\n"
            f"📊 Gõ <code>/digest</code> để xem tổng hợp phân tích AI mới nhất!"
        )
        send_telegram_message(msg)

    elif text.startswith("/unwatch") or text.startswith("/delstock"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_telegram_message("⚠️ Vui lòng nhập mã cổ phiếu muốn xóa! Ví dụ: <code>/unwatch CEO</code>")
            return

        success, removed, current_all = remove_from_watchlist(chat_id, parts[1])
        rem_str = ", ".join([f"<b>{t}</b>" for t in removed])
        all_str = ", ".join([f"<code>{t}</code>" for t in current_all]) if current_all else "<i>(Trống)</i>"

        msg = (
            f"🗑️ <b>ĐÃ XÓA MÃ CỔ PHIẾU KHỎI WATCHLIST!</b>\n\n"
            f"➖ Đã xóa: {rem_str}\n"
            f"📋 Danh mục còn lại: {all_str}"
        )
        send_telegram_message(msg, chat_id=chat_id)

    elif text.startswith("/price") or text.startswith("/gia") or text.startswith("/banggia"):
        watchlist = get_user_watchlist(chat_id)
        if not watchlist:
            send_telegram_message(
                f"📋 <b>DANH MỤC WATCHLIST CỦA BẠN ĐANG TRỐNG</b>\n\n"
                f"💡 Hãy thêm mã cổ phiếu quan tâm bằng lệnh: <code>/watch CEO, SSI, HPG</code>",
                chat_id=chat_id
            )
            return

        send_telegram_message("⏳ Đang tải dữ liệu giá chứng khoán realtime từ sàn...", chat_id=chat_id)
        price_msg = fetch_price_digest_for_tickers(watchlist)
        send_telegram_message(price_msg, chat_id=chat_id)

    elif text.startswith("/digest") or text.startswith("/summary") or text.startswith("/baocao"):
        send_telegram_message("⏳ Đang tổng hợp dữ liệu phân tích AI mới nhất từ Supabase DB cho danh mục của bạn...")
        reports = get_recent_digest_for_watchlist(chat_id, limit=6)

        if not reports:
            send_telegram_message(
                f"📊 <b>CHƯA CÓ BÁO CÁO MỚI CHO DANH MỤC CỦA BẠN</b>\n\n"
                f"Hệ thống chưa ghi nhận các buổi Live mới nhắc tới mã trong Watchlist của bạn.\n"
                f"Dùng <code>/watchlist</code> để xem danh sách mã đang theo dõi!"
            )
            return

        report_blocks = []
        for r in reports:
            tk = r.get("ticker", "")
            ch = r.get("channel", "Broker")
            sum_txt = r.get("summary", "")
            t_str = r.get("created_at", "")[:16].replace("T", " ")
            report_blocks.append(
                f"📌 <b>MÃ {tk}</b> ({ch} - <code>{t_str}</code>):\n"
                f"{sum_txt}\n"
            )

        full_msg = (
            f"📊 <b>TỔNG HỢP BÁO CÁO PHÂN TÍCH AI (DÀNH CHO WATCHLIST CỦA BẠN)</b>\n\n"
            + "\n--------------------\n".join(report_blocks) +
            f"\n\n🛡️ <i>Dữ liệu được trích xuất từ Groq AI GPT-OSS-120B & lưu trữ tại Supabase Database.</i>"
        )
        send_telegram_message(full_msg)

    # --- LIVESTREAM MONITORING COMMANDS ---
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
            f"🧠 Groq LLM Engine: <b>GPT-OSS-120B (Finance Analyzer)</b>\n"
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
