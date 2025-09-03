# orders/executor.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal

from exchange.bybit_client import BybitClient
from risk.manager import position_size, propose_levels

Side = Literal["Buy", "Sell"]

@dataclass
class BracketConfig:
    risk_pct: float = 0.01     # e.g., 1% of equity per trade
    atr_mult_sl: float = 1.0   # SL at 1 x ATR
    atr_mult_tp: float = 2.0   # TP at 2 x ATR
    category: str = "linear"

class OrderExecutor:
    """
    A thin, safe wrapper to:
    - compute order size from risk
    - round qty/price to exchange rules
    - place a single entry with TP/SL attached (tpslMode=Full)
    """
    def __init__(self, client: Optional[BybitClient] = None):
        self.client = client or BybitClient()

    # ---- Rounding helpers from the client ----
    def _qty_round(self, qty: float, symbol: str) -> float:
        min_qty, step = self.client.get_min_qty(symbol, self.client.cfg.runtime_mode == "live" and "linear" or "linear")
        if step in (None, 0,):
            return qty
        # snap down to a valid step so we never go under min due to rounding
        snapped = int(qty / step) * step
        # ensure we don't fall below min
        if snapped < min_qty:
            snapped = min_qty
        return round(snapped, 12)

    def _price_round(self, px: float, symbol: str) -> float:
        tick = self.client.get_tick_size(symbol)
        if not tick or tick <= 0:
            return px
        snapped = round(round(px / tick) * tick, 12)
        return snapped

    # ---- Build a single entry order with attached TP/SL ----
    def build_bracket(
        self,
        symbol: str,
        side: Side,
        entry_px: float,
        atr: float,
        equity: float,
        cfg: BracketConfig,
    ) -> dict:
        """
        1) Compute SL/TP by ATR multipliers
        2) Compute stop_distance (abs diff entry vs SL)
        3) Compute qty from risk_pct
        4) Round qty/price to exchange steps
        5) Return a ready-to-send order dict (Limit by default)
        """
        # 1) SL/TP proposal
        lvls = propose_levels(entry_px, atr, cfg.atr_mult_sl, cfg.atr_mult_tp, side=side)
        sl_px = self._price_round(lvls["sl"], symbol)
        tp_px = self._price_round(lvls["tp"], symbol)

        # 2) Stop distance
        stop_distance = abs(entry_px - sl_px)
        if stop_distance <= 0:
            raise ValueError("Stop distance is zero or negative; check ATR and multipliers.")

        # 3) Quantity from risk
        qty = position_size(equity, cfg.risk_pct, stop_distance)
        qty = self._qty_round(qty, symbol)

        # 4) Round entry price
        entry_px = self._price_round(entry_px, symbol)

        # 5) Build order payload for Bybit
        #    Use tpslMode="Full" to apply TP/SL to the whole position size.
        order = {
            "category": cfg.category,
            "symbol": symbol,
            "side": side,
            "order_type": "Limit",
            "price": entry_px,
            "qty": qty,
            "timeInForce": "PostOnly",     # safer: won’t cross the book accidentally
            "tpslMode": "Full",
            "takeProfit": tp_px,
            "stopLoss": sl_px,
            # You can also add reduceOnly=False, closeOnTrigger=False if needed
        }
        return order

    # ---- Submit / Amend / Cancel / Status ----
    def submit(self, order: dict) -> dict:
        return self.client.place_order(
            symbol=order["symbol"],
            side=order["side"],
            qty=order["qty"],
            order_type=order["order_type"],
            price=order.get("price"),
            category=order.get("category", "linear"),
            timeInForce=order.get("timeInForce"),
            tpslMode=order.get("tpslMode"),
            takeProfit=order.get("takeProfit"),
            stopLoss=order.get("stopLoss"),
        )

    def amend(self, symbol: str, order_id: str, **fields) -> dict:
        # Bybit uses 'amend_order' with flexible fields; in pybit it's place_order/cancel/amend depending on version.
        # If your pybit has amend support exposed, call it here; otherwise cancel & re-place.
        # For now, we keep a simple placeholder:
        # (You can implement self.client.session.amend_order(...) if your SDK exposes it)
        return {"note": "Implement amend via SDK if available", "requested_fields": fields}

    def cancel(self, symbol: str, order_id: str, category: str = "linear") -> dict:
        return self.client.cancel_order(symbol, order_id=order_id, category=category)
