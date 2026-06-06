"""Performance metrics computed from an equity curve.

All functions take a list of equity values (one per bar/period, oldest first)
and return plain floats so they compose cleanly into a
:class:`~trading_bot_framework.report.BacktestReport`. They are pure and
NumPy-free, which keeps them deterministic and easy to assert against in tests.

Conventions:

* ``periods_per_year`` annualises returns and volatility. Use ``252`` for daily
  bars, ``52`` for weekly, ``12`` for monthly, etc.
* ``risk_free_rate`` is the *per-period* risk-free return (default 0).

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence


def returns(equity_curve: Sequence[float]) -> list[float]:
    """Simple period-over-period returns of the equity curve.

    Output length is ``len(equity_curve) - 1``. A zero (or negative) prior
    value yields a 0.0 return for that step rather than dividing by zero.
    """
    out: list[float] = []
    for prev, cur in zip(equity_curve, list(equity_curve)[1:], strict=False):
        if prev <= 0:
            out.append(0.0)
        else:
            out.append(cur / prev - 1.0)
    return out


def total_return(equity_curve: Sequence[float]) -> float:
    """Fractional return from first to last equity value (0.10 == +10%)."""
    if len(equity_curve) < 2 or equity_curve[0] == 0.0:
        return 0.0
    return equity_curve[-1] / equity_curve[0] - 1.0


def cagr(equity_curve: Sequence[float], periods_per_year: float = 252.0) -> float:
    """Compound annual growth rate implied by the curve.

    Returns 0.0 for degenerate curves (fewer than two points, non-positive
    endpoints) so it never raises in a reporting pipeline.
    """
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    n = len(equity_curve)
    if n < 2:
        return 0.0
    start, end = equity_curve[0], equity_curve[-1]
    if start <= 0 or end <= 0:
        return 0.0
    years = (n - 1) / periods_per_year
    if years <= 0:
        return 0.0
    return float((end / start) ** (1.0 / years) - 1.0)


def volatility(equity_curve: Sequence[float], periods_per_year: float = 252.0) -> float:
    """Annualised standard deviation of period returns."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    rets = returns(equity_curve)
    if len(rets) < 2:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return float((var**0.5) * (periods_per_year**0.5))


def sharpe_ratio(
    equity_curve: Sequence[float],
    risk_free_rate: float = 0.0,
    periods_per_year: float = 252.0,
) -> float:
    """Annualised Sharpe ratio of the equity curve.

    Returns 0.0 when there is no return dispersion (flat curve) to avoid a
    division by zero.
    """
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    rets = returns(equity_curve)
    if len(rets) < 2:
        return 0.0
    excess = [r - risk_free_rate for r in rets]
    mean = sum(excess) / len(excess)
    var = sum((r - mean) ** 2 for r in excess) / (len(excess) - 1)
    sd = var**0.5
    if sd == 0.0:
        return 0.0
    return float((mean / sd) * (periods_per_year**0.5))


def sortino_ratio(
    equity_curve: Sequence[float],
    risk_free_rate: float = 0.0,
    periods_per_year: float = 252.0,
) -> float:
    """Annualised Sortino ratio (downside-deviation flavoured Sharpe)."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    rets = returns(equity_curve)
    if len(rets) < 2:
        return 0.0
    excess = [r - risk_free_rate for r in rets]
    mean = sum(excess) / len(excess)
    downside = [min(0.0, r) for r in excess]
    dvar = sum(d**2 for d in downside) / len(downside)
    dd = dvar**0.5
    if dd == 0.0:
        return 0.0
    return float((mean / dd) * (periods_per_year**0.5))


def max_drawdown(equity_curve: Sequence[float]) -> float:
    """Largest peak-to-trough decline as a non-positive fraction (-0.2 == -20%)."""
    peak = float("-inf")
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def calmar_ratio(equity_curve: Sequence[float], periods_per_year: float = 252.0) -> float:
    """CAGR divided by the magnitude of max drawdown.

    Returns 0.0 when there is no drawdown (no risk denominator).
    """
    mdd = max_drawdown(equity_curve)
    if mdd == 0.0:
        return 0.0
    return cagr(equity_curve, periods_per_year) / abs(mdd)
