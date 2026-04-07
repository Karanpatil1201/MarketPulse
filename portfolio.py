# ============================================================
# portfolio.py — Portfolio, transaction, and P&L management
# ============================================================

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from config import STARTING_CASH


# ------------------------------------------------------------------
# Data containers
# ------------------------------------------------------------------

@dataclass
class Holding:
    """A single stock position in the portfolio."""
    symbol:    str
    name:      str
    qty:       int     = 0
    avg_price: float   = 0.0   # volume-weighted average buy price

    @property
    def invested(self) -> float:
        return self.avg_price * self.qty


@dataclass
class Transaction:
    """Record of a single buy or sell event."""
    tx_type:   str    # "BUY" or "SELL"
    symbol:    str
    qty:       int
    price:     float
    timestamp: str    = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))

    @property
    def total(self) -> float:
        return self.qty * self.price


# ------------------------------------------------------------------
# Portfolio class
# ------------------------------------------------------------------

class Portfolio:
    """
    Manages cash, holdings, and transaction history.
    All monetary values are in INR (₹).
    """

    def __init__(self):
        self.cash: float                       = STARTING_CASH
        self.holdings: dict[str, Holding]      = {}
        self.history:  list[Transaction]       = []

    # ----------------------------------------------------------
    # Core operations
    # ----------------------------------------------------------

    def buy(self, symbol: str, name: str, qty: int, price: float) -> tuple[bool, str]:
        """
        Attempt to buy `qty` units at `price`.
        Returns (success: bool, message: str).
        """
        if qty <= 0:
            return False, "Quantity must be greater than zero."

        cost = qty * price
        if cost > self.cash:
            shortfall = cost - self.cash
            return False, f"Insufficient funds. Need ₹{shortfall:,.2f} more."

        # Deduct cash
        self.cash -= cost

        # Update holding (volume-weighted average price)
        if symbol in self.holdings:
            h = self.holdings[symbol]
            total_qty   = h.qty + qty
            h.avg_price = (h.avg_price * h.qty + price * qty) / total_qty
            h.qty       = total_qty
        else:
            self.holdings[symbol] = Holding(
                symbol=symbol, name=name, qty=qty, avg_price=price
            )

        # Record transaction
        self.history.append(Transaction("BUY", symbol, qty, price))
        return True, f"Bought {qty} × {symbol} @ ₹{price:,.2f}"

    def sell(self, symbol: str, qty: int, price: float) -> tuple[bool, str]:
        """
        Attempt to sell `qty` units at `price`.
        Returns (success: bool, message: str).
        """
        if qty <= 0:
            return False, "Quantity must be greater than zero."

        if symbol not in self.holdings or self.holdings[symbol].qty == 0:
            return False, f"You don't hold any shares of {symbol}."

        h = self.holdings[symbol]
        if qty > h.qty:
            return False, f"Only {h.qty} shares available to sell."

        # Credit cash
        self.cash += qty * price

        # Update holding
        h.qty -= qty
        if h.qty == 0:
            del self.holdings[symbol]

        # Record transaction
        self.history.append(Transaction("SELL", symbol, qty, price))
        return True, f"Sold {qty} × {symbol} @ ₹{price:,.2f}"

    # ----------------------------------------------------------
    # Computed properties
    # ----------------------------------------------------------

    def current_value(self, live_prices: dict[str, float]) -> float:
        """Total market value of all open positions."""
        return sum(
            h.qty * live_prices.get(sym, h.avg_price)
            for sym, h in self.holdings.items()
        )

    def total_invested(self) -> float:
        """Total cost basis of all open positions."""
        return sum(h.invested for h in self.holdings.values())

    def unrealized_pnl(self, live_prices: dict[str, float]) -> float:
        """Unrealized P&L across all open positions."""
        return self.current_value(live_prices) - self.total_invested()

    def net_worth(self, live_prices: dict[str, float]) -> float:
        """Cash + market value of all holdings."""
        return self.cash + self.current_value(live_prices)

    def holding_pnl(self, symbol: str, live_price: float) -> Optional[float]:
        """P&L for a single holding."""
        if symbol not in self.holdings:
            return None
        h = self.holdings[symbol]
        return (live_price - h.avg_price) * h.qty

    def holding_pnl_pct(self, symbol: str, live_price: float) -> Optional[float]:
        """% P&L for a single holding."""
        if symbol not in self.holdings:
            return None
        h = self.holdings[symbol]
        if h.avg_price == 0:
            return 0.0
        return ((live_price - h.avg_price) / h.avg_price) * 100
