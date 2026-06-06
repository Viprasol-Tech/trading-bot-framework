"""Multi-symbol portfolio engine.

Where :class:`~trading_bot_framework.engine.Engine` drives one strategy over
one symbol, :class:`PortfolioEngine` runs *many* symbol/strategy pairs against a
single shared :class:`~trading_bot_framework.broker.PaperBroker`. Bars from all
symbols are merged on their ``index`` and replayed in lock-step, so cash and
the equity curve reflect the whole book at every time step.

This makes it possible to backtest a basket (e.g. an SMA-cross on one symbol and
an RSI mean-reversion on another) sharing one capital pool with realistic
fees and slippage.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from trading_bot_framework.broker import PaperBroker
from trading_bot_framework.models import Bar, Fill
from trading_bot_framework.strategy import Context, Strategy


@dataclass(slots=True)
class Allocation:
    """One strategy bound to one symbol's bar series."""

    symbol: str
    strategy: Strategy
    bars: Sequence[Bar]


@dataclass(slots=True)
class PortfolioResult:
    """Outcome of a portfolio backtest."""

    starting_equity: float
    final_equity: float
    equity_curve: list[float] = field(default_factory=list)
    fills_by_symbol: dict[str, int] = field(default_factory=dict)

    @property
    def num_fills(self) -> int:
        """Total fills across every symbol in the book."""
        return sum(self.fills_by_symbol.values())


class PortfolioEngine:
    """Replay several symbol/strategy allocations against one broker."""

    def __init__(self, broker: PaperBroker, allocations: Sequence[Allocation]) -> None:
        if not allocations:
            raise ValueError("at least one allocation is required")
        symbols = [a.symbol for a in allocations]
        if len(set(symbols)) != len(symbols):
            raise ValueError("each symbol may appear in at most one allocation")
        self.broker = broker
        self.allocations = list(allocations)
        self._history: dict[str, list[Bar]] = {a.symbol: [] for a in allocations}
        self.fills: list[Fill] = []

    def run(self) -> PortfolioResult:
        """Replay all allocations in lock-step and return portfolio stats.

        Bars are stepped by position: at step ``t`` every allocation that has a
        bar at index ``t`` is processed, its price pushed to the broker, and its
        strategy consulted. Equity is recorded once per step after all symbols
        for that step have traded.
        """
        starting_equity = self.broker.equity() or self.broker.cash
        max_len = max(len(a.bars) for a in self.allocations)
        curve: list[float] = []
        fills_by_symbol: dict[str, int] = {a.symbol: 0 for a in self.allocations}

        for t in range(max_len):
            for alloc in self.allocations:
                if t >= len(alloc.bars):
                    continue
                bar = alloc.bars[t]
                hist = self._history[alloc.symbol]
                hist.append(bar)
                self.broker.update_price(bar.symbol, bar.close)
                ctx = Context(bar=bar, history=tuple(hist), broker=self.broker)
                for order in alloc.strategy.on_bar(ctx):
                    fill = self.broker.execute(order)
                    self.fills.append(fill)
                    fills_by_symbol[fill.symbol] += 1
            curve.append(self.broker.equity())

        return PortfolioResult(
            starting_equity=starting_equity,
            final_equity=self.broker.equity(),
            equity_curve=curve,
            fills_by_symbol=fills_by_symbol,
        )


def backtest_portfolio(
    allocations: Sequence[Allocation],
    starting_cash: float = 10_000.0,
    fee_rate: float = 0.0,
    slippage_rate: float = 0.0,
) -> PortfolioResult:
    """Convenience wrapper: build a broker and run a portfolio backtest."""
    broker = PaperBroker(cash=starting_cash, fee_rate=fee_rate, slippage_rate=slippage_rate)
    engine = PortfolioEngine(broker, allocations)
    return engine.run()
