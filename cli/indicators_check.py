# cli/indicators_check.py
from pathlib import Path
from data.market_data import fetch_ohlcv, add_basic_indicators

def main():
    symbol = "BTCUSDT"
    interval = "15"     # 15-minute candles
    limit = 300         # enough to compute SMA/RSI/ATR

    df = fetch_ohlcv(symbol, interval=interval, limit=limit)
    df = add_basic_indicators(df)

    print("Columns:", list(df.columns))
    print(df.tail(5))  # show the last 5 rows with indicators

    Path("reports").mkdir(exist_ok=True)
    out = Path(f"reports/{symbol}_{interval}m_with_indicators.csv")
    df.to_csv(out)
    print("Saved:", out)

if __name__ == "__main__":
    main()
