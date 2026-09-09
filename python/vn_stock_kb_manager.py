"""
Vietnamese Stock Knowledge Base & Normalizer Manager (Supabase DB Backed)
Handles spoken phonetics (e.g. 'ci ô', 'xeo', 'ci i ô' -> 'CEO'), normalization & logging.
"""
import os
import re
import json
import requests

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

# 🌟 CƠ SỞ KIẾN THỨC MÃ CHỨNG KHOÁN VIỆT NAM (DỮ LIỆU GỐC BAN ĐẦU)
DEFAULT_STOCK_KB = [
    {
        "ticker": "CEO",
        "company_name": "Tập đoàn CEO",
        "industry": "Bất động sản",
        "exchange": "HNX",
        "aliases": ["ceo", "c-e-o", "c e o", "ci ô", "ci i ô", "xeo", "xê e o", "tập đoàn ceo", "bất động sản ceo"]
    },
    {
        "ticker": "SSI",
        "company_name": "Công ty Cổ phần Chứng khoán SSI",
        "industry": "Chứng khoán",
        "exchange": "HOSE",
        "aliases": ["ssi", "s-s-i", "s i", "ép-sơ-sơ-y", "ép ép y", "chứng khoán ssi", "chứng khoán s i"]
    },
    {
        "ticker": "HPG",
        "company_name": "Tập đoàn Hòa Phát",
        "industry": "Thép",
        "exchange": "HOSE",
        "aliases": ["hpg", "h-p-g", "h p g", "hát pơ gờ", "thép hòa phát", "hòa phát", "hát bê gê"]
    },
    {
        "ticker": "DIG",
        "company_name": "Tổng Công ty Cổ phần Đầu tư Phát triển Xây dựng (DIC Corp)",
        "industry": "Bất động sản",
        "exchange": "HOSE",
        "aliases": ["dig", "d-i-g", "d i g", "đê y gê", "đích corp", "dic corp", "đích"]
    },
    {
        "ticker": "NVL",
        "company_name": "Công ty Cổ phần Tập đoàn Đầu tư Địa ốc No Va (Novaland)",
        "industry": "Bất động sản",
        "exchange": "HOSE",
        "aliases": ["nvl", "n-v-l", "n v l", "novaland", "nờ ve lờ", "nô va land"]
    },
    {
        "ticker": "VHM",
        "company_name": "Công ty Cổ phần Vinhomes",
        "industry": "Bất động sản",
        "exchange": "HOSE",
        "aliases": ["vhm", "v-h-m", "v h m", "vinhomes", "ve hát mờ", "vin home"]
    },
    {
        "ticker": "VIC",
        "company_name": "Tập đoàn Vingroup",
        "industry": "Bất động sản",
        "exchange": "HOSE",
        "aliases": ["vic", "v-i-c", "v i c", "vingroup", "ve y cờ", "vin group"]
    },
    {
        "ticker": "VND",
        "company_name": "Công ty Cổ phần Chứng khoán VNDIRECT",
        "industry": "Chứng khoán",
        "exchange": "HOSE",
        "aliases": ["vnd", "v-n-d", "v n d", "vndirect", "vn direct", "ve nờ đê"]
    },
    {
        "ticker": "HCM",
        "company_name": "Công ty Cổ phần Chứng khoán TP.HCM (HSC)",
        "industry": "Chứng khoán",
        "exchange": "HOSE",
        "aliases": ["hcm", "hsc", "h-c-m", "h c m", "hát xê mờ", "chứng khoán hsc"]
    },
    {
        "ticker": "VCI",
        "company_name": "Công ty Cổ phần Chứng khoán Vietcap",
        "industry": "Chứng khoán",
        "exchange": "HOSE",
        "aliases": ["vci", "vietcap", "v-c-i", "v c i", "ve xê y", "chứng khoán bản việt"]
    },
    {
        "ticker": "MWG",
        "company_name": "Công ty Cổ phần Đầu tư Thế Giới Di Động",
        "industry": "Bán lẻ",
        "exchange": "HOSE",
        "aliases": ["mwg", "m-w-g", "m w g", "tgdd", "thế giới di động", "mờ vê gê"]
    },
    {
        "ticker": "FPT",
        "company_name": "Công ty Cổ phần FPT",
        "industry": "Công nghệ",
        "exchange": "HOSE",
        "aliases": ["fpt", "f-p-t", "f p t", "ép bê tê", "công nghệ fpt"]
    },
    {
        "ticker": "VCB",
        "company_name": "Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)",
        "industry": "Ngân hàng",
        "exchange": "HOSE",
        "aliases": ["vcb", "vietcombank", "v-c-b", "v c b", "ve xê bê", "ngân hàng ngoại thương"]
    },
    {
        "ticker": "MBB",
        "company_name": "Ngân hàng TMCP Quân đội (MBBank)",
        "industry": "Ngân hàng",
        "exchange": "HOSE",
        "aliases": ["mbb", "mbbank", "mb bank", "m-b-b", "m b b", "mờ bê bê", "ngân hàng quân đội"]
    },
    {
        "ticker": "TCB",
        "company_name": "Ngân hàng TMCP Kỹ thương Việt Nam (Techcombank)",
        "industry": "Ngân hàng",
        "exchange": "HOSE",
        "aliases": ["tcb", "techcombank", "t-c-b", "t c b", "tê xê bê"]
    },
    {
        "ticker": "STB",
        "company_name": "Ngân hàng TMCP Sài Gòn Thương Tín (Sacombank)",
        "industry": "Ngân hàng",
        "exchange": "HOSE",
        "aliases": ["stb", "sacombank", "s-t-b", "s t b", "ép tê bê"]
    },
    {
        "ticker": "PDR",
        "company_name": "Công ty Cổ phần Phát triển Bất động sản Phát Đạt",
        "industry": "Bất động sản",
        "exchange": "HOSE",
        "aliases": ["pdr", "phát đạt", "p-d-r", "p d r", "pê đê rờ"]
    },
    {
        "ticker": "DXG",
        "company_name": "Công ty Cổ phần Tập đoàn Đất Xanh",
        "industry": "Bất động sản",
        "exchange": "HOSE",
        "aliases": ["dxg", "đất xanh", "d-x-g", "d x g", "đê ích gê"]
    },
    {
        "ticker": "HSG",
        "company_name": "Công ty Cổ phần Tập đoàn Hoa Sen",
        "industry": "Thép",
        "exchange": "HOSE",
        "aliases": ["hsg", "hoa sen", "h-s-g", "h s g", "hát ép gê", "thép hoa sen"]
    },
    {
        "ticker": "NKG",
        "company_name": "Công ty Cổ phần Thép Nam Kim",
        "industry": "Thép",
        "exchange": "HOSE",
        "aliases": ["nkg", "nam kim", "n-k-g", "n k g", "nờ ca gê", "thép nam kim"]
    }
]

def seed_stocks_kb_to_supabase():
    """
    Nạp toàn bộ cơ sở dữ liệu gốc mã chứng khoán & các biến thể phát âm lên Supabase DB table 'vn_stocks_kb'
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ℹ️ Thiếu SUPABASE_URL/KEY, dùng local KB cache.")
        return False

    db_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/vn_stocks_kb"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apiKey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    try:
        res = requests.post(db_url, headers=headers, json=DEFAULT_STOCK_KB, timeout=10)
        if res.status_code in [200, 201]:
            print("🚀 ĐÃ ĐỒNG BỘ NẠP DỮ LIỆU KNOWLEDGE BASE MÃ CHỨNG KHOÁN LÊN SUPABASE DB SUCCESSFUL!")
            return True
        else:
            print(f"ℹ️ Sync KB Supabase Note ({res.status_code}): {res.text}")
            return False
    except Exception as e:
        print(f"⚠️ Lỗi kết nối Supabase KB: {e}")
        return False

def load_stock_kb() -> list:
    """
    Đọc dữ liệu Knowledge Base từ Supabase DB table 'vn_stocks_kb', fallback sang DEFAULT_STOCK_KB nếu mất mạng
    """
    if SUPABASE_URL and SUPABASE_KEY:
        db_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/vn_stocks_kb?select=*"
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apiKey": SUPABASE_KEY
        }
        try:
            res = requests.get(db_url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass

    return DEFAULT_STOCK_KB

def add_alias_to_ticker(ticker_name: str, new_alias: str) -> bool:
    """
    Thêm động 1 từ lóng / phát âm biến thể mới vào Supabase DB cho mã chứng khoán mà KHÔNG CẦN sửa code!
    """
    clean_ticker = ticker_name.strip().upper()
    clean_alias = new_alias.strip().lower()
    if not clean_ticker or not clean_alias:
        return False

    kb = load_stock_kb()
    target_item = None
    for item in kb:
        if item["ticker"].upper() == clean_ticker:
            target_item = item
            break

    if not target_item:
        print(f"⚠️ Không tìm thấy mã {clean_ticker} trong Knowledge Base!")
        return False

    aliases = target_item.get("aliases", [])
    if isinstance(aliases, str):
        try:
            aliases = json.loads(aliases)
        except Exception:
            aliases = []

    if clean_alias not in [a.lower() for a in aliases]:
        aliases.append(clean_alias)
        target_item["aliases"] = aliases

        if SUPABASE_URL and SUPABASE_KEY:
            db_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/vn_stocks_kb?ticker=eq.{clean_ticker}"
            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "apiKey": SUPABASE_KEY,
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            try:
                res = requests.patch(db_url, headers=headers, json={"aliases": aliases}, timeout=5)
                if res.status_code in [200, 204]:
                    print(f"✅ Đã thêm từ lóng mới '{clean_alias}' cho mã {clean_ticker} trên Supabase DB!")
                    return True
            except Exception as e:
                print(f"⚠️ Lỗi cập nhật Supabase alias: {e}")

    return False

def normalize_and_extract_tickers(raw_transcript: str) -> list:
    """
    HÀM CHUẨN HÓA MÃ CHỨNG KHOÁN:
    - Đọc qua toàn bộ phát âm biến thể ('ci ô', 'xeo', 'ci i ô', 'đích corp', 'hát pơ gờ'...)
    - Chuẩn hóa quy đổi chính xác về Mã cổ phiếu chuẩn ('CEO', 'DIG', 'HPG'...)
    """
    if not raw_transcript:
        return []

    text_lower = raw_transcript.lower()
    kb = load_stock_kb()
    matches = []
    seen = set()

    for item in kb:
        ticker = item["ticker"]
        if ticker in seen:
            continue

        aliases = item.get("aliases", [])
        if isinstance(aliases, str):
            try:
                aliases = json.loads(aliases)
            except Exception:
                aliases = [ticker.lower()]

        # 1. Khớp mã viết tắt chính xác (Word boundary)
        pattern = rf"\b{ticker.lower()}\b"
        if re.search(pattern, text_lower):
            seen.add(ticker)
            matches.append({
                "ticker": ticker,
                "company_name": item.get("company_name", ticker),
                "industry": item.get("industry", "Chứng khoán"),
                "exchange": item.get("exchange", "HOSE"),
                "matched_term": ticker,
                "confidence": 0.98
            })
            continue

        # 2. Khớp các biến thể phát âm (Pronunciation & Spoken aliases e.g. "xeo", "ci ô", "ci i ô")
        for alias in aliases:
            alias_clean = alias.strip().lower()
            if not alias_clean:
                continue

            alias_pattern = rf"\b{re.escape(alias_clean)}\b"
            if re.search(alias_pattern, text_lower):
                seen.add(ticker)
                matches.append({
                    "ticker": ticker,
                    "company_name": item.get("company_name", ticker),
                    "industry": item.get("industry", "Chứng khoán"),
                    "exchange": item.get("exchange", "HOSE"),
                    "matched_term": alias_clean,
                    "confidence": 0.92
                })
                break

    # 3. Regex dự phòng cho các mã 3 chữ viết hoa (e.g. VNM, GEX...)
    raw_upper_words = re.findall(r"\b[A-Z]{3}\b", raw_transcript)
    for word in raw_upper_words:
        if word not in seen:
            seen.add(word)
            matches.append({
                "ticker": word,
                "company_name": f"Mã {word}",
                "industry": "Thị trường",
                "exchange": "HOSE",
                "matched_term": word,
                "confidence": 0.85
            })

    return matches

def log_extracted_tickers_to_supabase(channel: str, session_id: str, matches: list, raw_transcript: str):
    """
    Lưu nhật ký tất cả mã cổ phiếu đã chuẩn hóa và phát hiện xuống Supabase DB table 'extracted_ticker_logs'
    """
    if not SUPABASE_URL or not SUPABASE_KEY or not matches:
        return

    db_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/extracted_ticker_logs"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apiKey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    payloads = []
    for m in matches:
        payloads.append({
            "channel": channel,
            "session_id": session_id,
            "ticker": m["ticker"],
            "matched_term": m["matched_term"],
            "raw_transcript": raw_transcript[:500]
        })

    try:
        requests.post(db_url, headers=headers, json=payloads, timeout=5)
        print(f"💾 Đã lưu {len(payloads)} nhật ký mã chứng khoán xuống Supabase table 'extracted_ticker_logs'!")
    except Exception as e:
        print(f"⚠️ Lỗi lưu nhật ký ticker Supabase: {e}")

if __name__ == "__main__":
    # Test Seeding to Supabase
    seed_stocks_kb_to_supabase()

    # Test Phonetic Normalization
    test_sample = "mọi người hỏi là xeo 26 giữ không anh, rồi ci ô với ci i ô đà tăng thế nào, với đích corp gãy 30 thì bán nhé"
    res = normalize_and_extract_tickers(test_sample)
    print("\n🔍 DỮ LIỆU ĐÃ ĐƯỢC CHUẨN HÓA:")
    for r in res:
        print(f"  👉 Phonetic Speech Matched: '{r['matched_term']}' ==> CHUẨN HÓA VỀ MÃ: {r['ticker']} ({r['company_name']} - {r['industry']})")
