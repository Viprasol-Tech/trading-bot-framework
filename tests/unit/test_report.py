"""Tests for the backtest report builder and renderers."""

from __future__ import annotations

import pytest
from rich.table import Table

from trading_bot_framework.report import BacktestReport, build_report


def test_build_report_basic_fields() -> None:
    curve = [100.0, 110.0, 121.0]
    report = build_report(curve, num_fills=3)
    assert isinstance(report, BacktestReport)
    assert report.starting_equity == 100.0
    assert report.final_equity == 121.0
    assert report.total_return == pytest.approx(0.21)
    assert report.num_bars == 3
    assert report.num_fills == 3


def test_build_report_rejects_empty_curve() -> None:
    with pytest.raises(ValueError):
        build_report([], num_fills=0)


def test_report_drawdown_is_non_positive() -> None:
    report = build_report([100.0, 120.0, 60.0, 90.0], num_fills=1)
    assert report.max_drawdown <= 0.0
    assert report.max_drawdown == pytest.approx(-0.5)


def test_as_dict_round_trips_all_fields() -> None:
    report = build_report([100.0, 105.0, 110.0], num_fills=2)
    payload = report.as_dict()
    assert payload["final_equity"] == 110.0
    assert payload["num_fills"] == 2
    assert set(payload) >= {"sharpe", "sortino", "calmar", "cagr", "volatility"}


def test_render_text_contains_key_labels() -> None:
    report = build_report([100.0, 110.0], num_fills=1)
    text = report.render_text()
    assert "Final equity" in text
    assert "Sharpe ratio" in text
    assert "Max drawdown" in text


def test_render_table_returns_rich_table() -> None:
    report = build_report([100.0, 110.0], num_fills=1)
    table = report.render_table(title="X")
    assert isinstance(table, Table)
    assert table.row_count == len(report.as_rows())


def test_as_rows_formats_percentages() -> None:
    report = build_report([100.0, 150.0], num_fills=1)
    rows = dict(report.as_rows())
    assert rows["Total return"] == "+50.00%"
