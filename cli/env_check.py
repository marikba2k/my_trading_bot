# cli/env_check.py
from config.settings import load_env

def main():
    cfg = load_env()
    print("=== Environment Check ===")
    print(f"Runtime mode : {cfg.runtime_mode}")
    print(f"Testnet flag : {cfg.testnet}")
    if cfg.testnet:
        print("👉 Trading on TESTNET (safe sandbox)")
    else:
        print("⚠️ Trading on MAINNET (real money!)")

if __name__ == "__main__":
    main()
