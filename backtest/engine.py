# backtest/engine.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
import math
import pandas as pd

from strategy.base import Strategy
from risk.manager import position_size, propose_levels

@dataclass
class BTConfig:
    initial_equity: float = 2000.0
    risk_pct: float = 0.01          # 1% risk per trade
    atr_mult_sl: float = 1.0
    atr_mult_tp: float = 2.0
    fee_bps: float = 2.0            # 0.02% per side (maker-ish)
    slippage_bps: float = 1.0       # 0.01% per side
    side_one_at_a_time: bool = True

def _bps(price: float, bps: float) -> float:
    return price * (bps / 10_000.0)

def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    cfg: Optional[BTConfig] = None,
) -> Dict:
    """
    df must have columns: open, high, low, close, volume (datetime index, oldest->newest)
    strategy.generate_signal(df_slice) returns meta with 'atr14' ideally.
    """
    cfg = cfg or BTConfig()

    equity = cfg.initial_equity
    equity_curve = []  # list of (timestamp, equity)
    trades: List[Dict] = []

    in_pos = False
    pos_side = None     # "LONG" | "SHORT"
    entry_px = None
    qty = 0.0
    sl_px = None
    tp_px = None

    rows = list(df.itertuples())  # faster iteration
    # Start from warmup so indicators are ready
    start_idx = max(strategy.warmup(), 2)
    for i in range(start_idx, len(rows) - 1):
        # we will ENTER at next bar open if signal occurs on bar i (rows[i])
        # use a slice up to current bar (inclusive) for the strategy
        df_slice = df.iloc[: i + 1]
        sig = strategy.generate_signal(df_slice)
        cur = rows[i]
        nxt = rows[i + 1]  # next bar (where entries happen)
        ts = cur.Index

        # Mark equity (stair-step equity curve: only on closes/exits)
        equity_curve.append((ts, equity))

        # If in position, check SL/TP intrabar on current bar
        if in_pos:
            high = cur.high
            low = cur.low

            # Did we hit SL or TP within the bar?
            exit_reason = None
            exit_px = None

            if pos_side == "LONG":
                hit_sl = (low <= sl_px)
                hit_tp = (high >= tp_px)
                # assume worst/best: if both, SL/TP order priority? use SL first conservatively
                if hit_sl and hit_tp:
                    # conservative: assume SL first
                    exit_reason = "SL"
                    exit_px = sl_px
                elif hit_sl:
                    exit_reason = "SL"
                    exit_px = sl_px
                elif hit_tp:
                    exit_reason = "TP"
                    exit_px = tp_px
            else:  # SHORT
                hit_sl = (high >= sl_px)
                hit_tp = (low <= tp_px)
                if hit_sl and hit_tp:
                    exit_reason = "SL"
                    exit_px = sl_px
                elif hit_sl:
                    exit_reason = "SL"
                    exit_px = sl_px
                elif hit_tp:
                    exit_reason = "TP"
                    exit_px = tp_px

            if exit_reason:
                # fees + slippage on exit
                slip = _bps(exit_px, cfg.slippage_bps)
                fee = _bps(exit_px, cfg.fee_bps)
                if pos_side == "LONG":
                    pnl_per_unit = (exit_px - entry_px) - fee - slip
                else:
                    pnl_per_unit = (entry_px - exit_px) - fee - slip
                trade_pnl = pnl_per_unit * qty

                equity += trade_pnl
                trades.append({
                    "entry_time": entry_time,
                    "exit_time": ts,
                    "side": pos_side,
                    "entry_px": entry_px,
                    "exit_px": exit_px,
                    "qty": qty,
                    "reason": exit_reason,
                    "pnl": trade_pnl,
                    "equity_after": equity,
                })
                # flat
                in_pos = False
                pos_side = None
                entry_px = None
                sl_px = None
                tp_px = None
                qty = 0.0

        # If flat, consider entering on next bar open based on today's signal
        if not in_pos:
            if sig["signal"] in ("LONG", "SHORT"):
                # Need ATR for stop distance; fallback to simple fraction if missing
                atr = float(sig.get("meta", {}).get("atr14", 0.0)) or float(df_slice["close"].iloc[-1] * 0.005)
                # Entry on next bar open
                e_px = nxt.open
                # Propose SL/TP
                lvls = propose_levels(e_px, atr, cfg.atr_mult_sl, cfg.atr_mult_tp,
                                      side=("Buy" if sig["signal"] == "LONG" else "Sell"))
                sl = lvls["sl"]
                tp = lvls["tp"]
                stop_distance = abs(e_px - sl)
                if stop_distance <= 0:
                    continue

                # Position size from risk
                q = position_size(equity, cfg.risk_pct, stop_distance)

                # fees + slippage on entry (we "pay" them immediately in price terms)
                fee = _bps(e_px, cfg.fee_bps)
                slip = _bps(e_px, cfg.slippage_bps)

                # Open position
                in_pos = True
                pos_side = "LONG" if sig["signal"] == "LONG" else "SHORT"
                entry_px = e_px + slip + fee if pos_side == "LONG" else e_px - slip - fee
                sl_px = sl
                tp_px = tp
                qty = q
                entry_time = rows[i + 1].Index

    # append final equity point
    equity_curve.append((rows[-1].Index, equity))
    eq_series = pd.Series({t: v for t, v in equity_curve}).sort_index()
    return {"trades": trades, "equity_curve": eq_series, "final_equity": equity}
