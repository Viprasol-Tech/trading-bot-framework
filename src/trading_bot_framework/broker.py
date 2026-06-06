"""Broker abstraction and an in-memory paper broker.

External venues (Interactive Brokers, Alpaca, ccxt, ...) plug in by
implementing :class:`Broker`. :class:`PaperBroker` is a complete, offline
implementation that tracks cash and a single-symbol position and fills market
orders at the latest seen price, so the whole framework runs without network.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from trading_bot_framework.models import Fill, Order, Side


class Broker(ABC):
    """Minimal broker interface a strategy runner needs."""

    @abstractmethod
    def update_price(self, symbol: str, price: float) -> None:
        """Inform the broker of the latest traded price for ``symbol``."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, order: Order) -> Fill:
        """Execute ``order`` immediately and return the resulting fill."""
        raise NotImplementedError

    @abstractmethod
    def position(self, symbol: str) -> float:
        """Return the current signed quantity held in ``symbol``."""
        raise NotImplementedError

    @abstractmethod
    def equity(self) -> float:
        """Return total account value: cash plus marked-to-market positions."""
        raise NotImplementedError


class PaperBroker(Broker):
    """A simple long-only paper-trading broker.

    Fills market orders at the last known price plus a proportional commission.
    Cash and a single position quantity are tracked exactly. Selling more than
    the held quantity or buying without enough cash raises ``ValueError`` so
    strategy bugs surface loudly instead of silently corrupting the books.
    """

    def __init__(self, cash: float = 10_000.0, fee_rate: float = 0.0) -> None:
        if cash < 0:
            raise ValueError("starting cash must be non-negative")
        if fee_rate < 0:
            raise ValueError("fee_rate must be non-negative")
        self.cash = cash
        self.fee_rate = fee_rate
        self._positions: dict[str, float] = {}
        self._prices: dict[str, float] = {}

    def update_price(self, symbol: str, price: float) -> None:
        """Record the latest price used for fills and equity marking."""
        if price <= 0:
            raise ValueError("price must be positive")
        self._prices[symbol] = price

    def execute(self, order: Order) -> Fill:
        """Fill ``order`` at the last recorded price for its symbol."""
        if order.quantity <= 0:
            raise ValueError("order quantity must be positive")
        price = self._prices.get(order.symbol)
        if price is None:
            raise ValueError(f"no price known for {order.symbol!r}")

        fee = order.quantity * price * self.fee_rate
        fill = Fill(order.symbol, order.side, order.quantity, price, fee)

        held = self._positions.get(order.symbol, 0.0)
        if order.side is Side.BUY:
            if -fill.cash_delta > self.cash + 1e-9:
                raise ValueError("insufficient cash for buy order")
            self._positions[order.symbol] = held + order.quantity
        else:
            if order.quantity > held + 1e-9:
                raise ValueError("cannot sell more than current position")
            self._positions[order.symbol] = held - order.quantity

        self.cash += fill.cash_delta
        return fill

    def position(self, symbol: str) -> float:
        """Return the signed quantity currently held in ``symbol``."""
        return self._positions.get(symbol, 0.0)

    def equity(self) -> float:
        """Cash plus the marked-to-market value of every open position."""
        total = self.cash
        for symbol, qty in self._positions.items():
            price = self._prices.get(symbol, 0.0)
            total += qty * price
        return total
