# cli/strategy_check.py
from data.market_data import fetch_ohlcv
from strategy.sma_cross import SmaCross

def main():
    symbol = "BTCUSDT"
    tf = "15"
    df = fetch_ohlcv(symbol, interval=tf, limit=300)  # enough data for SMA50 + ATR
    strat = SmaCross(fast=20, slow=50)
    sig = strat.generate_signal(df)
    print(f"Strategy: SMA({strat.fast},{strat.slow}) on {symbol} {tf}m")
    print("Signal:", sig["signal"])
    print("Reason:", sig["reason"])
    print("Meta:", sig["meta"])

if __name__ == "__main__":
    main()
