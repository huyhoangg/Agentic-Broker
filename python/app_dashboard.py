"""
Visual Experiment Dashboard Web App for Speech-to-Text, Keyword Inspection & Groq LLM Intelligence Analysis
Zero External Dependencies (Runs on built-in Python http.server)
"""
import os
import sys
import json
import time
import glob
import subprocess
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from groq_whisper import transcribe_with_cloud_whisper
from ticker_mapper import extract_vn_tickers
from groq_llm_analyzer import analyze_transcript_with_groq_llm

PORT = 8080
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_ffmpeg_binary():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

FFMPEG_BIN = get_ffmpeg_binary()

class DashboardRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD_PAGE.encode("utf-8"))

        elif path == "/api/audio_files":
            files = []
            for ext in ["*.mp3", "*.webm", "*.wav", "*.m4a"]:
                for fpath in glob.glob(os.path.join(ROOT_DIR, ext)):
                    fname = os.path.basename(fpath)
                    fsize = round(os.path.getsize(fpath) / (1024 * 1024), 2)
                    files.append({"filename": fname, "size_mb": fsize, "path": fpath})
            
            files.sort(key=lambda x: x["filename"])
            self.send_json_response({"status": "success", "files": files})

        elif path == "/api/audio_stream":
            fname = query.get("file", [""])[0]
            fpath = os.path.join(ROOT_DIR, os.path.basename(fname))
            if os.path.exists(fpath):
                self.send_response(200)
                content_type = "audio/mpeg" if fname.endswith(".mp3") else "audio/webm"
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(os.path.getsize(fpath)))
                self.end_headers()
                with open(fpath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File not found")

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/upload":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            filename = f"uploaded_{int(time.time())}.mp3"
            save_path = os.path.join(ROOT_DIR, filename)

            with open(save_path, "wb") as f:
                f.write(body)

            self.send_json_response({"status": "success", "filename": filename, "size_mb": round(len(body)/(1024*1024), 2)})

        elif path == "/api/process_segment":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
                fname = data.get("filename", "")
                start_sec = int(data.get("start_sec", 0))
                duration_sec = int(data.get("duration_sec", 300))
                segment_idx = int(data.get("segment_idx", 0))

                source_fpath = os.path.join(ROOT_DIR, os.path.basename(fname))
                if not os.path.exists(source_fpath):
                    self.send_json_response({"status": "error", "message": f"File {fname} không tồn tại"}, status=404)
                    return

                temp_seg_dir = os.path.join(ROOT_DIR, "temp_segments")
                os.makedirs(temp_seg_dir, exist_ok=True)
                seg_fpath = os.path.join(temp_seg_dir, f"seg_{int(time.time())}_{segment_idx}.mp3")

                start_str = str(start_sec)
                dur_str = str(duration_sec)
                cmd = [
                    FFMPEG_BIN, "-y",
                    "-ss", start_str,
                    "-i", source_fpath,
                    "-t", dur_str,
                    "-vn", "-acodec", "libmp3lame", "-ab", "128k",
                    seg_fpath
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # 1. STT via Groq Whisper Cloud
                t0 = time.time()
                transcript = transcribe_with_cloud_whisper(seg_fpath)
                stt_proc_time = round(time.time() - t0, 2)

                if os.path.exists(seg_fpath):
                    try:
                        os.remove(seg_fpath)
                    except Exception:
                        pass

                if transcript is None:
                    transcript = ""

                # 2. Extract Stock Tickers
                keywords_data = extract_vn_tickers(transcript)

                # 3. Groq LLM Intelligence Analysis (GPT-OSS-120B)
                t1 = time.time()
                llm_res = analyze_transcript_with_groq_llm(transcript)
                llm_proc_time = round(time.time() - t1, 2)

                def format_time(sec):
                    m = sec // 60
                    s = sec % 60
                    return f"{m:02d}:{s:02d}"

                end_sec = start_sec + duration_sec
                time_range_str = f"{format_time(start_sec)} - {format_time(end_sec)}"

                self.send_json_response({
                    "status": "success",
                    "segment_idx": segment_idx,
                    "start_sec": start_sec,
                    "end_sec": end_sec,
                    "time_str": time_range_str,
                    "transcript": transcript,
                    "tickers": keywords_data,
                    "llm_analysis": llm_res.get("clean_analysis", ""),
                    "proc_time_sec": stt_proc_time,
                    "llm_time_sec": llm_proc_time
                })

            except Exception as e:
                self.send_json_response({"status": "error", "message": str(e)}, status=500)

        elif path == "/api/audio_info":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            fname = data.get("filename", "")
            fpath = os.path.join(ROOT_DIR, os.path.basename(fname))
            
            if os.path.exists(fpath):
                cmd = [FFMPEG_BIN, "-i", fpath]
                p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                _, err = p.communicate()
                err_str = err.decode('utf-8', errors='ignore')

                duration_sec = 180
                for line in err_str.split("\n"):
                    if "Duration:" in line:
                        try:
                            t_str = line.split("Duration:")[1].split(",")[0].strip()
                            h, m, s = t_str.split(":")
                            duration_sec = int(h)*3600 + int(m)*60 + float(s)
                            break
                        except Exception:
                            pass

                self.send_json_response({"status": "success", "duration_sec": int(duration_sec)})
            else:
                self.send_json_response({"status": "error", "message": "File not found"}, status=404)

        else:
            self.send_error(404, "Not Found")

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        return

HTML_DASHBOARD_PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpeechAI Inspector - Phân Tích Giọng Nói & Trích Xuất AI Chuyên Sâu</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0b0f19;
            --panel-bg: rgba(22, 30, 46, 0.7);
            --panel-border: rgba(255, 255, 255, 0.08);
            --accent-green: #10b981;
            --accent-cyan: #06b6d4;
            --accent-gold: #f59e0b;
            --accent-purple: #8b5cf6;
            --accent-red: #ef4444;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        body {
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(at 0% 0%, rgba(16, 185, 129, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(6, 182, 212, 0.12) 0px, transparent 50%),
                radial-gradient(at 50% 100%, rgba(139, 92, 246, 0.08) 0px, transparent 50%);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem 1.5rem;
        }

        .container {
            max-width: 1240px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--panel-border);
        }

        .logo-title h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 1.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #10b981, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }

        .logo-title p {
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-top: 0.2rem;
        }

        .badge-live {
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.4);
            padding: 0.4rem 0.9rem;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .badge-live span {
            width: 8px;
            height: 8px;
            background-color: var(--accent-green);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        .grid-layout {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 1.5rem;
        }

        @media (max-width: 960px) {
            .grid-layout { grid-template-columns: 1fr; }
        }

        .card {
            background: var(--panel-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--panel-border);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .card-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 1.2rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .form-group {
            margin-bottom: 1.2rem;
        }

        label {
            display: block;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }

        select, input[type="file"] {
            width: 100%;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--panel-border);
            border-radius: 0.6rem;
            padding: 0.75rem 1rem;
            color: #fff;
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }

        select:focus {
            border-color: var(--accent-cyan);
        }

        /* Segment selection list */
        .segment-selector-grid {
            max-height: 180px;
            overflow-y: auto;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--panel-border);
            border-radius: 0.6rem;
            padding: 0.6rem;
            margin-bottom: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }

        .segment-checkbox-item {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            font-size: 0.83rem;
            color: var(--text-main);
            cursor: pointer;
            padding: 0.3rem 0.5rem;
            border-radius: 0.4rem;
            transition: background 0.15s;
        }

        .segment-checkbox-item:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .button-group {
            display: flex;
            gap: 0.8rem;
        }

        .btn-primary {
            flex: 1;
            background: linear-gradient(135deg, #10b981, #059669);
            color: #ffffff;
            border: none;
            border-radius: 0.6rem;
            padding: 0.9rem 1rem;
            font-size: 0.92rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.4rem;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
        }

        .btn-stop {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: #ffffff;
            border: none;
            border-radius: 0.6rem;
            padding: 0.9rem 1.2rem;
            font-size: 0.92rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.4rem;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
        }

        .btn-stop:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
        }

        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }

        .stat-card {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--panel-border);
            border-radius: 0.8rem;
            padding: 1rem;
            text-align: center;
        }

        .stat-value {
            font-family: 'Outfit', sans-serif;
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--accent-cyan);
            margin-top: 0.2rem;
        }

        .stat-label {
            font-size: 0.78rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        /* Audio Player Bar */
        .audio-player-wrapper {
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid var(--panel-border);
            border-radius: 0.8rem;
            padding: 1rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        audio {
            width: 100%;
            height: 40px;
            border-radius: 0.5rem;
        }

        /* Progress Bar */
        .progress-wrapper {
            margin-bottom: 1.5rem;
        }

        .progress-bar-bg {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 9999px;
            height: 10px;
            overflow: hidden;
            margin-top: 0.5rem;
        }

        .progress-bar-fill {
            background: linear-gradient(90deg, #10b981, #06b6d4);
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
        }

        /* Segment Feed */
        .segment-feed {
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
        }

        .segment-card {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid var(--panel-border);
            border-radius: 0.8rem;
            padding: 1.2rem;
            transition: border-color 0.2s;
        }

        .segment-card:hover {
            border-color: rgba(6, 182, 212, 0.4);
        }

        .segment-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.8rem;
            padding-bottom: 0.6rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .segment-time {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            color: var(--accent-cyan);
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            cursor: pointer;
        }

        .segment-time:hover {
            text-decoration: underline;
        }

        .segment-speed {
            font-size: 0.78rem;
            color: var(--text-muted);
            background: rgba(255, 255, 255, 0.05);
            padding: 0.2rem 0.6rem;
            border-radius: 0.4rem;
        }

        .ticker-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 0.8rem;
        }

        .ticker-badge {
            background: rgba(245, 158, 11, 0.15);
            color: var(--accent-gold);
            border: 1px solid rgba(245, 158, 11, 0.4);
            padding: 0.3rem 0.7rem;
            border-radius: 0.5rem;
            font-size: 0.82rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            cursor: pointer;
            transition: all 0.15s;
        }

        .ticker-badge:hover {
            background: rgba(245, 158, 11, 0.3);
            transform: scale(1.05);
        }

        .llm-analysis-box {
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.25);
            border-radius: 0.6rem;
            padding: 1rem;
            margin-bottom: 0.8rem;
            font-size: 0.9rem;
            line-height: 1.6;
            color: #ecfdf5;
        }

        .llm-analysis-header {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            color: var(--accent-green);
            font-size: 0.88rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .transcript-collapsible {
            margin-top: 0.5rem;
        }

        .transcript-toggle-btn {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
            border: none;
            padding: 0.3rem 0.6rem;
            border-radius: 0.4rem;
            font-size: 0.78rem;
            cursor: pointer;
            margin-bottom: 0.5rem;
        }

        .transcript-text {
            font-size: 0.88rem;
            line-height: 1.6;
            color: #9ca3af;
            background: rgba(0, 0, 0, 0.3);
            padding: 0.8rem 1rem;
            border-radius: 0.6rem;
            border-left: 3px solid rgba(255, 255, 255, 0.1);
        }

        .empty-state {
            text-align: center;
            padding: 3rem 1rem;
            color: var(--text-muted);
        }

        .empty-state svg {
            width: 48px;
            height: 48px;
            margin-bottom: 1rem;
            stroke: var(--text-muted);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-title">
                <h1>⚡ SpeechAI Inspector</h1>
                <p>Phần Thử Nghiệm Xử Lý Giọng Nói & Phân Tích AI Chuyên Sâu (Groq GPT-OSS-120B)</p>
            </div>
            <div class="badge-live">
                <span></span> Groq Cloud LLM (Free Tier)
            </div>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">TỔNG THỜI LƯỢNG AUDIO</div>
                <div class="stat-value" id="stat-duration">00:00</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">PHÂN ĐOẠN ĐÃ XỬ LÝ</div>
                <div class="stat-value" id="stat-segments">0 / 0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">MÃ CỔ PHIẾU PHÁT HIỆN</div>
                <div class="stat-value" style="color: var(--accent-gold)" id="stat-tickers-count">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">TỐC ĐỘ XỬ LÝ AI</div>
                <div class="stat-value" style="color: var(--accent-green)" id="stat-speed">0x</div>
            </div>
        </div>

        <div class="grid-layout">
            <!-- Sidebar Controls -->
            <div class="card">
                <div class="card-title">
                    ⚙️ Cấu Hình & Chọn Phân Đoạn
                </div>

                <div class="form-group">
                    <label>1. CHỌN FILE AUDIO MẪU</label>
                    <select id="audio-select" onchange="onAudioSelectChange()">
                        <option value="">⏳ Đang tải danh sách file...</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>2. ĐỘ DÀI MỖI PHÂN ĐOẠN</label>
                    <select id="segment-size" onchange="generateSegmentCheckboxes()">
                        <option value="60">1 Phút / Đoạn</option>
                        <option value="180" selected>3 Phút / Đoạn (Khuyên dùng)</option>
                        <option value="300">5 Phút / Đoạn</option>
                    </select>
                </div>

                <div class="form-group">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem">
                        <label style="margin: 0">3. CHỌN ĐOẠN ĐỂ CHẠY THÍ NGHIỆM</label>
                        <span style="font-size: 0.75rem; color: var(--accent-cyan); cursor: pointer" onclick="toggleSelectAllSegments()">Chọn tất cả</span>
                    </div>
                    <div class="segment-selector-grid" id="segment-checkboxes-container">
                        <span style="font-size: 0.8rem; color: var(--text-muted)">Vui lòng chọn file audio ở trên</span>
                    </div>
                </div>

                <div class="button-group">
                    <button class="btn-primary" id="btn-run" onclick="startExperiment()">
                        ▶️ CHẠY AI
                    </button>
                    <button class="btn-stop" id="btn-stop" onclick="stopExperiment()" disabled>
                        🛑 DỪNG
                    </button>
                </div>

                <div style="margin-top: 1.2rem; padding-top: 1rem; border-top: 1px solid var(--panel-border); font-size: 0.78rem; color: var(--text-muted); line-height: 1.5">
                    💡 <b>Bộ lọc Groq AI LLM (GPT-OSS-120B):</b><br>
                    • Tự động <b>lọc sạch 100% các câu tán gẫu, trò chuyện cá nhân</b>.<br>
                    • Trích xuất chỉ: Mã cổ phiếu, Xu hướng (Tăng/Giảm), Mốc giá Kháng cự/Hỗ trợ/Cắt lỗ.<br>
                    • Bạn có thể chọn cụ thể đoạn muốn chạy và bấm nút DỪNG bất kỳ lúc nào!
                </div>
            </div>

            <!-- Main Content Area -->
            <div>
                <div class="audio-player-wrapper">
                    <audio id="main-audio-player" controls>
                        <source src="" type="audio/mpeg">
                        Browser không hỗ trợ Audio player.
                    </audio>
                </div>

                <div class="progress-wrapper">
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600">
                        <span id="progress-status-text">Sẵn sàng chạy thử nghiệm...</span>
                        <span id="progress-percent">0%</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" id="progress-fill"></div>
                    </div>
                </div>

                <!-- Live Stream Feed of Segments -->
                <div class="card">
                    <div class="card-title">
                        🤖 Báo Cáo Phân Tích Chuyên Sâu AI (Đã Lọc Tán Gẫu)
                    </div>

                    <div id="segment-feed" class="segment-feed">
                        <div class="empty-state">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.287a6 6 0 010 7.426M12 9v6m0 0l-3-3m3 3l3-3m-12 3a9 9 0 1118 0 9 9 0 01-18 0z" />
                            </svg>
                            <p>Chọn các phân đoạn muốn phân tích ở bảng bên trái và bấm <b>"▶️ CHẠY AI"</b> để xem kết quả.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let totalDurationSec = 0;
        let selectedFilename = "";
        let allDiscoveredTickers = new Set();
        let isRunning = false;
        let shouldStop = false;

        document.addEventListener("DOMContentLoaded", () => {
            loadAudioFilesList();
        });

        async function loadAudioFilesList() {
            try {
                const res = await fetch("/api/audio_files");
                const data = await res.json();
                const select = document.getElementById("audio-select");
                select.innerHTML = "";

                if (data.files && data.files.length > 0) {
                    data.files.forEach(f => {
                        const opt = document.createElement("option");
                        opt.value = f.filename;
                        opt.textContent = `${f.filename} (${f.size_mb} MB)`;
                        select.appendChild(opt);
                    });
                    onAudioSelectChange();
                } else {
                    select.innerHTML = "<option value=''>Không tìm thấy file audio nào</option>";
                }
            } catch (err) {
                console.error("Lỗi nạp audio files:", err);
            }
        }

        async function onAudioSelectChange() {
            const select = document.getElementById("audio-select");
            selectedFilename = select.value;
            if (!selectedFilename) return;

            const player = document.getElementById("main-audio-player");
            player.src = `/api/audio_stream?file=${encodeURIComponent(selectedFilename)}`;

            try {
                const res = await fetch("/api/audio_info", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ filename: selectedFilename })
                });
                const data = await res.json();
                if (data.duration_sec) {
                    totalDurationSec = data.duration_sec;
                    document.getElementById("stat-duration").textContent = formatMinSec(totalDurationSec);
                    generateSegmentCheckboxes();
                }
            } catch (e) {
                console.error("Lỗi lấy thông tin audio:", e);
            }
        }

        function formatMinSec(totalSec) {
            const m = Math.floor(totalSec / 60);
            const s = Math.floor(totalSec % 60);
            return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        }

        function generateSegmentCheckboxes() {
            const container = document.getElementById("segment-checkboxes-container");
            container.innerHTML = "";

            if (totalDurationSec <= 0) return;

            const segSizeSec = parseInt(document.getElementById("segment-size").value);
            const totalSegments = Math.ceil(totalDurationSec / segSizeSec);

            for (let i = 0; i < totalSegments; i++) {
                const startSec = i * segSizeSec;
                const endSec = Math.min((i + 1) * segSizeSec, totalDurationSec);
                const timeStr = `${formatMinSec(startSec)} - ${formatMinSec(endSec)}`;

                const item = document.createElement("label");
                item.className = "segment-checkbox-item";
                item.innerHTML = `
                    <input type="checkbox" class="seg-cb" value="${i}" data-start="${startSec}" data-dur="${endSec - startSec}" checked>
                    <span>Phân đoạn #${i + 1} (${timeStr})</span>
                `;
                container.appendChild(item);
            }
        }

        function toggleSelectAllSegments() {
            const checkboxes = document.querySelectorAll(".seg-cb");
            const anyUnchecked = Array.from(checkboxes).some(cb => !cb.checked);
            checkboxes.forEach(cb => cb.checked = anyUnchecked);
        }

        function stopExperiment() {
            if (isRunning) {
                shouldStop = true;
                document.getElementById("progress-status-text").textContent = "🛑 Đang gửi lệnh dừng...";
            }
        }

        async function startExperiment() {
            if (!selectedFilename || totalDurationSec <= 0) {
                alert("Vui lòng chọn một file audio hợp lệ!");
                return;
            }

            const selectedCBs = Array.from(document.querySelectorAll(".seg-cb:checked"));
            if (selectedCBs.length === 0) {
                alert("Vui lòng tích chọn ít nhất 1 phân đoạn để chạy!");
                return;
            }

            isRunning = true;
            shouldStop = false;

            document.getElementById("btn-run").disabled = true;
            document.getElementById("btn-stop").disabled = false;
            document.getElementById("segment-feed").innerHTML = "";
            allDiscoveredTickers.clear();
            document.getElementById("stat-tickers-count").textContent = "0";

            let completedSegs = 0;
            const totalSelected = selectedCBs.length;

            for (let i = 0; i < totalSelected; i++) {
                if (shouldStop) {
                    document.getElementById("progress-status-text").textContent = "🛑 ĐÃ DỪNG THÍ NGHIỆM THEO YÊU CẦU!";
                    break;
                }

                const cb = selectedCBs[i];
                const segIdx = parseInt(cb.value);
                const startSec = parseInt(cb.getAttribute("data-start"));
                const durSec = parseInt(cb.getAttribute("data-dur"));

                const percent = Math.round(((i) / totalSelected) * 100);
                document.getElementById("progress-fill").style.width = `${percent}%`;
                document.getElementById("progress-percent").textContent = `${percent}%`;
                document.getElementById("progress-status-text").textContent = `🧠 Groq AI đang dịch & phân tích Đoạn #${segIdx + 1} (${formatMinSec(startSec)})...`;
                document.getElementById("stat-segments").textContent = `${completedSegs} / ${totalSelected}`;

                try {
                    const res = await fetch("/api/process_segment", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            filename: selectedFilename,
                            start_sec: startSec,
                            duration_sec: durSec,
                            segment_idx: segIdx
                        })
                    });
                    const data = await res.json();

                    if (data.status === "success") {
                        completedSegs++;
                        const totalTime = (data.proc_time_sec || 1) + (data.llm_time_sec || 0);
                        const speedFactor = Math.round((durSec / totalTime) * 10) / 10;
                        document.getElementById("stat-speed").textContent = `${speedFactor}x`;

                        if (data.tickers && data.tickers.length > 0) {
                            data.tickers.forEach(t => allDiscoveredTickers.add(t.ticker));
                            document.getElementById("stat-tickers-count").textContent = allDiscoveredTickers.size;
                        }

                        renderSegmentCard(data);
                    }
                } catch (err) {
                    console.error(`Lỗi xử lý segment ${segIdx}:`, err);
                }
            }

            if (!shouldStop) {
                document.getElementById("progress-fill").style.width = "100%";
                document.getElementById("progress-percent").textContent = "100%";
                document.getElementById("progress-status-text").textContent = "🎉 HOÀN THÀNH TOÀN BỘ CÁC PHÂN ĐOẠN ĐÃ CHỌN!";
            }

            document.getElementById("stat-segments").textContent = `${completedSegs} / ${totalSelected}`;
            document.getElementById("btn-run").disabled = false;
            document.getElementById("btn-stop").disabled = true;
            isRunning = false;
        }

        function renderSegmentCard(data) {
            const feed = document.getElementById("segment-feed");

            let tickerBadgesHtml = "";
            if (data.tickers && data.tickers.length > 0) {
                tickerBadgesHtml = data.tickers.map(t => `
                    <div class="ticker-badge" onclick="jumpAudioTo(${data.start_sec})">
                        🏷️ ${t.ticker} (${t.name})
                    </div>
                `).join("");
            } else {
                tickerBadgesHtml = `<span style="font-size: 0.8rem; color: var(--text-muted)">Không có mã cụ thể trong đoạn này</span>`;
            }

            // Convert markdown simple bolding to HTML
            let formattedAnalysis = data.llm_analysis || "Chưa có phân tích";
            formattedAnalysis = formattedAnalysis
                .replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>')
                .replace(/\\n/g, '<br>');

            const cardHtml = `
                <div class="segment-card">
                    <div class="segment-header">
                        <div class="segment-time" onclick="jumpAudioTo(${data.start_sec})">
                            ▶️ Phân đoạn #${data.segment_idx + 1} (${data.time_str})
                        </div>
                        <div class="segment-speed">
                            ⚡ Groq STT: <b>${data.proc_time_sec}s</b> | LLM: <b>${data.llm_time_sec}s</b>
                        </div>
                    </div>

                    <div class="ticker-badges">
                        ${tickerBadgesHtml}
                    </div>

                    <!-- Groq LLM Intelligence Analysis Box -->
                    <div class="llm-analysis-box">
                        <div class="llm-analysis-header">
                            🤖 BÁO CÁO PHÂN TÍCH GROQ AI (GPT-OSS-120B)
                        </div>
                        <div>${formattedAnalysis}</div>
                    </div>

                    <!-- Collapsible Raw Transcript -->
                    <div class="transcript-collapsible">
                        <button class="transcript-toggle-btn" onclick="toggleRawTranscript(this)">
                            ▼ Xem văn bản bóc tách thô (Whisper STT)
                        </button>
                        <div class="transcript-text" style="display: none;">
                            "${data.transcript || 'Không có âm thanh'}"
                        </div>
                    </div>
                </div>
            `;

            feed.insertAdjacentHTML("beforeend", cardHtml);
        }

        function toggleRawTranscript(btn) {
            const txtBox = btn.nextElementSibling;
            if (txtBox.style.display === "none") {
                txtBox.style.display = "block";
                btn.textContent = "▲ Ẩn văn bản bóc tách thô";
            } else {
                txtBox.style.display = "none";
                btn.textContent = "▼ Xem văn bản bóc tách thô (Whisper STT)";
            }
        }

        function jumpAudioTo(seconds) {
            const player = document.getElementById("main-audio-player");
            player.currentTime = seconds;
            player.play();
        }
    </script>
</body>
</html>
"""

def main():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    print("=" * 70)
    print(f"🚀 SPEECH AI INSPECTOR WITH GROQ LLM READY AT: http://localhost:{PORT}")
    print("=" * 70)
    httpd.serve_forever()

if __name__ == "__main__":
    main()
