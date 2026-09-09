"""
TikTok Live Stream Audio Extractor & Real-time Stream Pipe
"""
import os
import sys
import subprocess
import time
import imageio_ffmpeg
import shutil

system_ffmpeg = shutil.which("ffmpeg")
if system_ffmpeg:
    ffmpeg_binary = system_ffmpeg
else:
    ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()

def get_tiktok_live_audio_stream_url(tiktok_username: str) -> str:
    """
    Trích xuất trực tiếp URL luồng HLS audio/video từ TikTok Livestream bằng yt-dlp
    """
    clean_username = tiktok_username.replace("@", "").strip()
    tiktok_url = f"https://www.tiktok.com/@{clean_username}/live"
    
    print(f"[+] Đang kết nối tới TikTok Live: {tiktok_url}")
    
    cmd = [
        "yt-dlp",
        "-g",
        "-f", "b[ext=mp4]/best",
        tiktok_url
    ]
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            stream_url = res.stdout.strip().split("\n")[0]
            print(f"✅ Đã lấy thành công luồng Stream HLS của @{clean_username}")
            return stream_url
        else:
            print(f"⚠️ Chưa phát hiện luồng Live (Kênh có thể đang tắt): {res.stderr[:100]}")
            return None
    except Exception as e:
        print(f"❌ Lỗi khi quét stream URL: {e}")
        return None

def capture_stream_audio_chunks(stream_url: str, output_dir="chunks", chunk_sec=10):
    os.makedirs(output_dir, exist_ok=True)
    out_pattern = os.path.join(output_dir, "frame_%03d.wav")

    print(f"🎙️ Đang bắt luồng Audio từ Live Stream -> Cắt thành các file {chunk_sec}s vào folder '{output_dir}'...")

    ffmpeg_cmd = [
        ffmpeg_binary,
        "-i", stream_url,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-f", "segment",
        "-segment_time", str(chunk_sec),
        "-reset_timestamps", "1",
        out_pattern
    ]

    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return process

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "@vtv24"
    url = get_tiktok_live_audio_stream_url(target)
    if url:
        print(f"Direct Stream URL: {url[:100]}...")
