"""Strategy interface and the per-bar context passed to it.

A :class:`Strategy` is pure decision logic: it receives a :class:`Context` for
each bar and returns the orders it wants to place. The :mod:`engine` executes
those orders on the broker. Keeping strategies free of side effects makes them
trivial to unit-test and to reuse across live trading and backtesting.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from trading_bot_framework.broker import Broker
from trading_bot_framework.models import Bar, Order, Side


@dataclass(slots=True, frozen=True)
class Context:
    """Everything a strategy is allowed to see when deciding on a bar.

    ``history`` includes the current bar as its last element, so a strategy can
    look back over closes without keeping its own buffers.
    """

    bar: Bar
    history: tuple[Bar, ...]
    broker: Broker

    @property
    def position(self) -> float:
        """Current signed quantity held in the bar's symbol."""
        return self.broker.position(self.bar.symbol)

    def closes(self) -> list[float]:
        """Return the close price of every bar seen so far, oldest first."""
        return [b.close for b in self.history]

    def buy(self, quantity: float) -> Order:
        """Convenience constructor for a market buy of ``quantity``."""
        return Order(self.bar.symbol, Side.BUY, quantity)

    def sell(self, quantity: float) -> Order:
        """Convenience constructor for a market sell of ``quantity``."""
        return Order(self.bar.symbol, Side.SELL, quantity)


class Strategy(ABC):
    """Base class for all trading strategies."""

    name: str = "strategy"

    @abstractmethod
    def on_bar(self, ctx: Context) -> list[Order]:
        """Return the orders to place for the current bar (may be empty)."""
        raise NotImplementedError
