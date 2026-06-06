"""Tests for the performance-metrics module."""

from __future__ import annotations

import pytest

from trading_bot_framework import metrics


def test_returns_length_and_values() -> None:
    rets = metrics.returns([100.0, 110.0, 99.0])
    assert len(rets) == 2
    assert rets[0] == pytest.approx(0.10)
    assert rets[1] == pytest.approx(-0.10)


def test_returns_handles_nonpositive_prior() -> None:
    assert metrics.returns([0.0, 10.0]) == [0.0]


def test_total_return() -> None:
    assert metrics.total_return([100.0, 150.0]) == pytest.approx(0.5)
    assert metrics.total_return([100.0]) == 0.0


def test_cagr_doubling_over_one_year() -> None:
    curve = [100.0] + [100.0] * 251 + [200.0]
    # 252 returns over 252 trading days == ~1 year, doubling -> ~100% CAGR.
    value = metrics.cagr(curve, periods_per_year=252.0)
    assert value == pytest.approx(1.0, abs=0.02)


def test_cagr_degenerate_returns_zero() -> None:
    assert metrics.cagr([100.0]) == 0.0
    assert metrics.cagr([-1.0, 50.0]) == 0.0


def test_max_drawdown_known() -> None:
    # Peak 120 then trough 60 -> -50% drawdown.
    assert metrics.max_drawdown([100.0, 120.0, 60.0, 90.0]) == pytest.approx(-0.5)


def test_max_drawdown_monotonic_is_zero() -> None:
    assert metrics.max_drawdown([1.0, 2.0, 3.0, 4.0]) == pytest.approx(0.0)


def test_volatility_flat_is_zero() -> None:
    assert metrics.volatility([100.0, 100.0, 100.0]) == pytest.approx(0.0)


def test_volatility_positive_for_choppy() -> None:
    assert metrics.volatility([100.0, 110.0, 100.0, 110.0]) > 0.0


def test_sharpe_flat_curve_is_zero() -> None:
    assert metrics.sharpe_ratio([100.0, 100.0, 100.0]) == 0.0


def test_sharpe_positive_for_steady_gains() -> None:
    curve = [100.0 * (1.01**i) for i in range(50)]
    assert metrics.sharpe_ratio(curve) > 0.0


def test_sortino_zero_without_downside() -> None:
    # A monotonically rising curve has no downside deviation -> 0.0 by guard.
    curve = [100.0 * (1.005**i) for i in range(50)]
    assert metrics.sortino_ratio(curve) == 0.0


def test_sortino_exceeds_sharpe_when_upside_dominates() -> None:
    # Mostly-up curve with occasional small dips: downside dev < total dev,
    # so Sortino should be the larger (more favourable) ratio.
    curve = [100.0]
    for i in range(1, 60):
        curve.append(curve[-1] * (0.99 if i % 5 == 0 else 1.02))
    assert metrics.sortino_ratio(curve) > metrics.sharpe_ratio(curve) > 0.0


def test_calmar_zero_without_drawdown() -> None:
    assert metrics.calmar_ratio([1.0, 2.0, 3.0]) == 0.0


def test_calmar_positive_with_recovery() -> None:
    curve = [100.0, 120.0, 90.0, 200.0]
    assert metrics.calmar_ratio(curve) != 0.0


def test_periods_per_year_must_be_positive() -> None:
    with pytest.raises(ValueError):
        metrics.cagr([100.0, 110.0], periods_per_year=0.0)
