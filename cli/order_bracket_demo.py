# cli/order_bracket_demo.py
from data.market_data import fetch_ohlcv, add_atr
from orders.executor import OrderExecutor, BracketConfig
from exchange.bybit_client import BybitClient

def main():
    symbol = "BTCUSDT"
    interval = "15"
    category = "linear"

    # 1) Get recent candles to compute ATR
    df = fetch_ohlcv(symbol, interval=interval, limit=100, category=category)
    atr_series = add_atr(df, period=14)
    atr = float(atr_series.dropna().iloc[-1])

    # 2) Get last price via ticker
    client = BybitClient()
    t = client.get_ticker(symbol, category=category)
    last = float(t.get("result", {}).get("list", [{}])[0].get("lastPrice", "0"))

    # 3) Define bracket config (risk 1%, SL 1xATR, TP 2xATR)
    cfg = BracketConfig(risk_pct=0.01, atr_mult_sl=1.0, atr_mult_tp=2.0, category=category)

    # 4) Build order (example: BUY slightly below last so it stays PostOnly)
    entry_px = last * 0.995  # 0.5% below
    exe = OrderExecutor(client=client)
    built = exe.build_bracket(symbol, side="Buy", entry_px=entry_px, atr=atr, equity=2000.0, cfg=cfg)

    print("Built order:", built)

    # 5) Submit
    resp = exe.submit(built)
    print("Submit response:", resp)

    order_id = resp.get("result", {}).get("orderId")
    if not order_id:
        print("No orderId returned; maybe it auto-canceled due to PostOnly cross? Check response above.")
        return

    # 6) Cancel (demo complete)
    cancel = exe.cancel(symbol, order_id=order_id, category=category)
    print("Cancel response:", cancel)

if __name__ == "__main__":
    main()
