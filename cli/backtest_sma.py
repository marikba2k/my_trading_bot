# cli/backtest_sma.py
from pathlib import Path
import pandas as pd
from data.market_data import fetch_ohlcv
from strategy.sma_cross import SmaCross
from backtest.engine import run_backtest, BTConfig
from analytics.metrics import summary_stats

def main():
    symbol = "BTCUSDT"
    interval = "15"
    limit = 2000  # ~enough for many months

    print(f"Fetching {symbol} {interval}m candles...")
    df = fetch_ohlcv(symbol, interval=interval, limit=limit)

    strat = SmaCross(fast=20, slow=50)
    cfg = BTConfig(
        initial_equity=2000.0,
        risk_pct=0.01,
        atr_mult_sl=1.0,
        atr_mult_tp=2.0,
        fee_bps=2.0,
        slippage_bps=1.0,
    )

    print("Running backtest...")
    result = run_backtest(df, strat, cfg)
    trades = result["trades"]
    eq = result["equity_curve"]

    stats = summary_stats(trades, eq)
    print("\n=== Summary ===")
    for k, v in stats.items():
        print(f"{k}: {v}")

    # Save outputs
    Path("reports").mkdir(exist_ok=True)
    trades_path = Path(f"reports/{symbol}_{interval}m_sma_trades.csv")
    eq_path = Path(f"reports/{symbol}_{interval}m_sma_equity.csv")
    pd.DataFrame(trades).to_csv(trades_path, index=False)
    eq.to_csv(eq_path, header=["equity"])
    print(f"\nSaved: {trades_path}")
    print(f"Saved: {eq_path}")

if __name__ == "__main__":
    main()
