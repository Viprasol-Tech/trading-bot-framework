"""Core domain types for the trading bot framework.

Defines the price ``Bar``, ``Order``, ``Fill`` and the per-step ``Context``
that strategies receive. Keeping these as plain dataclasses makes them cheap to
construct in hot backtesting loops and trivial to assert against in tests.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Side(str, Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


@dataclass(slots=True, frozen=True)
class Bar:
    """A single OHLC price bar for one symbol.

    ``index`` is the position of the bar in the series (0-based), which lets
    time-based strategies make decisions without depending on wall-clock time.
    """

    index: int
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass(slots=True, frozen=True)
class Order:
    """A market order request emitted by a strategy.

    Orders are filled by the broker at the current bar's close price. A positive
    ``quantity`` together with the ``side`` fully describes the trade.
    """

    symbol: str
    side: Side
    quantity: float


@dataclass(slots=True, frozen=True)
class Fill:
    """The result of executing an :class:`Order` against a broker."""

    symbol: str
    side: Side
    quantity: float
    price: float
    fee: float = 0.0

    @property
    def cash_delta(self) -> float:
        """Signed change in cash this fill causes (negative when buying)."""
        gross = self.quantity * self.price
        if self.side is Side.BUY:
            return -(gross + self.fee)
        return gross - self.fee
