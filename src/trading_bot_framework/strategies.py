"""Built-in example strategies.

Each strategy is pure decision logic over a
:class:`~trading_bot_framework.strategy.Context`:

* :class:`SmaCrossStrategy` — classic fast/slow moving-average crossover.
* :class:`RsiStrategy` — buy oversold, sell overbought (mean-reversion on RSI).
* :class:`BreakoutStrategy` — Donchian-style breakout of an N-bar high.
* :class:`MeanReversionStrategy` — Bollinger-style fade of price extremes.

All are long-only and position-aware so they round-trip cleanly in backtests.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from trading_bot_framework.indicators import (
    rolling_max,
    rolling_min,
    rsi,
    sma,
    stddev,
)
from trading_bot_framework.models import Order
from trading_bot_framework.strategy import Context, Strategy

__all__ = [
    "BreakoutStrategy",
    "MeanReversionStrategy",
    "RsiStrategy",
    "SmaCrossStrategy",
    "sma",
]


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


class RsiStrategy(Strategy):
    """Long-only RSI mean-reversion strategy.

    Enters when RSI falls to or below ``lower`` (oversold) and the book is flat,
    and exits the whole position when RSI rises to or above ``upper``
    (overbought). A common 14-period / 30-70 configuration is the default.
    """

    name = "rsi"

    def __init__(
        self,
        period: int = 14,
        lower: float = 30.0,
        upper: float = 70.0,
        quantity: float = 1.0,
    ) -> None:
        if period <= 0:
            raise ValueError("period must be positive")
        if not 0.0 < lower < upper < 100.0:
            raise ValueError("require 0 < lower < upper < 100")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.period = period
        self.lower = lower
        self.upper = upper
        self.quantity = quantity

    def on_bar(self, ctx: Context) -> list[Order]:
        """Buy when oversold and flat; sell the position when overbought."""
        value = rsi(ctx.closes(), self.period)
        if value is None:
            return []
        if value <= self.lower and ctx.position == 0.0:
            return [ctx.buy(self.quantity)]
        if value >= self.upper and ctx.position > 0.0:
            return [ctx.sell(ctx.position)]
        return []


class BreakoutStrategy(Strategy):
    """Donchian-channel breakout strategy (long-only).

    Buys when the latest close breaks above the highest close of the prior
    ``lookback`` bars, and exits when the close breaks below the lowest close of
    the prior ``exit_lookback`` bars. This is a trend-following entry, the
    opposite intent of the RSI/mean-reversion strategies.
    """

    name = "breakout"

    def __init__(
        self,
        lookback: int = 20,
        exit_lookback: int = 10,
        quantity: float = 1.0,
    ) -> None:
        if lookback <= 1 or exit_lookback <= 1:
            raise ValueError("lookbacks must be greater than 1")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.lookback = lookback
        self.exit_lookback = exit_lookback
        self.quantity = quantity

    def on_bar(self, ctx: Context) -> list[Order]:
        """Enter on an upside breakout, exit on a downside breakdown."""
        closes = ctx.closes()
        if not closes:
            return []
        price = closes[-1]
        prior = closes[:-1]

        if ctx.position == 0.0:
            high = rolling_max(prior, self.lookback)
            if high is not None and price > high:
                return [ctx.buy(self.quantity)]
            return []

        low = rolling_min(prior, self.exit_lookback)
        if low is not None and price < low:
            return [ctx.sell(ctx.position)]
        return []


class MeanReversionStrategy(Strategy):
    """Bollinger-band mean-reversion strategy (long-only).

    Buys when the close falls more than ``num_std`` standard deviations below
    its ``window``-bar moving average, and exits once price reverts back to (or
    above) the moving average. Profits from prices snapping back to the mean.
    """

    name = "mean_reversion"

    def __init__(
        self,
        window: int = 20,
        num_std: float = 2.0,
        quantity: float = 1.0,
    ) -> None:
        if window <= 1:
            raise ValueError("window must be greater than 1")
        if num_std <= 0:
            raise ValueError("num_std must be positive")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.window = window
        self.num_std = num_std
        self.quantity = quantity

    def on_bar(self, ctx: Context) -> list[Order]:
        """Buy oversized dips below the band; exit on reversion to the mean."""
        closes = ctx.closes()
        mean = sma(closes, self.window)
        sd = stddev(closes, self.window)
        if mean is None or sd is None:
            return []
        price = closes[-1]
        lower_band = mean - self.num_std * sd

        if ctx.position == 0.0 and price < lower_band:
            return [ctx.buy(self.quantity)]
        if ctx.position > 0.0 and price >= mean:
            return [ctx.sell(ctx.position)]
        return []
