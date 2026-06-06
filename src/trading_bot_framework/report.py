"""Human- and machine-readable backtest reports.

:class:`BacktestReport` turns a raw equity curve into the full slate of
performance metrics (return, CAGR, Sharpe, Sortino, drawdown, Calmar, ...) and
can render itself as a plain-text table, a ``dict`` for JSON, or a Rich table
for the CLI. Build one with :func:`build_report` from any
``BacktestResult``/``PortfolioResult``-like object exposing ``equity_curve``.

Part of Trading Bot Framework by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

from rich.table import Table

from trading_bot_framework import metrics


@dataclass(slots=True, frozen=True)
class BacktestReport:
    """A computed performance summary for one equity curve."""

    starting_equity: float
    final_equity: float
    total_return: float
    cagr: float
    volatility: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float
    num_bars: int
    num_fills: int

    def as_dict(self) -> dict[str, float | int]:
        """Return all fields as a plain dict (JSON-serialisable)."""
        return asdict(self)

    def as_rows(self) -> list[tuple[str, str]]:
        """Return ``(label, formatted_value)`` rows for tabular display."""
        return [
            ("Starting equity", f"${self.starting_equity:,.2f}"),
            ("Final equity", f"${self.final_equity:,.2f}"),
            ("Total return", f"{self.total_return * 100:+.2f}%"),
            ("CAGR", f"{self.cagr * 100:+.2f}%"),
            ("Volatility (ann.)", f"{self.volatility * 100:.2f}%"),
            ("Sharpe ratio", f"{self.sharpe:.2f}"),
            ("Sortino ratio", f"{self.sortino:.2f}"),
            ("Max drawdown", f"{self.max_drawdown * 100:.2f}%"),
            ("Calmar ratio", f"{self.calmar:.2f}"),
            ("Bars", str(self.num_bars)),
            ("Fills", str(self.num_fills)),
        ]

    def render_text(self) -> str:
        """Render the report as an aligned plain-text block."""
        rows = self.as_rows()
        width = max(len(label) for label, _ in rows)
        lines = [f"{label.ljust(width)} : {value}" for label, value in rows]
        return "\n".join(lines)

    def render_table(self, title: str = "Backtest Report") -> Table:
        """Render the report as a Rich table for terminal output."""
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        for label, value in self.as_rows():
            table.add_row(label, value)
        return table


def build_report(
    equity_curve: Sequence[float],
    num_fills: int,
    risk_free_rate: float = 0.0,
    periods_per_year: float = 252.0,
) -> BacktestReport:
    """Compute a :class:`BacktestReport` from an equity curve and fill count."""
    if not equity_curve:
        raise ValueError("equity_curve must not be empty")
    return BacktestReport(
        starting_equity=equity_curve[0],
        final_equity=equity_curve[-1],
        total_return=metrics.total_return(equity_curve),
        cagr=metrics.cagr(equity_curve, periods_per_year),
        volatility=metrics.volatility(equity_curve, periods_per_year),
        sharpe=metrics.sharpe_ratio(equity_curve, risk_free_rate, periods_per_year),
        sortino=metrics.sortino_ratio(equity_curve, risk_free_rate, periods_per_year),
        max_drawdown=metrics.max_drawdown(equity_curve),
        calmar=metrics.calmar_ratio(equity_curve, periods_per_year),
        num_bars=len(equity_curve),
        num_fills=num_fills,
    )
