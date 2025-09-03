# paper/runner.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal, Dict, List
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from data.market_data import fetch_ohlcv, add_atr
from strategy.base import Strategy
from risk.manager import position_size, propose_levels

Mode = Literal["replay", "live"]

@dataclass
class PaperConfig:
    symbol: str = "BTCUSDT"
    interval: str = "15"          # Bybit v5: "1","3","5","15","30","60",...
    category: str = "linear"      # USDT perps
    initial_equity: float = 2000.0
    risk_pct: float = 0.01         # 1% per trade
    atr_mult_sl: float = 1.0
    atr_mult_tp: float = 2.0
    fee_bps: float = 2.0          # 0.02% per side
    slippage_bps: float = 1.0     # 0.01% per side
    report_path: Path = Path("reports/paper_trades.csv")

def _bps(price: float, bps: float) -> float:
    return price * (bps / 10_000.0)

def _ensure_report_header(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        pd.DataFrame(columns=[
            "time","symbol","side","entry_px","exit_px","qty","reason",
            "pnl","equity_after","bar_interval","mode"
        ]).to_csv(path, index=False)

class PaperRunner:
    def __init__(self, strategy: Strategy, cfg: PaperConfig):
        self.strat = strategy
        self.cfg = cfg
        self.equity = cfg.initial_equity
        self.in_pos = False
        self.pos_side = None   # "LONG" | "SHORT"
        self.entry_px = None
        self.qty = 0.0
        self.sl_px = None
        self.tp_px = None
        self.entry_time = None

        _ensure_report_header(cfg.report_path)

    # ======== core simulation helpers ========

    def _maybe_exit_on_bar(self, bar) -> Optional[Dict]:
        """Check SL/TP intrabar; return trade dict if we exit."""
        if not self.in_pos:
            return None

        high = float(bar.high)
        low = float(bar.low)
        ts = bar.Index

        exit_reason = None
        exit_px = None

        if self.pos_side == "LONG":
            hit_sl = (low <= self.sl_px)
            hit_tp = (high >= self.tp_px)
            if hit_sl and hit_tp:
                exit_reason, exit_px = "SL", self.sl_px
            elif hit_sl:
                exit_reason, exit_px = "SL", self.sl_px
            elif hit_tp:
                exit_reason, exit_px = "TP", self.tp_px
        else:  # SHORT
            hit_sl = (high >= self.sl_px)
            hit_tp = (low <= self.tp_px)
            if hit_sl and hit_tp:
                exit_reason, exit_px = "SL", self.sl_px
            elif hit_sl:
                exit_reason, exit_px = "SL", self.sl_px
            elif hit_tp:
                exit_reason, exit_px = "TP", self.tp_px

        if not exit_reason:
            return None

        # costs
        slip = _bps(exit_px, self.cfg.slippage_bps)
        fee = _bps(exit_px, self.cfg.fee_bps)
        if self.pos_side == "LONG":
            pnl_per = (exit_px - self.entry_px) - fee - slip
        else:
            pnl_per = (self.entry_px - exit_px) - fee - slip

        trade_pnl = pnl_per * self.qty
        self.equity += trade_pnl

        trade = {
            "time": ts.isoformat(),
            "symbol": self.cfg.symbol,
            "side": self.pos_side,
            "entry_px": self.entry_px,
            "exit_px": exit_px,
            "qty": self.qty,
            "reason": exit_reason,
            "pnl": trade_pnl,
            "equity_after": self.equity,
            "bar_interval": self.cfg.interval,
        }

        # flat after exit
        self.in_pos = False
        self.pos_side = None
        self.entry_px = None
        self.qty = 0.0
        self.sl_px = None
        self.tp_px = None
        self.entry_time = None

        return trade

    def _enter_next_open(self, next_bar_open: float, atr: float, signal: str, next_ts) -> None:
        """Open a virtual position at next bar open with fees/slippage."""
        side = "LONG" if signal == "LONG" else "SHORT"
        lvls = propose_levels(next_bar_open, atr, self.cfg.atr_mult_sl, self.cfg.atr_mult_tp,
                              side=("Buy" if side == "LONG" else "Sell"))
        sl = lvls["sl"]
        tp = lvls["tp"]
        stop_distance = abs(next_bar_open - sl)
        if stop_distance <= 0:
            return

        q = position_size(self.equity, self.cfg.risk_pct, stop_distance)

        fee = _bps(next_bar_open, self.cfg.fee_bps)
        slip = _bps(next_bar_open, self.cfg.slippage_bps)
        entry_px = next_bar_open + slip + fee if side == "LONG" else next_bar_open - slip - fee

        self.in_pos = True
        self.pos_side = side
        self.entry_px = entry_px
        self.qty = q
        self.sl_px = sl
        self.tp_px = tp
        self.entry_time = next_ts

    def _append_trade(self, t: Dict, mode: str):
        t = dict(t)
        t["mode"] = mode
        df = pd.DataFrame([t])
        df.to_csv(self.cfg.report_path, mode="a", header=False, index=False)

    # ======== modes ========

    def run_replay(self, lookback_bars: int = 500):
        """Fast replay of the last N bars (bar-by-bar)."""
        df = fetch_ohlcv(self.cfg.symbol, self.cfg.interval, lookback_bars, self.cfg.category)
        # ATR column for convenience
        df["atr14"] = add_atr(df, 14)

        rows = list(df.itertuples())
        start = max(self.strat.warmup(), 2)

        for i in range(start, len(rows) - 1):
            cur = rows[i]
            nxt = rows[i + 1]
            df_slice = df.iloc[: i + 1]

            # 1) exit check on current bar
            maybe = self._maybe_exit_on_bar(cur)
            if maybe:
                self._append_trade(maybe, mode="replay")

            # 2) entry decision for next bar
            if not self.in_pos:
                sig = self.strat.generate_signal(df_slice)
                if sig["signal"] in ("LONG", "SHORT"):
                    atr = float(sig.get("meta", {}).get("atr14", 0.0)) or float(df_slice["close"].iloc[-1] * 0.005)
                    self._enter_next_open(next_bar_open=float(nxt.open), atr=atr, signal=sig["signal"], next_ts=nxt.Index)

        # final close-out: if still in position, close at last close (optional)
        if self.in_pos:
            last = rows[-1]
            last_close = float(last.close)
            fee = _bps(last_close, self.cfg.fee_bps)
            slip = _bps(last_close, self.cfg.slippage_bps)
            exit_px = last_close - fee - slip if self.pos_side == "LONG" else last_close + fee + slip
            pnl_per = (exit_px - self.entry_px) if self.pos_side == "LONG" else (self.entry_px - exit_px)
            self.equity += pnl_per * self.qty
            self._append_trade({
                "time": last.Index.isoformat(),
                "symbol": self.cfg.symbol,
                "side": self.pos_side,
                "entry_px": self.entry_px,
                "exit_px": exit_px,
                "qty": self.qty,
                "reason": "manual_close",
                "pnl": pnl_per * self.qty,
                "equity_after": self.equity,
                "bar_interval": self.cfg.interval,
            }, mode="replay")
            self.in_pos = False

    def run_live(self, poll_seconds: int = 5):
        """
        Waits for new bars to CLOSE.
        For a 15m interval, we only act when a fresh completed candle appears.
        """
        last_seen_ts = None
        while True:
            try:
                df = fetch_ohlcv(self.cfg.symbol, self.cfg.interval, 300, self.cfg.category)
                df["atr14"] = add_atr(df, 14)
                cur = df.iloc[-1]           # last closed bar
                prev = df.iloc[-2]          # previous bar
                ts = cur.name               # datetime index

                if last_seen_ts is None:
                    last_seen_ts = ts  # initialize
                elif ts == last_seen_ts:
                    # no new closed candle yet
                    time.sleep(poll_seconds)
                    continue

                # NEW bar arrived → process the previous closed bar (`prev`) for exits,
                # and the new bar open for entries.
                # Convert prev to a namedtuple-like for reuse
                prev_row = df.iloc[-2: -1].itertuples().__next__()
                cur_row = df.iloc[-1:].itertuples().__next__()  # used for next open
                df_slice = df.iloc[:-0]  # full df up to current last

                # 1) exit on prev bar (closed)
                maybe = self._maybe_exit_on_bar(prev_row)
                if maybe:
                    self._append_trade(maybe, mode="live")

                # 2) entry on new bar open
                if not self.in_pos:
                    sig = self.strat.generate_signal(df_slice)
                    if sig["signal"] in ("LONG", "SHORT"):
                        atr = float(sig.get("meta", {}).get("atr14", 0.0)) or float(df_slice["close"].iloc[-1] * 0.005)
                        next_open = float(cur_row.open)  # open of the newest bar
                        self._enter_next_open(next_open, atr, sig["signal"], cur_row.Index)

                last_seen_ts = ts
                # small heartbeat print (optional)
                print(f"[{datetime.now(timezone.utc).isoformat()}] Live tick @ {ts} | equity={self.equity:.2f} | in_pos={self.in_pos}")

                time.sleep(poll_seconds)

            except KeyboardInterrupt:
                print("Stopping live runner...")
                break
            except Exception as e:
                print("Error in live loop:", e)
                time.sleep(3)
