"""Tests for the synthetic data generators and the Typer CLI."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from trading_bot_framework import __version__
from trading_bot_framework.cli import app
from trading_bot_framework.data import random_walk_bars, sine_bars

runner = CliRunner()


# --- data generators --------------------------------------------------------


def test_sine_bars_length_and_symbol() -> None:
    bars = sine_bars(n=50, symbol="XYZ")
    assert len(bars) == 50
    assert all(b.symbol == "XYZ" for b in bars)
    assert all(b.high >= b.close >= b.low for b in bars)


def test_sine_bars_is_deterministic() -> None:
    assert [b.close for b in sine_bars(n=20)] == [b.close for b in sine_bars(n=20)]


def test_random_walk_is_seeded_and_positive() -> None:
    a = [b.close for b in random_walk_bars(n=100, seed=7)]
    b = [b.close for b in random_walk_bars(n=100, seed=7)]
    c = [b.close for b in random_walk_bars(n=100, seed=8)]
    assert a == b  # same seed -> identical
    assert a != c  # different seed -> different
    assert all(x > 0.0 for x in a)


def test_data_rejects_bad_n() -> None:
    with pytest.raises(ValueError):
        sine_bars(n=0)
    with pytest.raises(ValueError):
        random_walk_bars(n=0)


# --- CLI --------------------------------------------------------------------


def test_cli_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_strategies_lists_all() -> None:
    result = runner.invoke(app, ["strategies"])
    assert result.exit_code == 0
    for name in ("sma_cross", "rsi", "breakout", "mean_reversion"):
        assert name in result.stdout


def test_cli_demo_runs() -> None:
    result = runner.invoke(app, ["demo", "--fast", "4", "--slow", "12"])
    assert result.exit_code == 0
    assert "Final equity" in result.stdout


def test_cli_backtest_json_is_valid() -> None:
    result = runner.invoke(app, ["backtest", "--strategy", "rsi", "--bars", "120", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "sharpe" in payload
    assert "final_equity" in payload


def test_cli_backtest_rejects_unknown_strategy() -> None:
    result = runner.invoke(app, ["backtest", "--strategy", "nope"])
    assert result.exit_code != 0


def test_cli_portfolio_json_has_fills_by_symbol() -> None:
    result = runner.invoke(app, ["portfolio", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "fills_by_symbol" in payload
    assert set(payload["fills_by_symbol"]) == {"AAA", "BBB"}
