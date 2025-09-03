# strategy/sma_cross.py
from __future__ import annotations
from typing import Dict, Any
import pandas as pd

from strategy.base import Strategy, Signal
from data.market_data import add_sma, add_atr

class SmaCross(Strategy):
    def __init__(self, fast: int = 20, slow: int = 50):
        assert fast < slow, "fast MA must be smaller than slow MA"
        self.fast = fast
        self.slow = slow

    def warmup(self) -> int:
        # need enough bars to compute slow SMA and ATR
        return max(self.slow, 14) + 2

    def generate_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < self.warmup():
            return {"signal": "FLAT", "reason": "not_enough_data", "meta": {}}

        work = df.copy()
        work[f"sma{self.fast}"] = add_sma(work, self.fast)
        work[f"sma{self.slow}"] = add_sma(work, self.slow)
        work["atr14"] = add_atr(work, 14)

        last = work.iloc[-1]
        prev = work.iloc[-2]

        fast_now = last[f"sma{self.fast}"]
        slow_now = last[f"sma{self.slow}"]
        fast_prev = prev[f"sma{self.fast}"]
        slow_prev = prev[f"sma{self.slow}"]

        # Guard against NaNs during warmup
        if pd.isna(fast_now) or pd.isna(slow_now) or pd.isna(fast_prev) or pd.isna(slow_prev):
            return {"signal": "FLAT", "reason": "sma_warming_up", "meta": {}}

        # Cross up: yesterday fast <= slow, today fast > slow -> LONG
        if fast_prev <= slow_prev and fast_now > slow_now:
            return {
                "signal": "LONG",
                "reason": "bull_cross",
                "meta": {
                    "price": float(last["close"]),
                    "fast": float(fast_now),
                    "slow": float(slow_now),
                    "atr14": float(last["atr14"]),
                },
            }

        # Cross down: yesterday fast >= slow, today fast < slow -> SHORT
        if fast_prev >= slow_prev and fast_now < slow_now:
            return {
                "signal": "SHORT",
                "reason": "bear_cross",
                "meta": {
                    "price": float(last["close"]),
                    "fast": float(fast_now),
                    "slow": float(slow_now),
                    "atr14": float(last["atr14"]),
                },
            }

        return {
            "signal": "FLAT",
            "reason": "no_cross",
            "meta": {
                "price": float(last["close"]),
                "fast": float(fast_now),
                "slow": float(slow_now),
                "atr14": float(last["atr14"]),
            },
        }
