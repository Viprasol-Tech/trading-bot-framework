"""The strategy runner: feed bars to a strategy and execute its orders.

:class:`Engine` is the glue between a :class:`~trading_bot_framework.strategy.Strategy`
and a :class:`~trading_bot_framework.broker.Broker`. It maintains the rolling
history, builds the per-bar :class:`~trading_bot_framework.strategy.Context`,
forwards the latest price to the broker, and records every resulting fill.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Iterable

from trading_bot_framework.broker import Broker
from trading_bot_framework.models import Bar, Fill
from trading_bot_framework.strategy import Context, Strategy


class Engine:
    """Drive one strategy over a stream of bars against one broker."""

    def __init__(self, strategy: Strategy, broker: Broker) -> None:
        self.strategy = strategy
        self.broker = broker
        self.history: list[Bar] = []
        self.fills: list[Fill] = []

    def step(self, bar: Bar) -> list[Fill]:
        """Process a single bar and return the fills it produced."""
        self.history.append(bar)
        self.broker.update_price(bar.symbol, bar.close)
        ctx = Context(bar=bar, history=tuple(self.history), broker=self.broker)
        produced: list[Fill] = []
        for order in self.strategy.on_bar(ctx):
            fill = self.broker.execute(order)
            self.fills.append(fill)
            produced.append(fill)
        return produced

    def run(self, bars: Iterable[Bar]) -> float:
        """Replay every bar and return the broker's final equity."""
        for bar in bars:
            self.step(bar)
        return self.broker.equity()
