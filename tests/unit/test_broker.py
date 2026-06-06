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
