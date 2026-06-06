"""Tests for the technical-indicator helpers."""

from __future__ import annotations

import pytest

from trading_bot_framework.indicators import (
    ema,
    rolling_max,
    rolling_min,
    rsi,
    sma,
    stddev,
)


def test_sma_needs_full_window() -> None:
    assert sma([1.0, 2.0], 3) is None
    assert sma([1.0, 2.0, 3.0], 3) == pytest.approx(2.0)
    assert sma([2.0, 4.0, 6.0, 8.0], 2) == pytest.approx(7.0)


def test_sma_rejects_nonpositive_window() -> None:
    with pytest.raises(ValueError):
        sma([1.0], 0)


def test_ema_warms_up_then_tracks() -> None:
    assert ema([1.0, 2.0], 3) is None
    # Flat series -> EMA equals the constant value.
    assert ema([5.0, 5.0, 5.0, 5.0, 5.0], 3) == pytest.approx(5.0)


def test_ema_reacts_faster_than_sma_on_a_jump() -> None:
    values = [10.0] * 10 + [20.0]
    fast = ema(values, 3)
    slow = sma(values, 5)
    assert fast is not None and slow is not None
    assert fast > slow  # EMA weights the recent jump more heavily


def test_rsi_all_gains_is_100() -> None:
    rising = [float(i) for i in range(1, 20)]
    assert rsi(rising, 14) == pytest.approx(100.0)


def test_rsi_all_losses_is_0() -> None:
    falling = [float(i) for i in range(20, 1, -1)]
    assert rsi(falling, 14) == pytest.approx(0.0)


def test_rsi_needs_period_plus_one() -> None:
    assert rsi([1.0] * 14, 14) is None
    assert rsi([1.0] * 15, 14) is not None


def test_rsi_midrange_for_choppy_series() -> None:
    values = [
        10.0,
        11.0,
        10.0,
        11.0,
        10.0,
        11.0,
        10.0,
        11.0,
        10.0,
        11.0,
        10.0,
        11.0,
        10.0,
        11.0,
        10.0,
    ]
    value = rsi(values, 14)
    assert value is not None
    assert 0.0 < value < 100.0


def test_rolling_max_and_min() -> None:
    assert rolling_max([1.0, 5.0, 3.0], 2) == 5.0
    assert rolling_min([1.0, 5.0, 3.0], 2) == 3.0
    assert rolling_max([1.0], 2) is None


def test_stddev_of_constant_is_zero() -> None:
    assert stddev([4.0, 4.0, 4.0], 3) == pytest.approx(0.0)


def test_stddev_known_value() -> None:
    # Population std of [2,4,4,4,5,5,7,9] is 2.0
    assert stddev([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0], 8) == pytest.approx(2.0)


def test_stddev_requires_window_gt_one() -> None:
    with pytest.raises(ValueError):
        stddev([1.0, 2.0], 1)
