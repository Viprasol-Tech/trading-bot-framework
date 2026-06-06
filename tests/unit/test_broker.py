"""Tests for PaperBroker cash, position, and equity math."""

from __future__ import annotations

import pytest

from trading_bot_framework.broker import PaperBroker
from trading_bot_framework.models import Order, Side


def test_buy_reduces_cash_and_increases_position() -> None:
    broker = PaperBroker(cash=1_000.0)
    broker.update_price("ACME", 100.0)
    fill = broker.execute(Order("ACME", Side.BUY, 3.0))

    assert fill.price == 100.0
    assert broker.position("ACME") == 3.0
    assert broker.cash == pytest.approx(700.0)
    # Equity is unchanged by a fair-price trade (cash + marked position).
    assert broker.equity() == pytest.approx(1_000.0)


def test_sell_restores_cash() -> None:
    broker = PaperBroker(cash=1_000.0)
    broker.update_price("ACME", 100.0)
    broker.execute(Order("ACME", Side.BUY, 5.0))
    broker.update_price("ACME", 120.0)
    broker.execute(Order("ACME", Side.SELL, 5.0))

    assert broker.position("ACME") == 0.0
    assert broker.cash == pytest.approx(1_100.0)
    assert broker.equity() == pytest.approx(1_100.0)


def test_fee_rate_is_charged_on_both_sides() -> None:
    broker = PaperBroker(cash=1_000.0, fee_rate=0.01)
    broker.update_price("ACME", 100.0)
    broker.execute(Order("ACME", Side.BUY, 1.0))  # cost 100 + fee 1
    assert broker.cash == pytest.approx(899.0)


def test_cannot_oversell() -> None:
    broker = PaperBroker(cash=1_000.0)
    broker.update_price("ACME", 100.0)
    with pytest.raises(ValueError):
        broker.execute(Order("ACME", Side.SELL, 1.0))


def test_cannot_buy_without_cash() -> None:
    broker = PaperBroker(cash=50.0)
    broker.update_price("ACME", 100.0)
    with pytest.raises(ValueError):
        broker.execute(Order("ACME", Side.BUY, 1.0))


def test_execute_without_price_raises() -> None:
    broker = PaperBroker(cash=1_000.0)
    with pytest.raises(ValueError):
        broker.execute(Order("ACME", Side.BUY, 1.0))


def test_slippage_makes_buys_fill_higher() -> None:
    broker = PaperBroker(cash=1_000.0, slippage_rate=0.01)
    broker.update_price("ACME", 100.0)
    fill = broker.execute(Order("ACME", Side.BUY, 1.0))
    assert fill.price == pytest.approx(101.0)
    assert broker.cash == pytest.approx(899.0)


def test_slippage_makes_sells_fill_lower() -> None:
    broker = PaperBroker(cash=1_000.0, slippage_rate=0.02)
    broker.update_price("ACME", 100.0)
    broker.execute(Order("ACME", Side.BUY, 1.0))  # fills at 102
    broker.update_price("ACME", 100.0)
    fill = broker.execute(Order("ACME", Side.SELL, 1.0))
    assert fill.price == pytest.approx(98.0)


def test_negative_slippage_rejected() -> None:
    with pytest.raises(ValueError):
        PaperBroker(slippage_rate=-0.01)


def test_broker_tracks_multiple_symbols_independently() -> None:
    broker = PaperBroker(cash=10_000.0)
    broker.update_price("AAA", 100.0)
    broker.update_price("BBB", 50.0)
    broker.execute(Order("AAA", Side.BUY, 2.0))
    broker.execute(Order("BBB", Side.BUY, 4.0))
    assert broker.position("AAA") == 2.0
    assert broker.position("BBB") == 4.0
    # Equity: 10000 - 200 - 200 + 2*100 + 4*50 = 10000.
    assert broker.equity() == pytest.approx(10_000.0)
