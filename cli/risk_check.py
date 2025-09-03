# cli/risk_check.py
from risk.manager import position_size, propose_levels

def main():
    equity = 2000          # USDT in account
    risk_pct = 0.01        # risk 1% per trade
    entry_price = 50000.0  # pretend entry price
    atr = 200.0            # pretend ATR (volatility)

    # Stop distance: e.g., 1 ATR = 200
    stop_distance = atr

    qty = position_size(equity, risk_pct, stop_distance)
    print(f"Position size: {qty} contracts")

    levels = propose_levels(entry_price, atr, atr_mult_sl=1.0, atr_mult_tp=2.0, side="Buy")
    print("Proposed SL/TP:", levels)

if __name__ == "__main__":
    main()
