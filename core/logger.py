# core/logger.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already set up

    logger.setLevel(level)

    # Console handler (prints to terminal)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(ch)

    # File handler (writes to logs/app.log, rotates when big)
    Path("logs").mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(fh)

    return logger
