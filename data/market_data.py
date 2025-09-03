# data/market_data.py
from __future__ import annotations
from typing import List, Dict
import math
import pandas as pd

from exchange.bybit_client import BybitClient

# ---------- Helpers to parse Bybit kline ----------
# Bybit v5 returns klines as list of strings like:
# [
#   startTime, open, high, low, close, volume, turnover, ...
# ]
# We only use the first 6 fields.

COLUMNS = ["ts", "open", "high", "low", "close", "volume"]

def _to_float(x):
    try:
        return float(x)
    except Exception:
        return math.nan

def normalize_kline_row(row: List[str]) -> Dict:
    return {
        "ts": int(row[0]),                 # milliseconds since epoch
        "open": _to_float(row[1]),
        "high": _to_float(row[2]),
        "low": _to_float(row[3]),
        "close": _to_float(row[4]),
        "volume": _to_float(row[5]),
    }

# ---------- Fetch & shape ----------
def fetch_ohlcv(symbol: str, interval: str = "15", limit: int = 500, category: str = "linear") -> pd.DataFrame:
    """
    Returns a DataFrame with index=datetime (UTC), columns: open, high, low, close, volume
    """
    client = BybitClient()
    resp = client.get_klines(symbol, interval=interval, limit=limit, category=category)
    rows = resp.get("result", {}).get("list", []) or []

    if not rows:
        raise RuntimeError(f"No klines returned for {symbol} {interval}")

    # Bybit returns newest-first; sort to oldest-first
    rows = list(reversed(rows))

    norm = [normalize_kline_row(r) for r in rows]
    df = pd.DataFrame(norm, columns=COLUMNS)

    # Set datetime index
    df["datetime"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("datetime")[["open", "high", "low", "close", "volume"]]

    # Ensure numeric
    df = df.apply(pd.to_numeric, errors="coerce")

    # Drop rows with NaNs at the end if any
    df = df.dropna().copy()
    return df

# ---------- Indicators ----------
def add_sma(df: pd.DataFrame, period: int, col: str = "close") -> pd.Series:
    return df[col].rolling(period, min_periods=period).mean()

def add_ema(df: pd.DataFrame, period: int, col: str = "close") -> pd.Series:
    return df[col].ewm(span=period, adjust=False, min_periods=period).mean()

def add_rsi(df: pd.DataFrame, period: int = 14, col: str = "close") -> pd.Series:
    # Classic Wilder's RSI
    delta = df[col].diff()
    gain = (delta.clip(lower=0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, math.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def add_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    # True Range = max(high-low, abs(high-prevClose), abs(low-prevClose))
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        (df["high"] - df["low"]).abs(),
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr

def add_basic_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["sma20"] = add_sma(out, 20)
    out["sma50"] = add_sma(out, 50)
    out["ema20"] = add_ema(out, 20)
    out["rsi14"] = add_rsi(out, 14)
    out["atr14"] = add_atr(out, 14)
    return out
