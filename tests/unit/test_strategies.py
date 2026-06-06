"""Tests for the RSI, breakout, and mean-reversion strategies."""

from __future__ import annotations

import pytest

from trading_bot_framework.broker import PaperBroker
from trading_bot_framework.models import Bar, Order, Side
from trading_bot_framework.strategies import (
    BreakoutStrategy,
    MeanReversionStrategy,
    RsiStrategy,
)
from trading_bot_framework.strategy import Context


def _ctx(closes: list[float], broker: PaperBroker, symbol: str = "ACME") -> Context:
    bars = tuple(
        Bar(index=i, symbol=symbol, open=c, high=c, low=c, close=c) for i, c in enumerate(closes)
    )
    broker.update_price(symbol, closes[-1])
    return Context(bar=bars[-1], history=bars, broker=broker)


# --- RSI strategy -----------------------------------------------------------


def test_rsi_buys_when_oversold() -> None:
    strat = RsiStrategy(period=14, lower=30.0, upper=70.0, quantity=1.0)
    broker = PaperBroker()
    falling = [float(i) for i in range(40, 20, -1)]  # strictly down -> RSI ~ 0
    orders = strat.on_bar(_ctx(falling, broker))
    assert len(orders) == 1
    assert orders[0].side is Side.BUY


def test_rsi_sells_when_overbought_and_long() -> None:
    strat = RsiStrategy(period=14, lower=30.0, upper=70.0, quantity=1.0)
    broker = PaperBroker()
    broker.update_price("ACME", 10.0)
    broker.execute(Order("ACME", Side.BUY, 2.0))
    rising = [float(i) for i in range(1, 21)]  # strictly up -> RSI ~ 100
    orders = strat.on_bar(_ctx(rising, broker))
    assert len(orders) == 1
    assert orders[0].side is Side.SELL
    assert orders[0].quantity == pytest.approx(2.0)


def test_rsi_no_signal_while_warming_up() -> None:
    strat = RsiStrategy(period=14)
    broker = PaperBroker()
    assert strat.on_bar(_ctx([10.0, 11.0, 12.0], broker)) == []


def test_rsi_rejects_bad_bounds() -> None:
    with pytest.raises(ValueError):
        RsiStrategy(lower=70.0, upper=30.0)


# --- Breakout strategy ------------------------------------------------------


def test_breakout_enters_on_new_high() -> None:
    strat = BreakoutStrategy(lookback=5, exit_lookback=3, quantity=1.0)
    broker = PaperBroker()
    closes = [10.0, 10.0, 10.0, 10.0, 10.0, 15.0]  # last bar breaks the range
    orders = strat.on_bar(_ctx(closes, broker))
    assert len(orders) == 1
    assert orders[0].side is Side.BUY


def test_breakout_no_entry_inside_range() -> None:
    strat = BreakoutStrategy(lookback=5, exit_lookback=3, quantity=1.0)
    broker = PaperBroker()
    closes = [10.0, 12.0, 11.0, 13.0, 12.0, 12.5]  # below prior high of 13
    assert strat.on_bar(_ctx(closes, broker)) == []


def test_breakout_exits_on_breakdown() -> None:
    strat = BreakoutStrategy(lookback=5, exit_lookback=3, quantity=1.0)
    broker = PaperBroker()
    broker.update_price("ACME", 12.0)
    broker.execute(Order("ACME", Side.BUY, 1.0))
    closes = [12.0, 13.0, 14.0, 11.0, 10.5, 9.0]  # last bar breaks below recent low
    orders = strat.on_bar(_ctx(closes, broker))
    assert len(orders) == 1
    assert orders[0].side is Side.SELL


def test_breakout_rejects_bad_lookback() -> None:
    with pytest.raises(ValueError):
        BreakoutStrategy(lookback=1)


# --- Mean-reversion strategy ------------------------------------------------


def test_mean_reversion_buys_on_band_breach() -> None:
    strat = MeanReversionStrategy(window=5, num_std=1.0, quantity=1.0)
    broker = PaperBroker()
    closes = [10.0, 10.0, 10.0, 10.0, 6.0]  # sharp dip below the lower band
    orders = strat.on_bar(_ctx(closes, broker))
    assert len(orders) == 1
    assert orders[0].side is Side.BUY


def test_mean_reversion_exits_on_reversion() -> None:
    strat = MeanReversionStrategy(window=5, num_std=1.0, quantity=1.0)
    broker = PaperBroker()
    broker.update_price("ACME", 6.0)
    broker.execute(Order("ACME", Side.BUY, 1.0))
    closes = [8.0, 9.0, 10.0, 11.0, 12.0]  # price at/above the moving average
    orders = strat.on_bar(_ctx(closes, broker))
    assert len(orders) == 1
    assert orders[0].side is Side.SELL


def test_mean_reversion_no_signal_inside_band() -> None:
    strat = MeanReversionStrategy(window=5, num_std=2.0, quantity=1.0)
    broker = PaperBroker()
    closes = [10.0, 10.1, 9.9, 10.05, 9.95]  # tight range, no breach
    assert strat.on_bar(_ctx(closes, broker)) == []


def test_mean_reversion_rejects_bad_std() -> None:
    with pytest.raises(ValueError):
        MeanReversionStrategy(num_std=0.0)
