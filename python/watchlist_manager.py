"""
Watchlist & Stock Intelligence Digest Manager (Supabase DB Backed)
Manages user watched stocks (/watch, /unwatch, /watchlist) & stores AI digest reports to Supabase DB.
"""
import os
import requests
from datetime import datetime
from vn_stock_kb_manager import normalize_and_extract_tickers

# Auto-load .env file
env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_user_watchlist(chat_id: str) -> list:
    """
    Lấy danh sách các mã cổ phiếu đang quan tâm của user từ Supabase DB table 'user_watchlist'
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    db_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/user_watchlist?chat_id=eq.{chat_id}&select=ticker"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apiKey": SUPABASE_KEY
    }

    try:
        res = requests.get(db_url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return [item["ticker"] for item in data if "ticker" in item]
    except Exception as e:
        print(f"⚠️ Lỗi lấy watchlist từ Supabase: {e}")

    return []

def add_to_watchlist(chat_id: str, input_str: str) -> tuple:
    """
    Thêm mã cổ phiếu vào danh sách quan tâm của user trên Supabase DB
    """
    if not input_str:
        return False, [], "⚠️ Vui lòng nhập mã cổ phiếu! (Ví dụ: <code>/watch CEO, SSI, HPG</code>)"

    # Chuẩn hóa mã cổ phiếu qua Knowledge Base
    extracted = normalize_and_extract_tickers(input_str)
    raw_tickers = [w.strip().upper() for w in input_str.replace(",", " ").split() if len(w.strip()) >= 3]
    
    valid_tickers = set()
    for item in extracted:
        valid_tickers.add(item["ticker"])
    for r in raw_tickers:
        if len(r) == 3 and r.isalpha():
            valid_tickers.add(r)

    if not valid_tickers:
        return False, [], "⚠️ Không tìm thấy mã cổ phiếu hợp lệ!"

    added_list = []
    if SUPABASE_URL and SUPABASE_KEY:
        db_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/user_watchlist"
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apiKey": SUPABASE_KEY,
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

        payloads = [{"chat_id": chat_id, "ticker": t} for t in valid_tickers]
        try:
            res = requests.post(db_url, headers=headers, json=payloads, timeout=5)
            if res.status_code in [200, 201]:
                added_list = list(valid_tickers)
        except Exception as e:
            print(f"⚠️ Lỗi thêm watchlist Supabase: {e}")

    current_all = get_user_watchlist(chat_id)
    return True, added_list, current_all

def remove_from_watchlist(chat_id: str, input_str: str) -> tuple:
    """
    Xóa mã cổ phiếu khỏi danh sách quan tâm trên Supabase DB
    """
    raw_tickers = [w.strip().upper() for w in input_str.replace(",", " ").split() if len(w.strip()) >= 3]
    if not raw_tickers:
        return False, "⚠️ Vui lòng nhập mã muốn xóa! (Ví dụ: <code>/unwatch CEO</code>)"

    removed_count = 0
    if SUPABASE_URL and SUPABASE_KEY:
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apiKey": SUPABASE_KEY
        }
        for t in raw_tickers:
            db_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/user_watchlist?chat_id=eq.{chat_id}&ticker=eq.{t}"
            try:
                res = requests.delete(db_url, headers=headers, timeout=5)
                if res.status_code in [200, 204]:
                    removed_count += 1
            except Exception:
                pass

    current_all = get_user_watchlist(chat_id)
    return True, raw_tickers, current_all

def save_stock_digest_report(ticker: str, channel: str, summary: str, raw_transcript: str = "", audio_url: str = ""):
    """
    Lưu báo cáo tổng hợp thông tin mã cổ phiếu vào Supabase DB table 'stock_digest_reports'
    """
    if not SUPABASE_URL or not SUPABASE_KEY or not ticker:
        return False

    db_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/stock_digest_reports"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apiKey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    payload = {
        "ticker": ticker.upper(),
        "channel": channel,
        "summary": summary,
        "raw_transcript": raw_transcript[:500] if raw_transcript else "",
        "audio_url": audio_url,
        "created_at": datetime.now().isoformat()
    }

    try:
        res = requests.post(db_url, headers=headers, json=payload, timeout=5)
        if res.status_code in [200, 201]:
            print(f"💾 Đã lưu báo cáo mã {ticker} vào Supabase table 'stock_digest_reports'!")
            return True
    except Exception as e:
        print(f"⚠️ Lỗi lưu stock_digest_reports: {e}")

    return False

def get_recent_digest_for_watchlist(chat_id: str, limit: int = 5) -> list:
    """
    Tổng hợp tin tức & báo cáo AI mới nhất cho các mã thuộc danh sách quan tâm của User từ Supabase DB
    """
    watchlist = get_user_watchlist(chat_id)
    if not watchlist:
        return []

    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    # Query recent reports for tickers in watchlist
    tickers_param = ",".join(watchlist)
    db_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/stock_digest_reports?ticker=in.({tickers_param})&order=created_at.desc&limit={limit}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apiKey": SUPABASE_KEY
    }

    try:
        res = requests.get(db_url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"⚠️ Lỗi lấy digest từ Supabase: {e}")

    return []
