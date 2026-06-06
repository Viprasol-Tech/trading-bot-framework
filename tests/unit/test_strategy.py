"""Tests for the SMA-cross strategy signals and the sma() helper."""

from __future__ import annotations

import pytest

from trading_bot_framework.broker import PaperBroker
from trading_bot_framework.models import Bar, Order, Side
from trading_bot_framework.strategies import SmaCrossStrategy, sma
from trading_bot_framework.strategy import Context


def _ctx(closes: list[float], broker: PaperBroker, symbol: str = "ACME") -> Context:
    bars = tuple(
        Bar(index=i, symbol=symbol, open=c, high=c, low=c, close=c) for i, c in enumerate(closes)
    )
    broker.update_price(symbol, closes[-1])
    return Context(bar=bars[-1], history=bars, broker=broker)


def test_sma_needs_full_window() -> None:
    assert sma([1.0, 2.0], 3) is None
    assert sma([1.0, 2.0, 3.0], 3) == pytest.approx(2.0)
    assert sma([1.0, 2.0, 3.0, 4.0], 2) == pytest.approx(3.5)


def test_no_signal_before_enough_data() -> None:
    strat = SmaCrossStrategy(fast=2, slow=3)
    broker = PaperBroker()
    assert strat.on_bar(_ctx([10.0, 11.0], broker)) == []


def test_bullish_cross_emits_buy() -> None:
    # Falling then jumping: the fast SMA crosses above the slow SMA -> buy.
    strat = SmaCrossStrategy(fast=2, slow=3, quantity=1.0)
    broker = PaperBroker()
    closes = [10.0, 9.0, 8.0, 12.0]
    orders = strat.on_bar(_ctx(closes, broker))
    assert len(orders) == 1
    assert orders[0].side is Side.BUY
    assert orders[0].quantity == 1.0


def test_bearish_cross_sells_entire_position() -> None:
    strat = SmaCrossStrategy(fast=2, slow=3, quantity=1.0)
    broker = PaperBroker()
    # Establish an existing long position of 2 units.
    broker.update_price("ACME", 8.0)
    broker.execute(Order("ACME", Side.BUY, 2.0))
    assert broker.position("ACME") == 2.0

    closes = [10.0, 11.0, 12.0, 6.0]  # last bar drags the fast SMA below slow
    orders = strat.on_bar(_ctx(closes, broker))
    assert len(orders) == 1
    assert orders[0].side is Side.SELL
    assert orders[0].quantity == pytest.approx(2.0)


def test_no_double_buy_when_already_long() -> None:
    strat = SmaCrossStrategy(fast=2, slow=3, quantity=1.0)
    broker = PaperBroker()
    broker.update_price("ACME", 8.0)
    broker.execute(Order("ACME", Side.BUY, 1.0))  # already long
    closes = [10.0, 9.0, 8.0, 12.0]  # bullish cross, but position is open
    assert strat.on_bar(_ctx(closes, broker)) == []


def test_fast_must_be_shorter_than_slow() -> None:
    with pytest.raises(ValueError):
        SmaCrossStrategy(fast=5, slow=5)
