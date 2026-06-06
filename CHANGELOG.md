# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[SemVer](https://semver.org/).

## [0.2.0] - 2025

### Added
- `indicators` module: `sma`, `ema`, `rsi` (Wilder), `rolling_max`,
  `rolling_min`, and `stddev` — pure-Python, NumPy-free, warm-up aware.
- Three new built-in strategies: `RsiStrategy` (mean-reversion on RSI),
  `BreakoutStrategy` (Donchian-channel breakout), and `MeanReversionStrategy`
  (Bollinger-band fade).
- `metrics` module: total return, CAGR, annualised volatility, Sharpe, Sortino,
  max drawdown, and Calmar ratio.
- `report` module with `BacktestReport` and `build_report` — render results as
  plain text, a JSON-ready dict, or a Rich table.
- `portfolio` module: `PortfolioEngine` and `backtest_portfolio` run multiple
  symbol/strategy allocations against one shared capital pool in lock-step.
- `data` module: deterministic synthetic series (`sine_bars`, seeded
  `random_walk_bars`) for offline demos and tests.
- Slippage modelling in `PaperBroker` via `slippage_rate` (works against the
  trader on both sides); `backtest`/`backtest_portfolio` now accept it.
- CLI subcommands: `strategies`, `backtest`, and `portfolio` (with `--json`),
  alongside the existing `version` and `demo`.

### Changed
- `PaperBroker` is now explicitly multi-symbol with per-symbol position tracking.
- Bumped version to 0.2.0.

## [0.1.0] - 2025

### Added
- Initial release of trading-bot-framework: Generic strategy-runner trading bot framework with backtesting.
