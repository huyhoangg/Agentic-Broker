"""
Script tự động kết nối và lấy Chat ID từ Telegram Bot hoangmuadaybandinh_bot
"""
import time
import requests

TOKEN = "8643759548:AAF948HTbHKiD0YagFjSE2xpk8NkBqqKjlw"
BOT_USERNAME = "hoangmuadaybandinh_bot"

def wait_for_user_chat_id():
    print("=" * 65)
    print(f"🤖 ĐANG KẾT NỐI VỚI TELEGRAM BOT: @{BOT_USERNAME}")
    print("=" * 65)
    print(f"👉 Vui lòng mở ứng dụng Telegram trên điện thoại/máy tính:")
    print(f"👉 Mở link: https://t.me/{BOT_USERNAME}")
    print(f"👉 Bấm nút 'START' hoặc gửi 1 tin nhắn bất kỳ (ví dụ: 'xin chào') vào Bot.")
    print("-" * 65)
    print("⏳ Đang chờ tin nhắn từ bạn...")

    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    while True:
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("ok") and res.get("result"):
                # Take latest message
                for item in res["result"]:
                    message = item.get("message") or item.get("channel_post")
                    if message and "chat" in message:
                        chat_id = str(message["chat"]["id"])
                        first_name = message["chat"].get("first_name", "Bạn")
                        
                        print(f"\n🎉 THÀNH CÔNG! ĐÃ TÌM THẤY CHAT ID CỦA BẠN: {chat_id}")
                        
                        # Save to .env file
                        with open(".env", "w", encoding="utf-8") as f:
                            f.write(f"TELEGRAM_BOT_TOKEN={TOKEN}\n")
                            f.write(f"TELEGRAM_CHAT_ID={chat_id}\n")
                            f.write(f"TIKTOK_CHANNEL=@vtv24\n")
                            f.write(f"CHECK_INTERVAL=180\n")

                        print("💾 Đã lưu cấu hình vào file '.env'!")

                        # Send Test Message to user
                        send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                        msg_text = (
                            f"🎉 <b>KẾT NỐI THÀNH CÔNG!</b>\n\n"
                            f"Xin chào <b>{first_name}</b>!\n"
                            f"Bot <b>@{BOT_USERNAME}</b> đã được tích hợp hoàn toàn với Trợ Lý Broker Chứng Khoán VN.\n\n"
                            f"🔴 Mỗi khi Broker bạn theo dõi bật Live, Bot sẽ tự động thông báo và gửi phân tích mã cổ phiếu (HCM, SSI, HPG, DIG...) về đây cho bạn!"
                        )
                        requests.post(send_url, json={"chat_id": chat_id, "text": msg_text, "parse_mode": "HTML"})
                        print(f"📲 Đã gửi tin nhắn xác nhận tới Telegram của {first_name}!")
                        return chat_id

            time.sleep(2)
        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    wait_for_user_chat_id()
