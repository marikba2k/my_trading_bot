# risk/manager.py
from dataclasses import dataclass

@dataclass
class RiskConfig:
    equity: float          # account equity in USDT
    risk_pct: float        # % of equity to risk per trade (e.g. 0.01 for 1%)
    atr_mult_sl: float     # how many ATRs below/above entry for stop
    atr_mult_tp: float     # how many ATRs for take profit

def position_size(equity: float, risk_pct: float, stop_distance: float, contract_value: float = 1.0) -> float:
    """
    Compute how many contracts to buy/sell.
    equity: total account size (e.g., 2000 USDT)
    risk_pct: risk per trade (e.g., 0.01 for 1%)
    stop_distance: difference between entry and stop (in price terms)
    contract_value: size per contract (usually 1 for USDT per unit)
    """
    risk_amount = equity * risk_pct
    if stop_distance <= 0:
        raise ValueError("Stop distance must be > 0")
    qty = risk_amount / (stop_distance * contract_value)
    return round(qty, 6)  # round for exchange safety

def propose_levels(entry: float, atr: float, atr_mult_sl: float, atr_mult_tp: float, side: str = "Buy") -> dict:
    """
    Propose SL and TP based on entry, ATR, and multipliers.
    """
    if side == "Buy":
        sl = entry - atr * atr_mult_sl
        tp = entry + atr * atr_mult_tp
    else:  # Sell
        sl = entry + atr * atr_mult_sl
        tp = entry - atr * atr_mult_tp
    return {"sl": sl, "tp": tp}

def validate_order(qty: float, min_qty: float, max_leverage: float = 10) -> None:
    """
    Basic safety checks before placing an order.
    """
    if qty < min_qty:
        raise ValueError(f"Order qty {qty} is below minimum {min_qty}")
    if qty <= 0:
        raise ValueError("Quantity must be > 0")
    # You could add leverage/margin checks here
