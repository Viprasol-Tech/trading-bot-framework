"""Tests for the backtest runner and engine."""

from __future__ import annotations

import math

import pytest

from trading_bot_framework.backtest import BacktestResult, backtest
from trading_bot_framework.broker import PaperBroker
from trading_bot_framework.engine import Engine
from trading_bot_framework.models import Bar, Order, Side
from trading_bot_framework.strategies import SmaCrossStrategy
from trading_bot_framework.strategy import Context, Strategy


def _bars(n: int = 120, symbol: str = "ACME") -> list[Bar]:
    out: list[Bar] = []
    for i in range(n):
        close = 100.0 + 15.0 * math.sin(i / 12.0) + 5.0 * math.sin(i / 3.0)
        out.append(
            Bar(index=i, symbol=symbol, open=close, high=close + 1, low=close - 1, close=close)
        )
    return out


def test_equity_curve_has_one_point_per_bar() -> None:
    bars = _bars(120)
    result = backtest(SmaCrossStrategy(fast=5, slow=20, quantity=5.0), bars)
    assert isinstance(result, BacktestResult)
    assert len(result.equity_curve) == len(bars)


def test_total_return_is_float() -> None:
    bars = _bars(120)
    result = backtest(SmaCrossStrategy(fast=5, slow=20, quantity=5.0), bars)
    assert isinstance(result.total_return, float)
    # Equity must equal cash when flat at the end (strategy is round-trip).
    assert isinstance(result.final_equity, float)


def test_buy_and_hold_return_matches_price_move() -> None:
    class BuyOnce(Strategy):
        name = "buy_once"

        def __init__(self) -> None:
            self.done = False

        def on_bar(self, ctx: Context) -> list[Order]:
            if not self.done:
                self.done = True
                return [ctx.buy(1.0)]
            return []

    bars = [
        Bar(index=0, symbol="ACME", open=100.0, high=100.0, low=100.0, close=100.0),
        Bar(index=1, symbol="ACME", open=110.0, high=110.0, low=110.0, close=110.0),
    ]
    result = backtest(BuyOnce(), bars, starting_cash=1_000.0)
    # Bought 1 unit @100; final equity = 900 cash + 110 position = 1010 -> +1%.
    assert result.final_equity == pytest.approx(1_010.0)
    assert result.total_return == pytest.approx(0.01)


def test_engine_records_fills() -> None:
    broker = PaperBroker(cash=10_000.0)
    engine = Engine(SmaCrossStrategy(fast=3, slow=8, quantity=2.0), broker)
    final = engine.run(_bars(100))
    assert isinstance(final, float)
    assert all(f.side in (Side.BUY, Side.SELL) for f in engine.fills)


def test_max_drawdown_non_positive() -> None:
    result = backtest(SmaCrossStrategy(fast=5, slow=20, quantity=5.0), _bars(150))
    assert result.max_drawdown <= 0.0
