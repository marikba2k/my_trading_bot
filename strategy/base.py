# strategy/base.py
from __future__ import annotations
from typing import Literal, Dict, Any
import pandas as pd

Signal = Literal["LONG", "SHORT", "FLAT"]

class Strategy:
    def warmup(self) -> int:
        """
        How many candles does this strategy need before it can output a signal?
        Example: SMA(50) needs at least 50 bars.
        """
        return 50

    def generate_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Given a DataFrame with at least warmup() rows, return:
        {
          "signal": "LONG" | "SHORT" | "FLAT",
          "reason": "...",
          "meta": {...}   # anything useful (e.g., prices, indicators)
        }
        """
        raise NotImplementedError
