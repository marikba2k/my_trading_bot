# exec/live_runner.py
from __future__ import annotations
import time
import signal
from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any

from data.market_data import fetch_ohlcv, add_atr
from strategy.base import Strategy
from orders.executor import OrderExecutor, BracketConfig
from exchange.bybit_client import BybitClient
from core.logger import get_logger
from config.settings import load_env

Side = Literal["Buy", "Sell"]

@dataclass
class LiveConfig:
    symbol: str = "BTCUSDT"
    interval: str = "15"              # Bybit intervals as strings: "1","3","5","15","30","60","240","D","W"
    category: str = "linear"
    equity_hint: float = 2000.0       # used for sizing if you don't compute equity from balances yet
    risk_pct: float = 0.01
    atr_mult_sl: float = 1.0
    atr_mult_tp: float = 2.0
    poll_seconds: int = 5

class LiveRunner:
    def __init__(self, strategy: Strategy, cfg: LiveConfig):
        self.cfg = cfg
        self.strategy = strategy
        self.settings = load_env()
        self.log = get_logger("LiveRunner", self.settings.log_level)
        self.client = BybitClient()
        self.exec = OrderExecutor(self.client)
        self.bracket_cfg = BracketConfig(
            risk_pct=cfg.risk_pct,
            atr_mult_sl=cfg.atr_mult_sl,
            atr_mult_tp=cfg.atr_mult_tp,
            category=cfg.category,
        )

        self._stop = False
        signal.signal(signal.SIGINT, self._sig_stop)
        signal.signal(signal.SIGTERM, self._sig_stop)

        self._resting_order_id: Optional[str] = None  # entry order waiting to fill
        self._last_seen_bar_ts = None

    # ----- signal handling -----
    def _sig_stop(self, *args):
        self.log.warning("Stop signal received. Attempting graceful shutdown...")
        self._stop = True

    # ----- exchange state helpers -----
    def get_open_position(self) -> Dict[str, Any] | None:
        """Return a simplified open position for symbol, or None."""
        try:
            pos = self.client.get_positions(symbol=self.cfg.symbol, category=self.cfg.category)
            items = pos.get("result", {}).get("list", []) or []
            # Unified trading often returns multiple entries; pick the one with size > 0
            for it in items:
                sz = float(it.get("size", "0") or 0)
                if sz != 0:
                    side = "LONG" if it.get("side") == "Buy" else "SHORT"
                    entry_px = float(it.get("avgPrice", "0") or 0)
                    return {"size": sz, "side": side, "avg": entry_px}
            return None
        except Exception as e:
            self.log.error("get_open_position error: %s", e)
            return None

    def cancel_resting_entry(self):
        if not self._resting_order_id:
            return
        try:
            self.log.info("Cancelling resting entry order %s", self._resting_order_id)
            self.client.cancel_order(self.cfg.symbol, order_id=self._resting_order_id, category=self.cfg.category)
        except Exception as e:
            self.log.error("Cancel error: %s", e)
        finally:
            self._resting_order_id = None

    def close_position_market(self, pos: Dict[str, Any]):
        """Emergency/flip close using reduceOnly market order."""
        if not pos:
            return
        try:
            reduce_side: Side = "Sell" if pos["side"] == "LONG" else "Buy"
            qty = abs(float(pos["size"]))
            self.log.warning("Closing position %s %s @ market (reduceOnly)", pos["side"], qty)
            self.client.place_order(
                category=self.cfg.category,
                symbol=self.cfg.symbol,
                side=reduce_side,
                orderType="Market",
                qty=qty,
                reduceOnly=True,
                closeOnTrigger=False,
                timeInForce="IOC",
            )
        except Exception as e:
            self.log.error("Close market error: %s", e)

    # ----- main loop -----
    def run(self):
        self.log.info("Live runner starting (symbol=%s, tf=%sm, testnet=%s)",
                      self.cfg.symbol, self.cfg.interval, self.settings.testnet)

        while not self._stop:
            try:
                # 1) Pull recent candles; last row is the latest CLOSED bar
                df = fetch_ohlcv(self.cfg.symbol, self.cfg.interval, limit=300, category=self.cfg.category)
                df["atr14"] = add_atr(df, 14)
                last = df.iloc[-1]
                prev = df.iloc[-2]
                last_ts = last.name  # datetime index

                # Only act when a NEW bar has closed
                if self._last_seen_bar_ts is None:
                    self._last_seen_bar_ts = last_ts
                    self.log.info("Initialized on closed bar %s", last_ts)
                    time.sleep(self.cfg.poll_seconds)
                    continue
                if last_ts == self._last_seen_bar_ts:
                    # no new closed candle yet
                    time.sleep(self.cfg.poll_seconds)
                    continue

                # New bar closed -> process previous bar for exits/logic, and use current bar OPEN for new entries
                self._last_seen_bar_ts = last_ts

                # 2) Check exchange state
                pos = self.get_open_position()

                # 3) Generate a signal from strategy (using all data up to latest closed bar)
                sig = self.strategy.generate_signal(df)
                s = sig.get("signal", "FLAT")
                reason = sig.get("reason", "?")
                meta = sig.get("meta", {})
                atr = float(meta.get("atr14") or 0.0) or float(df["close"].iloc[-1] * 0.005)

                self.log.info("Signal %s (%s) | price=%.4f | atr=%.4f | in_pos=%s",
                              s, reason, float(last["close"]), atr, bool(pos))

                # 4) Handle cases
                if s == "FLAT":
                    # If we have a resting entry and strategy is FLAT, cancel it
                    if self._resting_order_id:
                        self.cancel_resting_entry()
                    # Do not force-close active positions here; let TP/SL manage them
                    time.sleep(self.cfg.poll_seconds)
                    continue

                # LONG or SHORT signal:
                desired_side: Side = "Buy" if s == "LONG" else "Sell"

                # 4a) If position exists and it's the SAME direction → do nothing (let TP/SL manage)
                if pos and ((pos["side"] == "LONG" and s == "LONG") or (pos["side"] == "SHORT" and s == "SHORT")):
                    self.log.info("Already in %s, keeping position.", pos["side"])
                    time.sleep(self.cfg.poll_seconds)
                    continue

                # 4b) If position exists in the OPPOSITE direction → close it then (optionally) re-enter
                if pos and ((pos["side"] == "LONG" and s == "SHORT") or (pos["side"] == "SHORT" and s == "LONG")):
                    self.log.warning("Flip detected: %s -> %s", pos["side"], s)
                    self.close_position_market(pos)
                    # clear any resting entry just in case
                    self.cancel_resting_entry()
                    # fall through to build a fresh entry after close

                # 4c) No position → build and place a new bracket entry off current bar OPEN
                # For safety, use PostOnly LIMIT a little away from market so we don't cross.
                open_px = float(last["open"])
                equity = self.cfg.equity_hint  # You can wire actual equity from balances later

                # Small nudge: if LONG, place slightly below open; if SHORT, slightly above
                entry_px = open_px * (0.998 if s == "LONG" else 1.002)

                order = self.exec.build_bracket(
                    symbol=self.cfg.symbol,
                    side=desired_side,
                    entry_px=entry_px,
                    atr=atr,
                    equity=equity,
                    cfg=self.bracket_cfg,
                )
                self.log.info("Placing bracket: %s", {k: order[k] for k in ("side", "price", "qty", "takeProfit", "stopLoss")})

                resp = self.exec.submit(order)
                self._resting_order_id = resp.get("result", {}).get("orderId")
                if self._resting_order_id:
                    self.log.info("Resting entry orderId=%s", self._resting_order_id)
                else:
                    self.log.warning("No orderId returned. Response: %s", str(resp)[:300])

                time.sleep(self.cfg.poll_seconds)

            except Exception as e:
                self.log.error("Live loop error: %s", e)
                time.sleep(3)

        # graceful shutdown: cancel any resting entry
        self.cancel_resting_entry()
        self.log.info("Live runner stopped.")
