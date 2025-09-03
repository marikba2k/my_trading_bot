# cli/paper.py
import argparse
from paper.runner import PaperRunner, PaperConfig
from strategy.sma_cross import SmaCross

def parse_hours_to_bars(hours: int, tf_minutes: int) -> int:
    bars = max(100, int((hours * 60) / tf_minutes))  # at least 100 bars for warmup
    return bars

def main():
    ap = argparse.ArgumentParser(description="Paper trading (replay or live)")
    ap.add_argument("--mode", choices=["replay","live"], required=True)
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--tf", default="15", help="Bybit interval minutes: 1,3,5,15,30,60,240, ... as string")
    ap.add_argument("--lookback", default="72h", help="Replay lookback, e.g. 24h, 72h, 7d")
    ap.add_argument("--risk", type=float, default=0.01, help="Risk % per trade, e.g. 0.01 for 1%")
    args = ap.parse_args()

    # Strategy (you can swap later)
    strat = SmaCross(fast=20, slow=50)

    cfg = PaperConfig(
        symbol=args.symbol,
        interval=args.tf,
        risk_pct=args.risk,
    )
    runner = PaperRunner(strategy=strat, cfg=cfg)

    if args.mode == "replay":
        # convert lookback to bars
        look = args.lookback.lower()
        if look.endswith("h"):
            hours = int(look[:-1])
        elif look.endswith("d"):
            hours = int(look[:-1]) * 24
        else:
            hours = int(look)  # assume hours
        tf_minutes = int(args.tf)
        bars = parse_hours_to_bars(hours, tf_minutes)
        print(f"Replaying last ~{hours}h → {bars} bars for {args.symbol} {args.tf}m")
        runner.run_replay(lookback_bars=bars)
        print("Replay finished. See reports/paper_trades.csv")
    else:
        print(f"Starting LIVE paper mode on {args.symbol} {args.tf}m (Ctrl+C to stop)")
        runner.run_live()

if __name__ == "__main__":
    main()
