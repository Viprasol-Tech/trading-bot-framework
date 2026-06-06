"""Built-in example strategies.

:class:`SmaCrossStrategy` is a classic moving-average crossover: go long when
the fast SMA crosses above the slow SMA, flatten when it crosses back below. It
demonstrates how to use the :class:`~trading_bot_framework.strategy.Context`
history and position helpers to write a complete, position-aware strategy.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from trading_bot_framework.models import Order
from trading_bot_framework.strategy import Context, Strategy


def sma(values: list[float], window: int) -> float | None:
    """Return the simple moving average of the last ``window`` values.

    Returns ``None`` until at least ``window`` values are available, so callers
    can distinguish "not enough data yet" from a real average.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


class SmaCrossStrategy(Strategy):
    """Long-only SMA crossover strategy.

    Buys ``quantity`` units when the fast SMA rises above the slow SMA and the
    book is flat; sells the whole position when the fast SMA drops back below
    the slow SMA. Signals are evaluated on bar closes.
    """

    name = "sma_cross"

    def __init__(self, fast: int = 5, slow: int = 20, quantity: float = 1.0) -> None:
        if fast >= slow:
            raise ValueError("fast window must be shorter than slow window")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.fast = fast
        self.slow = slow
        self.quantity = quantity

    def on_bar(self, ctx: Context) -> list[Order]:
        """Emit a buy on a bullish cross and a sell on a bearish cross."""
        closes = ctx.closes()
        fast_now = sma(closes, self.fast)
        slow_now = sma(closes, self.slow)
        fast_prev = sma(closes[:-1], self.fast)
        slow_prev = sma(closes[:-1], self.slow)
        if None in (fast_now, slow_now, fast_prev, slow_prev):
            return []
        assert fast_now is not None and slow_now is not None
        assert fast_prev is not None and slow_prev is not None

        crossed_up = fast_prev <= slow_prev and fast_now > slow_now
        crossed_down = fast_prev >= slow_prev and fast_now < slow_now

        if crossed_up and ctx.position == 0.0:
            return [ctx.buy(self.quantity)]
        if crossed_down and ctx.position > 0.0:
            return [ctx.sell(ctx.position)]
        return []
