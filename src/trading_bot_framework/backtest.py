"""Backtesting: run a strategy over historical bars and measure performance.

:func:`backtest` runs an :class:`~trading_bot_framework.engine.Engine` and
records the account equity after every bar, producing an equity curve plus
summary statistics (total return, max drawdown, number of fills). Everything is
computed offline from the in-memory broker, so backtests are deterministic.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from trading_bot_framework.broker import PaperBroker
from trading_bot_framework.engine import Engine
from trading_bot_framework.models import Bar
from trading_bot_framework.strategy import Strategy


@dataclass(slots=True)
class BacktestResult:
    """The outcome of a backtest run."""

    starting_equity: float
    final_equity: float
    equity_curve: list[float] = field(default_factory=list)
    num_fills: int = 0

    @property
    def total_return(self) -> float:
        """Fractional return over the run (0.10 means +10%)."""
        if self.starting_equity == 0.0:
            return 0.0
        return self.final_equity / self.starting_equity - 1.0

    @property
    def max_drawdown(self) -> float:
        """Largest peak-to-trough decline of the equity curve, as a fraction."""
        peak = float("-inf")
        worst = 0.0
        for value in self.equity_curve:
            peak = max(peak, value)
            if peak > 0:
                worst = min(worst, value / peak - 1.0)
        return worst


def backtest(
    strategy: Strategy,
    bars: Sequence[Bar],
    starting_cash: float = 10_000.0,
    fee_rate: float = 0.0,
) -> BacktestResult:
    """Run ``strategy`` over ``bars`` and return performance statistics.

    The equity curve has exactly one entry per bar (the account equity marked
    to that bar's close), so ``len(result.equity_curve) == len(bars)``.
    """
    broker = PaperBroker(cash=starting_cash, fee_rate=fee_rate)
    engine = Engine(strategy, broker)
    curve: list[float] = []
    for bar in bars:
        engine.step(bar)
        curve.append(broker.equity())
    return BacktestResult(
        starting_equity=starting_cash,
        final_equity=broker.equity(),
        equity_curve=curve,
        num_fills=len(engine.fills),
    )
