# exchange/bybit_client.py
from pybit.unified_trading import HTTP
from config.settings import load_env
from core.logger import get_logger


class BybitClient:
    def __init__(self):
        self.cfg = load_env()
        self.log = get_logger("BybitClient", self.cfg.log_level)

        # Create a session
        self.session = HTTP(
            api_key=self.cfg.api_key,
            api_secret=self.cfg.api_secret,
            testnet=self.cfg.testnet,
            demo=True
        )
        self.log.info("Bybit client initialized (testnet=%s)", self.cfg.testnet)

    # --- Basic checks ---
    def ping(self) -> bool:
        try:
            self.session.get_server_time()
            return True
        except Exception as e:
            self.log.error("Ping failed: %s", e)
            return False

    def server_time(self):
        try:
            return self.session.get_server_time()
        except Exception as e:
            self.log.error("Server time error: %s", e)
            return None

    # --- Market data ---
    def get_symbols(self, category="linear"):
        return self.session.get_instruments_info(category=category)

    def get_ticker(self, symbol, category="linear"):
        return self.session.get_tickers(category=category, symbol=symbol)

    def get_klines(self, symbol, interval="15", limit=100, category="linear"):
        return self.session.get_kline(category=category, symbol=symbol, interval=interval, limit=limit)

    # --- Account info ---
    def get_balance(self, account_type="UNIFIED"):
        return self.session.get_wallet_balance(accountType=account_type)

    def get_positions(self, symbol=None, category="linear"):
        return self.session.get_positions(category=category, symbol=symbol)

    # --- Orders ---
    def place_order(self, symbol, side, qty, order_type="Market", price=None, category="linear", **kwargs):
        return self.session.place_order(
            category=category,
            symbol=symbol,
            side=side,
            orderType=order_type,
            qty=qty,
            price=price,
            **kwargs
        )

    def cancel_order(self, symbol, order_id=None, category="linear", **kwargs):
        return self.session.cancel_order(category=category, symbol=symbol, orderId=order_id, **kwargs)

    def get_fills(self, symbol=None, category="linear"):
        return self.session.get_executions(category=category, symbol=symbol)
    
    def get_symbol_info(self, symbol, category="linear"):
        try:
            data = self.session.get_instruments_info(category=category, symbol=symbol)
            items = data.get("result", {}).get("list", [])
            return items[0] if items else None
        except Exception as e:
            self.log.error("get_symbol_info error: %s", e)
            return None

    # Pull min qty & step from instrument specs (so we don't send invalid sizes)
    def get_min_qty(self, symbol, category="linear"):
        info = self.get_symbol_info(symbol, category)
        if not info:
            return None, None
        lot = info.get("lotSizeFilter", {})
        # On Bybit, qtyStep tells you the smallest increment; minOrderQty is the absolute minimum
        min_qty = float(lot.get("minOrderQty", "0.001"))
        step = float(lot.get("qtyStep", "0.001"))
        return min_qty, step

    # Price step (tick size) to make valid limit prices
    def get_tick_size(self, symbol, category="linear"):
        info = self.get_symbol_info(symbol, category)
        if not info:
            return None
        price_filter = info.get("priceFilter", {})
        tick = float(price_filter.get("tickSize", "0.5"))
        return tick

    # Round a number to the nearest valid exchange step
    @staticmethod
    def _round_step(value: float, step: float) -> float:
        if step <= 0:
            return value
        # round to nearest multiple of step
        return round(round(value / step) * step, 12)

    # Safe Post-Only limit order (maker only). If it would cross the book, Bybit auto-cancels it.
    def place_postonly_limit(self, symbol, side, qty, price, category="linear"):
        return self.place_order(
            symbol=symbol,
            side=side,
            qty=qty,
            order_type="Limit",
            price=price,
            category=category,
            timeInForce="PostOnly"
        )

