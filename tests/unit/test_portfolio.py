"""Tests for the multi-symbol portfolio engine."""

from __future__ import annotations

import pytest

from trading_bot_framework.broker import PaperBroker
from trading_bot_framework.data import sine_bars
from trading_bot_framework.models import Bar, Order, Side
from trading_bot_framework.portfolio import (
    Allocation,
    PortfolioEngine,
    backtest_portfolio,
)
from trading_bot_framework.strategies import RsiStrategy, SmaCrossStrategy
from trading_bot_framework.strategy import Context, Strategy


class _BuyHold(Strategy):
    """Buy ``qty`` once on the first bar of a symbol, then hold."""

    name = "buy_hold"

    def __init__(self, qty: float) -> None:
        self.qty = qty
        self._done = False

    def on_bar(self, ctx: Context) -> list[Order]:
        if not self._done:
            self._done = True
            return [ctx.buy(self.qty)]
        return []


def test_portfolio_requires_allocations() -> None:
    broker = PaperBroker()
    with pytest.raises(ValueError):
        PortfolioEngine(broker, [])


def test_portfolio_rejects_duplicate_symbols() -> None:
    broker = PaperBroker()
    a = Allocation("AAA", SmaCrossStrategy(), sine_bars(n=30, symbol="AAA"))
    b = Allocation("AAA", RsiStrategy(), sine_bars(n=30, symbol="AAA"))
    with pytest.raises(ValueError):
        PortfolioEngine(broker, [a, b])


def test_equity_curve_length_matches_longest_series() -> None:
    allocs = [
        Allocation("AAA", SmaCrossStrategy(quantity=1.0), sine_bars(n=60, symbol="AAA")),
        Allocation("BBB", RsiStrategy(quantity=1.0), sine_bars(n=40, symbol="BBB")),
    ]
    result = backtest_portfolio(allocs, starting_cash=50_000.0)
    assert len(result.equity_curve) == 60


def test_portfolio_tracks_two_independent_positions() -> None:
    a_bars = [
        Bar(index=0, symbol="AAA", open=10.0, high=10.0, low=10.0, close=10.0),
        Bar(index=1, symbol="AAA", open=20.0, high=20.0, low=20.0, close=20.0),
    ]
    b_bars = [
        Bar(index=0, symbol="BBB", open=5.0, high=5.0, low=5.0, close=5.0),
        Bar(index=1, symbol="BBB", open=5.0, high=5.0, low=5.0, close=5.0),
    ]
    allocs = [
        Allocation("AAA", _BuyHold(2.0), a_bars),
        Allocation("BBB", _BuyHold(3.0), b_bars),
    ]
    broker = PaperBroker(cash=1_000.0)
    engine = PortfolioEngine(broker, allocs)
    result = engine.run()

    assert broker.position("AAA") == pytest.approx(2.0)
    assert broker.position("BBB") == pytest.approx(3.0)
    # Cash: 1000 - 2*10 (AAA @ bar0) - 3*5 (BBB @ bar0) = 965.
    assert broker.cash == pytest.approx(965.0)
    # Equity at end: 965 + 2*20 + 3*5 = 1020.
    assert result.final_equity == pytest.approx(1_020.0)
    assert result.fills_by_symbol == {"AAA": 1, "BBB": 1}
    assert result.num_fills == 2


def test_fills_are_attributed_to_correct_symbol() -> None:
    allocs = [
        Allocation(
            "AAA", SmaCrossStrategy(fast=3, slow=8, quantity=1.0), sine_bars(n=80, symbol="AAA")
        ),
        Allocation(
            "BBB", SmaCrossStrategy(fast=3, slow=8, quantity=1.0), sine_bars(n=80, symbol="BBB")
        ),
    ]
    result = backtest_portfolio(allocs, starting_cash=100_000.0)
    assert set(result.fills_by_symbol) == {"AAA", "BBB"}
    assert result.num_fills == sum(result.fills_by_symbol.values())


def test_fees_reduce_final_equity() -> None:
    allocs = [
        Allocation(
            "AAA", SmaCrossStrategy(fast=3, slow=8, quantity=1.0), sine_bars(n=120, symbol="AAA")
        ),
    ]
    free = backtest_portfolio(allocs, starting_cash=100_000.0, fee_rate=0.0)
    allocs2 = [
        Allocation(
            "AAA", SmaCrossStrategy(fast=3, slow=8, quantity=1.0), sine_bars(n=120, symbol="AAA")
        ),
    ]
    charged = backtest_portfolio(allocs2, starting_cash=100_000.0, fee_rate=0.01)
    assert charged.final_equity < free.final_equity


def test_side_enum_used_in_fills() -> None:
    allocs = [
        Allocation("AAA", _BuyHold(1.0), sine_bars(n=5, symbol="AAA")),
    ]
    broker = PaperBroker(cash=10_000.0)
    engine = PortfolioEngine(broker, allocs)
    engine.run()
    assert all(f.side is Side.BUY for f in engine.fills)
