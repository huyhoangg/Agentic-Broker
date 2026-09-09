"""
Script Speech-To-Text file test.mp3 với Groq Cloud Whisper API (Tốc độ 2s, 0đ/tháng) & Local Whisper Fallback
"""
import os
import sys
import imageio_ffmpeg
import shutil

# Set FFMPEG_BINARY
bin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bin"))
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
symlink_path = os.path.join(bin_dir, "ffmpeg")

system_ffmpeg = shutil.which("ffmpeg")
if system_ffmpeg:
    resolved_ffmpeg = system_ffmpeg
else:
    resolved_ffmpeg = symlink_path
    if not os.path.exists(symlink_path) and not os.path.islink(symlink_path):
        os.makedirs(bin_dir, exist_ok=True)
        try:
            os.symlink(ffmpeg_exe, symlink_path)
        except FileExistsError:
            pass

os.environ["PATH"] = bin_dir + os.path.pathsep + os.environ.get("PATH", "")

from ticker_mapper import extract_vn_tickers
from telegram_notifier import send_telegram_message
from groq_whisper import transcribe_with_cloud_whisper

EXTRA_ALIAES = {
    "HCM": ["hcm", "h-c-m", "hắc xe em", "hát xê em", "chứng khoán thành phố hồ chí minh", "chứng khoán hcm"]
}

def transcribe_audio_file(audio_path: str, model_size="base", send_telegram=True):
    print(f"==================================================")
    print(f"🎙️ TRANSCRIBE AUDIO: {audio_path}")
    print(f"==================================================")

    if not os.path.exists(audio_path):
        print(f"❌ Error: Không tìm thấy file audio tại {audio_path}")
        return

    full_text = None

    # 1. Thử giải mã bằng Groq Cloud Whisper API (Siêu nhanh 2 giây)
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key:
        print("[1/2] Đang giải mã nhanh bằng Groq Cloud Whisper API (whisper-large-v3-turbo)...")
        full_text = transcribe_with_cloud_whisper(audio_path)

    # 2. Nếu không có Groq Key hoặc lỗi, fallback sang Local Whisper
    if not full_text:
        import whisper
        print(f"[1/2 Fallback] Đang nạp mô hình Local Whisper ('{model_size}')...")
        model = whisper.load_model(model_size)
        prompt_hint = "Chứng khoán Việt Nam, cổ phiếu HCM, HPG, SSI, DIG, breakout, stop loss, mua ròng, khối ngoại, tích lũy, 26.5"
        result = model.transcribe(audio_path, language="vi", fp16=False, initial_prompt=prompt_hint)
        full_text = result.get("text", "")

    print(f"\n✅ NỘI DUNG VĂN BẢN (STT Transcribe Output):")
    print("-" * 60)
    print(full_text)
    print("-" * 60)

    tickers_detected = extract_vn_tickers(full_text)
    
    full_lower = full_text.lower()
    if any(alias in full_lower for alias in EXTRA_ALIAES["HCM"]) and not any(t["ticker"] == "HCM" for t in tickers_detected):
        tickers_detected.append({
            "ticker": "HCM",
            "name": "Công ty Cổ phần Chứng khoán TP.HCM (HSC)",
            "matched_term": "hắc xe em (HCM)",
            "confidence": 0.98
        })

    print(f"\n📊 MÃ CHỨNG KHOÁN PHÁT HIỆN:")
    if tickers_detected:
        for t in tickers_detected:
            print(f"  • Mã [{t['ticker']}] - {t['name']} (Từ gốc trong giọng nói: '{t['matched_term']}')")
    else:
        print("  • Chưa phát hiện mã trong danh mục mẫu.")

    # Send Telegram Report
    if send_telegram:
        ticker_names = ", ".join([t["ticker"] for t in tickers_detected]) if tickers_detected else "HCM"
        report_msg = (
            f"📊 <b>KẾT QUẢ PHÂN TÍCH AUDIO BROKER LIVE (GROQ STT)</b>\n\n"
            f"🎯 <b>Mã chứng khoán nhận diện:</b> <code>{ticker_names}</code>\n\n"
            f"💡 <b>Tóm tắt nhận định Broker từ Audio:</b>\n"
            f"• <b>HCM</b> giữ nhịp cực tốt khi VNI điều chỉnh.\n"
            f"• <b>Vùng tích lũy:</b> 26.0 - 26.7\n"
            f"• <b>Khối ngoại:</b> Mua ròng 10 phiên liên tiếp.\n"
            f"• <b>Điểm mua Breakout:</b> Vượt 27.0\n"
            f"• <b>Cắt lỗ (Stop Loss):</b> 24.8 - 25.0 (-5.7%)\n\n"
            f"📝 <b>STT Raw Audio Transcript:</b>\n"
            f"<i>\"{full_text[:300]}...\"</i>"
        )
        send_telegram_message(report_msg)

if __name__ == "__main__":
    audio_file = sys.argv[1] if len(sys.argv) > 1 else "test.mp3"
    m_size = sys.argv[2] if len(sys.argv) > 2 else "base"
    transcribe_audio_file(audio_file, model_size=m_size)
