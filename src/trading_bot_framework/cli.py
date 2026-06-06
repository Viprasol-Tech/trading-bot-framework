"""Command-line interface for Trading Bot Framework.

``trading-bot-framework demo`` backtests the built-in SMA-crossover strategy on
a synthetic price series — no broker account, no API keys, no network.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math

import typer
from rich.console import Console

from trading_bot_framework import __version__
from trading_bot_framework.backtest import backtest
from trading_bot_framework.models import Bar
from trading_bot_framework.strategies import SmaCrossStrategy

app = typer.Typer(add_completion=False, help="Trading Bot Framework — by Viprasol Tech.")
console = Console()


def _synthetic_bars(n: int = 200, base: float = 100.0, symbol: str = "ACME") -> list[Bar]:
    """Build a wavy synthetic OHLC series for offline demos and tests."""
    bars: list[Bar] = []
    for i in range(n):
        close = base + 15.0 * math.sin(i / 12.0) + 5.0 * math.sin(i / 3.0)
        high = close + 1.0
        low = close - 1.0
        bars.append(Bar(index=i, symbol=symbol, open=close, high=high, low=low, close=close))
    return bars


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"trading-bot-framework [bold cyan]{__version__}[/] — by Viprasol Tech")


@app.command()
def demo(
    fast: int = typer.Option(5, help="Fast SMA window."),
    slow: int = typer.Option(20, help="Slow SMA window."),
) -> None:
    """Backtest the SMA-cross strategy on synthetic data and print stats."""
    bars = _synthetic_bars()
    strategy = SmaCrossStrategy(fast=fast, slow=slow, quantity=10.0)
    result = backtest(strategy, bars, starting_cash=10_000.0)

    console.print(f"Strategy:      [bold]{strategy.name}[/] (fast={fast}, slow={slow})")
    console.print(f"Bars:          {len(bars)}")
    console.print(f"Fills:         {result.num_fills}")
    console.print(f"Final equity:  [bold green]${result.final_equity:,.2f}[/]")
    console.print(f"Total return:  [bold]{result.total_return * 100:+.2f}%[/]")
    console.print(f"Max drawdown:  {result.max_drawdown * 100:.2f}%")


if __name__ == "__main__":
    app()
