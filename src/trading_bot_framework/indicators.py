"""Pure-Python technical indicators used by the built-in strategies.

Every function works on a plain ``list[float]`` of closing prices (oldest
first) and returns ``None`` until enough data is available, so callers can
cleanly distinguish "warming up" from a real reading. Keeping indicators free
of NumPy makes them trivial to unit-test and cheap in tight backtest loops.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations


def sma(values: list[float], window: int) -> float | None:
    """Return the simple moving average of the last ``window`` values.

    Returns ``None`` until at least ``window`` values are available.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def ema(values: list[float], window: int) -> float | None:
    """Return the exponential moving average of ``values``.

    Seeded with the SMA of the first ``window`` points, then smoothed with the
    standard ``2 / (window + 1)`` factor. Returns ``None`` while warming up.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        return None
    k = 2.0 / (window + 1.0)
    seed = sum(values[:window]) / window
    out = seed
    for value in values[window:]:
        out = value * k + out * (1.0 - k)
    return out


def rsi(values: list[float], period: int = 14) -> float | None:
    """Return Wilder's Relative Strength Index in the 0..100 range.

    Needs ``period + 1`` closes to produce the first reading. A flat series
    (no losses) returns 100.0; an all-down series returns 0.0.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period + 1:
        return None

    # Initial average gain/loss over the first `period` deltas.
    deltas = [values[i + 1] - values[i] for i in range(period)]
    avg_gain = sum(d for d in deltas if d > 0) / period
    avg_loss = sum(-d for d in deltas if d < 0) / period

    # Wilder smoothing over the remaining deltas.
    for i in range(period, len(values) - 1):
        delta = values[i + 1] - values[i]
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0.0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def rolling_max(values: list[float], window: int) -> float | None:
    """Return the highest of the last ``window`` values, or ``None`` if short."""
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        return None
    return max(values[-window:])


def rolling_min(values: list[float], window: int) -> float | None:
    """Return the lowest of the last ``window`` values, or ``None`` if short."""
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        return None
    return min(values[-window:])


def stddev(values: list[float], window: int) -> float | None:
    """Population standard deviation of the last ``window`` values."""
    if window <= 1:
        raise ValueError("window must be greater than 1")
    if len(values) < window:
        return None
    window_vals = values[-window:]
    mean = sum(window_vals) / window
    var = sum((v - mean) ** 2 for v in window_vals) / window
    return float(var**0.5)
