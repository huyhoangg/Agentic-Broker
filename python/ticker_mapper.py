"""
Vietnamese Stock Ticker Extractor & Phonetic Normalizer Module (Expanded Dictionary)
"""
import re
from typing import List, Dict, Any

VN_STOCK_DATABASE = [
    # --- Chứng khoán ---
    {"ticker": "SSI", "name": "Chứng khoán SSI", "industry": "Chứng khoán", "aliases": ["ssi", "s-s-i", "ép-sơ-sơ-y", "chứng khoán ssi"]},
    {"ticker": "VND", "name": "VNDirect", "industry": "Chứng khoán", "aliases": ["vndirect", "vnd", "v-n-d", "ve nờ đê"]},
    {"ticker": "HCM", "name": "Chứng khoán TP.HCM (HSC)", "industry": "Chứng khoán", "aliases": ["hcm", "hsc", "h-c-m", "hát xê mờ"]},
    {"ticker": "VCI", "name": "Chứng khoán Vietcap", "industry": "Chứng khoán", "aliases": ["vci", "vietcap", "v-c-i", "ve xê y"]},
    {"ticker": "SHS", "name": "Chứng khoán Sài Gòn - Hà Nội", "industry": "Chứng khoán", "aliases": ["shs", "s-h-s", "ép hát ép"]},
    {"ticker": "MBS", "name": "Chứng khoán MB", "industry": "Chứng khoán", "aliases": ["mbs", "m-b-s", "mờ bê ép"]},
    {"ticker": "FTS", "name": "Chứng khoán FPT", "industry": "Chứng khoán", "aliases": ["fts", "f-t-s", "ép tê ép"]},

    # --- Thép ---
    {"ticker": "HPG", "name": "Tập đoàn Hòa Phát", "industry": "Thép", "aliases": ["hòa phát", "h-p-g", "hát pơ gờ", "h p g", "thép hòa phát"]},
    {"ticker": "HSG", "name": "Tập đoàn Hoa Sen", "industry": "Thép", "aliases": ["hoa sen", "hsg", "h-s-g", "hát ép gê", "thép hoa sen"]},
    {"ticker": "NKG", "name": "Thép Nam Kim", "industry": "Thép", "aliases": ["nam kim", "nkg", "n-k-g", "nờ ca gê", "thép nam kim"]},

    # --- Bất động sản ---
    {"ticker": "DIG", "name": "DIC Corp", "industry": "Bất động sản", "aliases": ["đê y gê", "d-i-g", "dic corp", "d i g", "đích corp"]},
    {"ticker": "CEO", "name": "Tập đoàn CEO", "industry": "Bất động sản", "aliases": ["c-e-o", "xê e o", "c e o", "tập đoàn ceo"]},
    {"ticker": "NVL", "name": "Novaland", "industry": "Bất động sản", "aliases": ["novaland", "n-v-l", "nờ ve lờ", "n v l"]},
    {"ticker": "VHM", "name": "Vinhomes", "industry": "Bất động sản", "aliases": ["vinhomes", "v-h-m", "ve hát mờ", "v h m"]},
    {"ticker": "VIC", "name": "Tập đoàn Vingroup", "industry": "Bất động sản", "aliases": ["vingroup", "v-i-c", "ve y cờ", "v i c"]},
    {"ticker": "PDR", "name": "Phát Đạt", "industry": "Bất động sản", "aliases": ["phát đạt", "pdr", "p-d-r", "pê đê rờ"]},
    {"ticker": "DXG", "name": "Đất Xanh Group", "industry": "Bất động sản", "aliases": ["đất xanh", "dxg", "d-x-g", "đê ích gê"]},
    {"ticker": "KBC", "name": "Kinh Bắc City", "industry": "Bất động sản KCN", "aliases": ["kinh bắc", "kbc", "k-b-c", "ca bê xê"]},

    # --- Ngân hàng ---
    {"ticker": "VCB", "name": "Vietcombank", "industry": "Ngân hàng", "aliases": ["vietcombank", "vcb", "v-c-b", "ve xê bê"]},
    {"ticker": "BID", "name": "BIDV", "industry": "Ngân hàng", "aliases": ["bidv", "bid", "b-i-d", "bê y đê"]},
    {"ticker": "CTG", "name": "VietinBank", "industry": "Ngân hàng", "aliases": ["vietinbank", "ctg", "c-t-g", "xê tê gê"]},
    {"ticker": "TCB", "name": "Techcombank", "industry": "Ngân hàng", "aliases": ["techcombank", "tcb", "t-c-b", "tê xê bê"]},
    {"ticker": "MBB", "name": "MB Bank", "industry": "Ngân hàng", "aliases": ["mb bank", "mbb", "m-b-b", "mờ bê bê", "ngân hàng quân đội"]},
    {"ticker": "VPB", "name": "VPBank", "industry": "Ngân hàng", "aliases": ["vpbank", "vpb", "v-p-b", "ve pê bê"]},
    {"ticker": "ACB", "name": "ACB", "industry": "Ngân hàng", "aliases": ["acb", "a-c-b", "a xê bê"]},
    {"ticker": "STB", "name": "Sacombank", "industry": "Ngân hàng", "aliases": ["sacombank", "stb", "s-t-b", "ép tê bê"]},
    {"ticker": "SHB", "name": "SHB", "industry": "Ngân hàng", "aliases": ["shb", "s-h-b", "ép hát bê"]},

    # --- Trụ & Bán lẻ & Công nghệ ---
    {"ticker": "FPT", "name": "Tập đoàn FPT", "industry": "Công nghệ", "aliases": ["fpt", "f-p-t", "ép bê tê"]},
    {"ticker": "MWG", "name": "Thế Giới Di Động", "industry": "Bán lẻ", "aliases": ["thế giới di động", "mwg", "m-w-g", "mờ vê gê", "tgdd"]},
    {"ticker": "VNM", "name": "Vinamilk", "industry": "Thực phẩm", "aliases": ["vinamilk", "vnm", "v-n-m", "ve nờ mờ"]},
    {"ticker": "GEX", "name": "Gelex", "industry": "Điện & Thiết bị", "aliases": ["gelex", "gex", "g-e-x", "gê e ích"]},
    {"ticker": "DGC", "name": "Hóa chất Đức Giang", "industry": "Hóa chất", "aliases": ["đức giang", "dgc", "d-g-c", "đê gê xê"]}
]

def extract_vn_tickers(raw_transcript: str) -> List[Dict[str, Any]]:
    """
    Scans transcribed text to extract VN stock tickers matching direct symbols or spoken phonetics.
    """
    if not raw_transcript:
        return []

    text_lower = raw_transcript.lower()
    matches = []
    seen = set()

    # 1. Check known database dictionary
    for stock in VN_STOCK_DATABASE:
        ticker = stock["ticker"]
        if ticker in seen:
            continue

        # Exact Ticker Word Boundary match
        pattern = rf"\b{ticker.lower()}\b"
        if re.search(pattern, text_lower):
            seen.add(ticker)
            matches.append({
                "ticker": ticker,
                "name": stock["name"],
                "industry": stock["industry"],
                "matched_term": ticker,
                "confidence": 0.98
            })
            continue

        # Alias / Spoken name match
        for alias in stock["aliases"]:
            if alias.lower() in text_lower:
                seen.add(ticker)
                matches.append({
                    "ticker": ticker,
                    "name": stock["name"],
                    "industry": stock["industry"],
                    "matched_term": alias,
                    "confidence": 0.90
                })
                break

    # 2. General 3-Letter Upper-Case Ticker regex fallback
    raw_words = re.findall(r"\b[A-Z]{3}\b", raw_transcript)
    for word in raw_words:
        if word not in seen:
            seen.add(word)
            matches.append({
                "ticker": word,
                "name": f"Mã {word}",
                "industry": "Thị trường",
                "matched_term": word,
                "confidence": 0.85
            })

    return matches
