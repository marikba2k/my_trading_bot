# cli/live.py
import argparse
from exec.live_runner import LiveRunner, LiveConfig
from strategy.sma_cross import SmaCross

def main():
    ap = argparse.ArgumentParser(description="Live trading runner (TESTNET)")
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--tf", default="15", help="Bybit interval string: 1,3,5,15,30,60,240,D")
    ap.add_argument("--risk", type=float, default=0.01, help="Risk % per trade (e.g., 0.01 for 1%)")
    ap.add_argument("--slatr", type=float, default=1.0, help="Stop at N x ATR")
    ap.add_argument("--tpatr", type=float, default=2.0, help="Take-profit at N x ATR")
    ap.add_argument("--equity", type=float, default=2000.0, help="Sizing equity hint (USDT)")
    args = ap.parse_args()

    strat = SmaCross(fast=20, slow=50)
    cfg = LiveConfig(
        symbol=args.symbol,
        interval=args.tf,
        risk_pct=args.risk,
        atr_mult_sl=args.slatr,
        atr_mult_tp=args.tpatr,
        equity_hint=args.equity,
    )
    runner = LiveRunner(strategy=strat, cfg=cfg)
    runner.run()

if __name__ == "__main__":
    main()
