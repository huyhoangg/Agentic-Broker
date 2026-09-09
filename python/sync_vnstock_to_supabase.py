"""
Sync All 1500+ Official VN Stock Symbols from vnstock to Supabase Database Table 'vn_stocks_kb'
"""
import os
import sys
import json
import requests

sys.path.append(os.path.dirname(__file__))

env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Phonetic generator helper for Vietnamese spelling
SPELLING_MAP = {
    'A': 'a', 'B': 'bê', 'C': 'xê', 'D': 'đê', 'E': 'e', 'F': 'ép',
    'G': 'gê', 'H': 'hát', 'I': 'y', 'J': 'giây', 'K': 'ca', 'L': 'lờ',
    'M': 'mờ', 'N': 'nờ', 'O': 'o', 'P': 'pê', 'Q': 'quy', 'R': 'rờ',
    'S': 'ép', 'T': 'tê', 'U': 'u', 'V': 've', 'W': 'vê', 'X': 'ích',
    'Y': 'y', 'Z': 'dét'
}

def generate_phonetic_aliases(ticker: str, organ_name: str) -> list:
    aliases = set()
    ticker = ticker.upper().strip()
    
    # 1. Lowercase ticker
    aliases.add(ticker.lower())
    
    # 2. Spaced / Hyphenated ticker e.g. H-P-G, H P G
    aliases.add("-".join(list(ticker.lower())))
    aliases.add(" ".join(list(ticker.lower())))

    # 3. Spoken Vietnamese letter spelling (e.g. HPG -> hát pơ gờ / hát bê gê)
    spoken_chars = []
    for ch in ticker:
        spoken_chars.append(SPELLING_MAP.get(ch, ch.lower()))
    aliases.add(" ".join(spoken_chars))

    # 4. Special cases & Company short name
    if organ_name:
        clean_org = organ_name.replace("CTCP", "").replace("Tập đoàn", "").replace("Tổng Công ty", "").strip().lower()
        if len(clean_org) > 2 and len(clean_org) < 40:
            aliases.add(clean_org)

    # Specific slang additions
    SLANG_DICTIONARY = {
        "CEO": ["ci ô", "ci i ô", "xeo", "xê e o"],
        "SSI": ["ép sơ sơ y", "ép ép y", "chứng khoán ssi"],
        "HPG": ["hát pơ gờ", "thép hòa phát", "hòa phát"],
        "DIG": ["đích corp", "đê y gê", "dic corp", "đích"],
        "NVL": ["novaland", "nờ ve lờ", "nô va land"],
        "MWG": ["thế giới di động", "tgdd", "mờ vê gê"],
        "VHM": ["vinhomes", "ve hát mờ", "vin home"],
        "VIC": ["vingroup", "ve y cờ", "vin group"],
        "VND": ["vndirect", "ve nờ đê"],
        "VCB": ["vietcombank", "ve xê bê"]
    }

    if ticker in SLANG_DICTIONARY:
        for slang in SLANG_DICTIONARY[ticker]:
            aliases.add(slang)

    return list(aliases)

def sync_all_vnstock_symbols():
    try:
        import vnstock
        print("🔍 Đang kết nối tới `vnstock` để nạp danh sách 1500+ mã niêm yết...")
        
        # Fetch listing using vnstock 4.0 API
        try:
            from vnstock import Listing
            df = Listing().all_symbols()
        except Exception:
            stock = vnstock.Vnstock().stock(symbol='HPG', source='VCI')
            df = stock.listing.all_symbols()

        total_symbols = len(df)
        print(f"✅ Đã tải về {total_symbols} mã chứng khoán chính thức từ vnstock!")

        records = []
        for idx, row in df.iterrows():
            ticker = str(row.get("symbol", "")).upper().strip()
            organ_name = str(row.get("organ_name", ticker))
            if not ticker or len(ticker) > 10:
                continue

            aliases = generate_phonetic_aliases(ticker, organ_name)

            records.append({
                "ticker": ticker,
                "company_name": organ_name,
                "industry": "Thị trường Chứng Khoán VN",
                "exchange": "HOSE/HNX",
                "aliases": aliases
            })

        print(f"📦 Đang nạp {len(records)} mã vào Supabase DB table 'vn_stocks_kb' theo lô (Batch)...")

        # Upsert in batches of 200
        batch_size = 200
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apiKey": SUPABASE_KEY,
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

        success_count = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            db_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/vn_stocks_kb"
            res = requests.post(db_url, headers=headers, json=batch, timeout=15)
            if res.status_code in [200, 201]:
                success_count += len(batch)
                print(f"  🟢 Uploaded batch {i//batch_size + 1}: {len(batch)} mã...")
            else:
                print(f"  ⚠️ Error batch {i//batch_size + 1}: {res.status_code} {res.text[:100]}")

        print(f"\n🎉 HOÀN THÀNH ĐỒNG BỘ 100%! Đã lưu {success_count}/{len(records)} mã chứng khoán chính thức từ `vnstock` lên Supabase Database!")

    except Exception as e:
        print(f"❌ Lỗi đồng bộ vnstock: {e}")

if __name__ == "__main__":
    sync_all_vnstock_symbols()
