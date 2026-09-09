"""
Vietnamese Stock Ticker Extractor & Phonetic Normalizer Wrapper
"""
import os
import sys

sys.path.append(os.path.dirname(__file__))

from vn_stock_kb_manager import normalize_and_extract_tickers as extract_vn_tickers

__all__ = ["extract_vn_tickers"]
