# cli/order_sanity.py
from exchange.bybit_client import BybitClient

def main():
    client = BybitClient()
    symbol = "BTCUSDT"          # USDT perpetual on testnet
    category = "linear"         # linear = USDT-margined perpetuals

    # 1) Connection & last price
    print("Ping:", client.ping())
    t = client.get_ticker(symbol, category=category)
    last_str = t.get("result", {}).get("list", [{}])[0].get("lastPrice", "0")
    last = float(last_str)
    print(f"Last price {symbol}:", last)

    # 2) Exchange rules: min qty, steps, tick size
    min_qty, qty_step = client.get_min_qty(symbol, category)
    tick = client.get_tick_size(symbol, category)
    if min_qty is None:
        print("Could not fetch symbol rules. Aborting.")
        return

    # Use the minimum valid size (rounded to step)
    test_qty = max(min_qty, qty_step)
    # Round defensively to the step
    test_qty = client._round_step(test_qty, qty_step)

    # 3) Pick a limit price far from market so it won't fill
    #    - For BUY, set 10% LOWER than last
    #    - For SELL, set 10% HIGHER than last
    side = "Buy"
    raw_price = last * 0.9 if side == "Buy" else last * 1.1
    price = client._round_step(raw_price, tick)

    print(f"Placing PostOnly {side} {test_qty} {symbol} at {price} (tick={tick}, step={qty_step})")

    # 4) Place the order (PostOnly => maker only; won’t cross)
    resp = client.place_postonly_limit(symbol, side, test_qty, price, category=category)
    print("Place order response:", resp)

    order_id = resp.get("result", {}).get("orderId")
    if not order_id:
        print("No orderId returned; cannot cancel. Response may include an error message above.")
        return

    # 5) Immediately cancel to complete the lifecycle
    print("Cancelling order:", order_id)
    cancel = client.cancel_order(symbol, order_id=order_id, category=category)
    print("Cancel response:", cancel)

if __name__ == "__main__":
    main()
