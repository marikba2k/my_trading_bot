# cli/bybit_check.py
from exchange.bybit_client import BybitClient

def main():
    client = BybitClient()

    # Test connection
    print("Ping:", client.ping())
    print("Server time:", client.server_time())

    # Market data
    symbols = client.get_symbols()
    print("Got", len(symbols["result"]["list"]), "symbols")

    ticker = client.get_ticker("BTCUSDT")
    print("BTCUSDT ticker:", ticker)

    klines = client.get_klines("BTCUSDT", interval="15", limit=3)
    print("Last 3 candles:", klines)

    # Account info
    balance = client.get_balance()
    print("Balance:", balance)

if __name__ == "__main__":
    main()
