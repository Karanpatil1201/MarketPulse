# ============================================================
# engine.py — Real-time price simulation engine
# Uses Geometric Brownian Motion (GBM):
#   price(t+1) = price(t) * exp(drift + volatility * N(0,1))
# ============================================================

import random
import math
import threading
import time
from config import STOCKS, PRICE_HISTORY_LEN, CANDLE_PERIOD, UPDATE_INTERVAL


class StockData:
    """Holds live state and price history for a single stock."""

    def __init__(self, symbol: str):
        cfg             = STOCKS[symbol]
        self.symbol     = symbol
        self.name       = cfg["name"]
        self.color      = cfg["color"]
        self.drift      = cfg["drift"]
        self.volatility = cfg["volatility"]

        # Live price
        self.price      = cfg["price"]
        self.open_price = cfg["price"]   # day-open reference
        self.prev_price = cfg["price"]   # previous tick

        # OHLC candle accumulation
        self._tick_count   = 0
        self._candle_open  = cfg["price"]
        self._candle_high  = cfg["price"]
        self._candle_low   = cfg["price"]

        # History lists — each element is a dict {o, h, l, c}
        self.candles: list[dict] = []

        # Momentum: last N tick-level close prices (for line overlay)
        self.tick_prices: list[float] = []

    # ----------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------
    def _gbm_step(self) -> float:
        """Return next price using Geometric Brownian Motion."""
        shock  = random.gauss(0, 1)
        factor = math.exp(self.drift + self.volatility * shock)
        return self.price * factor

    def _flush_candle(self):
        """Finalize current OHLC candle and append to history."""
        candle = {
            "o": self._candle_open,
            "h": self._candle_high,
            "l": self._candle_low,
            "c": self.price,
        }
        self.candles.append(candle)
        # Trim to max history length
        if len(self.candles) > PRICE_HISTORY_LEN:
            self.candles.pop(0)

        # Start new candle
        self._candle_open = self.price
        self._candle_high = self.price
        self._candle_low  = self.price

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------
    def tick(self):
        """Advance simulation by one time step."""
        self.prev_price = self.price
        self.price      = self._gbm_step()

        # Update candle accumulators
        if self.price > self._candle_high:
            self._candle_high = self.price
        if self.price < self._candle_low:
            self._candle_low = self.price

        # Store tick price for momentum line
        self.tick_prices.append(self.price)
        if len(self.tick_prices) > PRICE_HISTORY_LEN * CANDLE_PERIOD:
            self.tick_prices.pop(0)

        self._tick_count += 1
        if self._tick_count >= CANDLE_PERIOD:
            self._flush_candle()
            self._tick_count = 0

    # ----------------------------------------------------------
    # Derived properties
    # ----------------------------------------------------------
    @property
    def change_pct(self) -> float:
        """% change from day-open."""
        return ((self.price - self.open_price) / self.open_price) * 100

    @property
    def tick_change(self) -> float:
        """Absolute change from previous tick."""
        return self.price - self.prev_price

    @property
    def is_up(self) -> bool:
        return self.price >= self.prev_price


class PriceEngine:
    """
    Manages all stock simulations and runs a background thread
    that ticks every UPDATE_INTERVAL ms.  Observers can register
    a callback to receive updates.
    """

    def __init__(self):
        # Create one StockData per configured symbol
        self.stocks: dict[str, StockData] = {
            sym: StockData(sym) for sym in STOCKS
        }
        self._callbacks: list = []
        self._running   = False
        self._thread    = None

    # ----------------------------------------------------------
    # Observer registration
    # ----------------------------------------------------------
    def subscribe(self, callback):
        """Register a function to call after each price tick."""
        self._callbacks.append(callback)

    def _notify(self):
        for cb in self._callbacks:
            cb(self.stocks)

    # ----------------------------------------------------------
    # Thread control
    # ----------------------------------------------------------
    def start(self):
        """Start background simulation thread."""
        self._running = True
        self._thread  = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Gracefully stop the simulation."""
        self._running = False

    def _run_loop(self):
        interval_sec = UPDATE_INTERVAL / 1000.0
        while self._running:
            for stock in self.stocks.values():
                stock.tick()
            self._notify()
            time.sleep(interval_sec)

    # ----------------------------------------------------------
    # Convenience
    # ----------------------------------------------------------
    def get(self, symbol: str) -> StockData:
        return self.stocks[symbol]
