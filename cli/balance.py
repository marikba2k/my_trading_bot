# cli/balance.py
from exchange.bybit_client import BybitClient
from config.settings import load_env

def main():
    cfg = load_env()
    client = BybitClient()

    print("=== Balance Check ===")
    print(f"Runtime mode : {cfg.runtime_mode}")
    print(f"Testnet flag : {cfg.testnet}\n")

    try:
        resp = client.get_balance()
        result = resp.get("result", {})
        balances = result.get("list", []) or []

        if not balances:
            print("No balance info returned.")
            return

        for acct in balances:
            coin_list = acct.get("coin", []) or []
            print(f"Account type: {acct.get('accountType')}")
            for c in coin_list:
                coin = c.get("coin")
                free = c.get("walletBalance")
                avail = c.get("availableToWithdraw")
                usd_val = c.get("equity")
                print(f"  {coin}: balance={free}, available={avail}, equity≈{usd_val}")
            print("")

    except Exception as e:
        print("Error fetching balance:", e)

if __name__ == "__main__":
    main()
