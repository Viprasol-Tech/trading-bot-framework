"""Deterministic synthetic price data for offline demos and tests.

Generates reproducible OHLC :class:`~trading_bot_framework.models.Bar` series
with no network, no API keys, and no randomness that varies across runs. Two
generators are provided: a smooth sinusoidal series (good for crossover demos)
and a seeded pseudo-random walk (good for stress-testing metrics).

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math

from trading_bot_framework.models import Bar


def sine_bars(
    n: int = 200,
    base: float = 100.0,
    symbol: str = "ACME",
    amplitude: float = 15.0,
) -> list[Bar]:
    """Build a wavy sinusoidal OHLC series of length ``n``."""
    if n <= 0:
        raise ValueError("n must be positive")
    bars: list[Bar] = []
    for i in range(n):
        close = base + amplitude * math.sin(i / 12.0) + 5.0 * math.sin(i / 3.0)
        bars.append(
            Bar(index=i, symbol=symbol, open=close, high=close + 1.0, low=close - 1.0, close=close)
        )
    return bars


def random_walk_bars(
    n: int = 200,
    base: float = 100.0,
    symbol: str = "ACME",
    seed: int = 1,
    step: float = 1.0,
) -> list[Bar]:
    """Build a seeded pseudo-random walk that always floats above zero.

    Uses a small deterministic linear-congruential generator so results are
    identical across machines and Python versions without importing ``random``.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if step <= 0:
        raise ValueError("step must be positive")
    bars: list[Bar] = []
    state = (seed * 2654435761 + 1) & 0xFFFFFFFF
    price = base
    for i in range(n):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        unit = state / 0x7FFFFFFF  # in [0, 1)
        delta = (unit - 0.5) * 2.0 * step
        price = max(1.0, price + delta)
        bars.append(
            Bar(index=i, symbol=symbol, open=price, high=price + 0.5, low=price - 0.5, close=price)
        )
    return bars
