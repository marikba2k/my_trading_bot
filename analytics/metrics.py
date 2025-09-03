# analytics/metrics.py
from __future__ import annotations
import math
import pandas as pd

def summary_stats(trades: list[dict], equity_curve: pd.Series) -> dict:
    if not trades:
        return {"trades": 0, "final_equity": float(equity_curve.iloc[-1]), "winrate": 0.0, "pf": 0.0,
                "max_dd": 0.0, "sharpe": 0.0}

    wins = [t["pnl"] for t in trades if t["pnl"] > 0]
    losses = [abs(t["pnl"]) for t in trades if t["pnl"] < 0]
    winrate = (len(wins) / len(trades)) * 100.0 if trades else 0.0
    pf = (sum(wins) / sum(losses)) if losses else math.inf

    # Max Drawdown on equity_curve
    peak = -1e18
    dd = 0.0
    for v in equity_curve:
        peak = max(peak, v)
        dd = max(dd, (peak - v))
    max_dd = dd

    # Simple Sharpe: returns from step differences (not annualized precisely)
    rets = equity_curve.pct_change().dropna()
    sharpe = (rets.mean() / (rets.std() + 1e-12)) * math.sqrt(252) if len(rets) > 3 else 0.0

    return {
        "trades": len(trades),
        "final_equity": float(equity_curve.iloc[-1]),
        "winrate": winrate,
        "pf": float(pf),
        "max_dd": float(max_dd),
        "sharpe": float(sharpe),
        "avg_win": float(sum(wins)/len(wins)) if wins else 0.0,
        "avg_loss": float(sum(losses)/len(losses)) if losses else 0.0,
    }
