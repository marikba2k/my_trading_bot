# cli/init_check.py
from config.settings import load_env
from core.logger import get_logger

def main():
    try:
        cfg = load_env()
    except Exception as e:
        print("Config error:", e)
        return
    log = get_logger("init", cfg.log_level)
    log.info("Config loaded successfully")
    log.info(f"Mode={cfg.runtime_mode} | Testnet={cfg.testnet} | DB={cfg.db_path}")

if __name__ == "__main__":
    main()
