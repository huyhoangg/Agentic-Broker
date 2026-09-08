"""
Vietnamese Stock Ticker Extractor & Phonetic Normalizer Module
"""
import re
from typing import List, Dict, Any

VN_STOCK_DATABASE = [
    {
        "ticker": "HPG",
        "name": "Tập đoàn Hòa Phát",
        "industry": "Thép",
        "aliases": ["hòa phát", "h-p-g", "hát pơ gờ", "h p g", "thép hòa phát"]
    },
    {
        "ticker": "SSI",
        "name": "Công ty Cổ phần Chứng khoán SSI",
        "industry": "Chứng khoán",
        "aliases": ["ssi", "s-s-i", "ép-sơ-sơ-y", "chứng khoán ssi", "chứng khoán s i"]
    },
    {
        "ticker": "VHM",
        "name": "Công ty Cổ phần Vinhomes",
        "industry": "Bất động sản",
        "aliases": ["vinhomes", "v-h-m", "ve hát mờ", "v h m"]
    },
    {
        "ticker": "VIC",
        "name": "Tập đoàn Vingroup",
        "industry": "Bất động sản",
        "aliases": ["vingroup", "v-i-c", "ve y cờ", "v i c"]
    },
    {
        "ticker": "DIG",
        "name": "DIC Corp",
        "industry": "Bất động sản",
        "aliases": ["đê y gê", "d-i-g", "dic corp", "d i g", "đích corp"]
    },
    {
        "ticker": "CEO",
        "name": "Tập đoàn CEO",
        "industry": "Bất động sản",
        "aliases": ["c-e-o", "xê e o", "c e o"]
    },
    {
        "ticker": "NVL",
        "name": "Novaland",
        "industry": "Bất động sản",
        "aliases": ["novaland", "n-v-l", "nờ ve lờ", "n v l"]
    },
    {
        "ticker": "MWG",
        "name": "Thế Giới Di Động",
        "industry": "Bán lẻ",
        "aliases": ["thế giới di động", "m-w-g", "mờ vê gê", "tgdd"]
    },
    {
        "ticker": "FPT",
        "name": "Tập đoàn FPT",
        "industry": "Công nghệ",
        "aliases": ["fpt", "f-p-t", "ép bê tê", "f p t"]
    },
    {
        "ticker": "VCB",
        "name": "Vietcombank",
        "industry": "Ngân hàng",
        "aliases": ["vietcombank", "vcb", "v-c-b", "ve xê bê"]
    }
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

    for stock in VN_STOCK_DATABASE:
        ticker = stock["ticker"]
        if ticker in seen:
            continue

        # 1. Exact Ticker Word Boundary match
        pattern = rf"\b{ticker.lower()}\b"
        if re.search(pattern, text_lower):
            seen.add(ticker)
            matches.append({
                "ticker": ticker,
                "name": stock["name"],
                "matched_term": ticker,
                "confidence": 0.98
            })
            continue

        # 2. Alias / Spoken name match
        for alias in stock["aliases"]:
            if alias.lower() in text_lower:
                seen.add(ticker)
                matches.append({
                    "ticker": ticker,
                    "name": stock["name"],
                    "matched_term": alias,
                    "confidence": 0.90
                })
                break

    return matches
