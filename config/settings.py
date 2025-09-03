# config/settings.py
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env in the project folder

@dataclass
class Settings:
    api_key: str
    api_secret: str
    testnet: bool
    log_level: str
    runtime_mode: str  # "backtest" | "paper" | "live"
    db_path: Path

def load_env() -> Settings:
    api_key = os.getenv("BYBIT_API_KEY", "").strip()
    api_secret = os.getenv("BYBIT_API_SECRET", "").strip()
    testnet = os.getenv("BYBIT_TESTNET", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    runtime_mode = os.getenv("RUNTIME_MODE", "paper").lower()
    db_path = Path("storage/tradebot.sqlite")

    # Friendly checks with clear messages
    if not api_key or len(api_key) < 6:
        raise ValueError("Missing or invalid BYBIT_API_KEY in .env")
    if not api_secret or len(api_secret) < 10:
        raise ValueError("Missing or invalid BYBIT_API_SECRET in .env")
    if runtime_mode not in {"backtest", "paper", "live"}:
        raise ValueError("RUNTIME_MODE must be backtest, paper, or live")

    return Settings(
        api_key=api_key,
        api_secret=api_secret,
        testnet=testnet,
        log_level=log_level,
        runtime_mode=runtime_mode,
        db_path=db_path,
    )
