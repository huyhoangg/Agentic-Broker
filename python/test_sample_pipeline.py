"""
Test Script: Run full pipeline on YouTube sample audio (sample_youtube.mp3)
"""
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from groq_whisper import transcribe_with_cloud_whisper
from ticker_mapper import extract_vn_tickers
from supabase_client import upload_audio_to_supabase
from telegram_notifier import send_telegram_message

def test_pipeline():
    sample_filepath = os.path.join(os.path.dirname(__file__), "..", "sample_youtube.mp3")
    channel_name = "@youtube_sample_broker"
    
    if not os.path.exists(sample_filepath):
        print(f"❌ Không tìm thấy file âm thành mẫu tại: {sample_filepath}")
        return

    print("=" * 60)
    print(f"🎬 [TEST LUỒNG XỬ LÝ SẢN PHẨM] File âm thanh: {sample_filepath}")
    print("=" * 60)

    # 1. Gửi thông báo bắt đầu lên Telegram
    start_dt = datetime.now()
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
        f"🧪 <b>TEST LUỒNG: BẮT ĐẦU CHẠY SAMPLE YOUTUBE</b>\n\n"
        f"👤 Channel Test: <b>{channel_name}</b>\n"
        f"📁 File Sample: <code>sample_youtube.mp3</code> (3 phút audio)\n"
        f"⏰ Thời điểm test: <code>{start_dt.strftime('%H:%M:%S %d/%m/%Y')}</code>\n\n"
        f"👇 <b>Các nút bấm tương tác quản lý tiến trình:</b>",
        reply_markup=interactive_buttons
    )

    # 2. Upload MP3 sample lên Supabase Storage & lưu DB table live_recordings
    print("\n☁️ BƯỚC 1: Tải file audio lên Supabase Storage & lưu DB...")
    public_url = upload_audio_to_supabase(sample_filepath, channel_name)

    # 3. Transcribe qua Groq Cloud Whisper API (Siêu tốc 2s)
    print("\n🧠 BƯỚC 2: Gọi Groq Cloud Whisper API trích xuất văn bản...")
    transcript_text = transcribe_with_cloud_whisper(sample_filepath)

    if transcript_text:
        print("\n📝 NỘI DUNG VĂN BẢN TRÍCH XUẤT TỪ AUDIO:")
        print("-" * 50)
        print(transcript_text)
        print("-" * 50)

        # 4. Bóc tách mã cổ phiếu tiếng Việt
        print("\n🏷️ BƯỚC 3: Bóc tách các mã cổ phiếu Việt Nam...")
        detected_tickers = extract_vn_tickers(transcript_text)
        ticker_names = [t["ticker"] for t in detected_tickers] if detected_tickers else []
        ticker_str = ", ".join(ticker_names) if ticker_names else "Không phát hiện mã cụ thể trong 3 phút mẫu"

        print(f"✅ Mã phát hiện được: {ticker_str}")

        # 5. Gửi Báo Cáo Tổng Kết lên Telegram
        report_msg = (
            f"✅ <b>HOÀN THÀNH TEST LUỒNG SAMPLE YOUTUBE SUCCESSFUL!</b>\n\n"
            f"👤 Broker: <b>{channel_name}</b>\n"
            f"🏷️ <b>Mã phát hiện được:</b> <b>{ticker_str}</b>\n"
            f"🔗 <b>Audio Link Supabase:</b> {public_url if public_url else 'Đã lưu'}\n\n"
            f"🗣️ <b>Văn bản bóc tách Groq AI (Đoạn 300 ký tự đầu):</b>\n"
            f"<i>\"{transcript_text[:350]}...\"</i>"
        )
        send_telegram_message(report_msg)
    else:
        print("⚠️ Không thể trích xuất văn bản từ Groq API.")

if __name__ == "__main__":
    test_pipeline()
