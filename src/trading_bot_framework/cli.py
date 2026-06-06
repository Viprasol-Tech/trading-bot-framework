"""Command-line interface for Trading Bot Framework.

Subcommands (all run fully offline on synthetic data — no broker account, no
API keys, no network):

* ``version``     — print the installed version.
* ``strategies``  — list the built-in strategies.
* ``demo``        — quick SMA-cross backtest with a summary line.
* ``backtest``    — run any built-in strategy and print a full metrics report.
* ``portfolio``   — run a two-symbol portfolio sharing one capital pool.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import json as jsonlib

import typer
from rich.console import Console

from trading_bot_framework import __version__
from trading_bot_framework.backtest import backtest
from trading_bot_framework.data import sine_bars
from trading_bot_framework.portfolio import Allocation, backtest_portfolio
from trading_bot_framework.report import build_report
from trading_bot_framework.strategies import (
    BreakoutStrategy,
    MeanReversionStrategy,
    RsiStrategy,
    SmaCrossStrategy,
)
from trading_bot_framework.strategy import Strategy

app = typer.Typer(add_completion=False, help="Trading Bot Framework - by Viprasol Tech.")
console = Console()

_STRATEGIES: dict[str, str] = {
    "sma_cross": "Fast/slow simple-moving-average crossover (trend following).",
    "rsi": "RSI mean-reversion: buy oversold, sell overbought.",
    "breakout": "Donchian-channel breakout of an N-bar high (trend following).",
    "mean_reversion": "Bollinger-band fade of price extremes back to the mean.",
}


def _build_strategy(name: str, quantity: float) -> Strategy:
    """Construct a built-in strategy by name with sensible defaults."""
    if name == "sma_cross":
        return SmaCrossStrategy(quantity=quantity)
    if name == "rsi":
        return RsiStrategy(quantity=quantity)
    if name == "breakout":
        return BreakoutStrategy(quantity=quantity)
    if name == "mean_reversion":
        return MeanReversionStrategy(quantity=quantity)
    raise typer.BadParameter(f"unknown strategy {name!r}; try one of {', '.join(_STRATEGIES)}")


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"trading-bot-framework [bold cyan]{__version__}[/] - by Viprasol Tech")


@app.command()
def strategies() -> None:
    """List the built-in strategies and a one-line description of each."""
    for name, desc in _STRATEGIES.items():
        console.print(f"[bold]{name:<15}[/] {desc}")


@app.command()
def demo(
    fast: int = typer.Option(5, help="Fast SMA window."),
    slow: int = typer.Option(20, help="Slow SMA window."),
) -> None:
    """Backtest the SMA-cross strategy on synthetic data and print stats."""
    bars = sine_bars()
    strategy = SmaCrossStrategy(fast=fast, slow=slow, quantity=10.0)
    result = backtest(strategy, bars, starting_cash=10_000.0)

    console.print(f"Strategy:      [bold]{strategy.name}[/] (fast={fast}, slow={slow})")
    console.print(f"Bars:          {len(bars)}")
    console.print(f"Fills:         {result.num_fills}")
    console.print(f"Final equity:  [bold green]${result.final_equity:,.2f}[/]")
    console.print(f"Total return:  [bold]{result.total_return * 100:+.2f}%[/]")
    console.print(f"Max drawdown:  {result.max_drawdown * 100:.2f}%")


@app.command(name="backtest")
def backtest_cmd(
    strategy: str = typer.Option(
        "sma_cross", help="One of: sma_cross, rsi, breakout, mean_reversion."
    ),
    bars: int = typer.Option(250, help="Number of synthetic bars."),
    cash: float = typer.Option(10_000.0, help="Starting cash."),
    quantity: float = typer.Option(10.0, help="Order size per signal."),
    fee_rate: float = typer.Option(0.0, help="Proportional commission per trade."),
    slippage_rate: float = typer.Option(0.0, help="Proportional slippage per trade."),
    json: bool = typer.Option(False, "--json", help="Emit the report as JSON."),
) -> None:
    """Run a built-in strategy and print a full performance report."""
    strat = _build_strategy(strategy, quantity)
    series = sine_bars(n=bars)
    result = backtest(
        strat, series, starting_cash=cash, fee_rate=fee_rate, slippage_rate=slippage_rate
    )
    report = build_report(result.equity_curve, result.num_fills)

    if json:
        console.print_json(jsonlib.dumps(report.as_dict()))
        return
    console.print(report.render_table(title=f"Backtest: {strat.name}"))


@app.command()
def portfolio(
    cash: float = typer.Option(20_000.0, help="Shared starting cash."),
    quantity: float = typer.Option(5.0, help="Order size per signal."),
    fee_rate: float = typer.Option(0.0, help="Proportional commission per trade."),
    slippage_rate: float = typer.Option(0.0, help="Proportional slippage per trade."),
    json: bool = typer.Option(False, "--json", help="Emit the report as JSON."),
) -> None:
    """Backtest a two-symbol portfolio (SMA-cross + RSI) on one capital pool."""
    allocations = [
        Allocation("AAA", SmaCrossStrategy(quantity=quantity), sine_bars(n=250, symbol="AAA")),
        Allocation(
            "BBB",
            RsiStrategy(quantity=quantity),
            sine_bars(n=250, symbol="BBB", base=80.0, amplitude=20.0),
        ),
    ]
    result = backtest_portfolio(
        allocations, starting_cash=cash, fee_rate=fee_rate, slippage_rate=slippage_rate
    )
    report = build_report(result.equity_curve, result.num_fills)

    if json:
        payload = report.as_dict() | {"fills_by_symbol": result.fills_by_symbol}
        console.print_json(jsonlib.dumps(payload))
        return
    console.print(report.render_table(title="Portfolio: AAA (sma_cross) + BBB (rsi)"))
    for symbol, count in result.fills_by_symbol.items():
        console.print(f"  {symbol}: {count} fills")


if __name__ == "__main__":
    app()
