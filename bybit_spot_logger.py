import os, csv, time, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from pybit.unified_trading import WebSocket

load_dotenv()
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
TESTNET = (os.getenv("BYBIT_TESTNET","true").lower() == "true")

CSV_PATH = Path("bybit_spot_fills.csv")

# Keep a small local index of execIds so we never double-write
seen = set()
if CSV_PATH.exists():
    with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            seen.add(row["exec_id"])

# Ensure CSV has headers
headers = ["ts_utc","symbol","side","qty","price","fee","fee_asset","exec_id","order_id","is_maker"]
if not CSV_PATH.exists():
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=headers).writeheader()

def write_fill(fill: dict):
    exec_id = str(fill.get("execId"))
    if not exec_id or exec_id in seen:
        return
    seen.add(exec_id)

    # Quantities/prices can be strings; coerce safely
    def fnum(x):
        try:
            return float(x)
        except Exception:
            return 0.0

    row = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": fill.get("symbol"),
        "side": fill.get("side"),                    # "Buy" / "Sell"
        "qty": fnum(fill.get("execQty")),            # base asset qty (e.g., BTC)
        "price": fnum(fill.get("execPrice")),        # quote per base (e.g., USDT per BTC)
        "fee": fnum(fill.get("execFee")),            # fee amount
        "fee_asset": fill.get("feeCurrency"),        # often quote (e.g., USDT)
        "exec_id": exec_id,
        "order_id": fill.get("orderId"),
        "is_maker": "1" if fill.get("isMaker") else "0"
    }

    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writerow(row)

def on_execution(msg: dict):
    for fill in msg.get("data", []):
        write_fill(fill)

def on_order(_msg: dict):
    # Optional: store order lifecycle events if you want
    pass

if __name__ == "__main__":
    ws = WebSocket(
        testnet=TESTNET,
        channel_type="private",
        api_key=API_KEY,
        api_secret=API_SECRET,
    )
    ws.execution_stream(callback=on_execution)
    ws.order_stream(callback=on_order)

    print("Listening for spot fills… (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Bye.")
