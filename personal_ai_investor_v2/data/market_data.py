import datetime as dt
import re
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from config import CACHE_TTL, INFO_CACHE_TTL, SCREENER_NAMES

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def history(symbol, period="2y"):
    try:
        h = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
        if h is None or h.empty: return pd.DataFrame()
        h = h[~h.index.duplicated(keep="last")].dropna(subset=["Close"])
        return h
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=INFO_CACHE_TTL, show_spinner=False)
def info(symbol):
    try:
        value = yf.Ticker(symbol).get_info()
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}

@st.cache_data(ttl=INFO_CACHE_TTL, show_spinner=False)
def financial_statements(symbol):
    """Fetch annual and quarterly statements independently; Yahoo may omit one or more."""
    ticker = yf.Ticker(symbol)
    result = {"income": pd.DataFrame(), "balance": pd.DataFrame(), "cashflow": pd.DataFrame(), "errors": []}
    getters = {
        "income": ("get_income_stmt", "income_stmt"),
        "balance": ("get_balance_sheet", "balance_sheet"),
        "cashflow": ("get_cash_flow", "cashflow"),
    }
    for key, (method_name, property_name) in getters.items():
        frame = pd.DataFrame()
        method = getattr(ticker, method_name, None)
        if callable(method):
            for freq in ("yearly", "quarterly"):
                try:
                    candidate = method(freq=freq)
                    if isinstance(candidate, pd.DataFrame) and not candidate.empty:
                        frame = candidate
                        break
                except Exception as exc:
                    result["errors"].append(f"{key} {freq}: {type(exc).__name__}")
        if frame.empty:
            try:
                candidate = getattr(ticker, property_name)
                if isinstance(candidate, pd.DataFrame) and not candidate.empty:
                    frame = candidate
            except Exception as exc:
                result["errors"].append(f"{key}: {type(exc).__name__}")
        result[key] = frame
    return result

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def news(symbol):
    try:
        return yf.Ticker(symbol).news or []
    except Exception:
        return []

@st.cache_data(ttl=21600, show_spinner=False)
def exchange_symbols():
    """Download public exchange symbol directories; exclude funds, test issues and non-common securities."""
    frames = []
    urls = [
        ("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt", "|"),
        ("https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt", "|")
    ]
    for url, sep in urls:
        try:
            frame = pd.read_csv(url, sep=sep, dtype=str, on_bad_lines="skip")
            frames.append(frame)
        except Exception:
            continue
    if not frames: return []
    symbols = []
    for f in frames:
        symbol_col = "Symbol" if "Symbol" in f.columns else "ACT Symbol" if "ACT Symbol" in f.columns else None
        if not symbol_col: continue
        for _, row in f.iterrows():
            s = str(row.get(symbol_col, "")).strip()
            name = str(row.get("Security Name", "")).lower()
            etf = str(row.get("ETF", "N")).upper()
            test = str(row.get("Test Issue", "N")).upper()
            if not s or s.lower() == "nan" or etf == "y" or test == "y": continue
            if any(x in name for x in ["warrant", "right", "unit", "preferred", "depositary share", "notes due", " debenture"]): continue
            if not re.fullmatch(r"[A-Z][A-Z0-9.\\-]{0,6}", s): continue
            symbols.append(s.replace("-", "."))
    return sorted(set(symbols))

@st.cache_data(ttl=900, show_spinner=False)
def yahoo_screen_symbols(screen_name, count=100):
    try:
        result = yf.screen(screen_name, count=min(max(int(count), 1), 250))
        quotes = result.get("quotes", []) if isinstance(result, dict) else []
        return [q.get("symbol") for q in quotes if q.get("symbol")]
    except Exception:
        return []

def discover_universe(count=60):
    """Dynamic candidate pool: current Yahoo screener results plus a rotating exchange-directory sample."""
    count = min(max(int(count), 20), 150)
    gathered = []
    per_screen = max(20, min(100, count))
    for name in SCREENER_NAMES:
        gathered.extend(yahoo_screen_symbols(name, per_screen))
    screen_unique = list(dict.fromkeys(s for s in gathered if isinstance(s, str) and s and "^" not in s))
    directory = exchange_symbols()
    directory_sample = []
    if directory:
        day = dt.datetime.now(dt.timezone.utc).timetuple().tm_yday
        start = (day * count) % len(directory)
        rotated = directory[start:] + directory[:start]
        directory_sample = rotated[:max(30, count * 2)]
    mixed = []
    a, b = screen_unique[:count * 2], directory_sample
    for idx in range(max(len(a), len(b))):
        if idx < len(a): mixed.append(a[idx])
        if idx < len(b): mixed.append(b[idx])
    unique = list(dict.fromkeys(mixed))
    return unique[:max(count * 3, count)], {"screeners": len(set(gathered)), "directory_count": len(directory), "rotating_directory_sample": len(directory_sample), "candidate_pool": min(len(unique), max(count*3,count))}

def sector_etf_history(symbol):
    return history(symbol, "6mo")
