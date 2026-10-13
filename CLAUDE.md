# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Python 3.12, managed by uv. `./setup.sh` runs `uv sync` and installs the commit-msg hook.

```bash
uv run pytest                                   # all tests (pytest runs unittest-style *_test.py files)
uv run pytest test/components/uwqsc/market_data # one brick
uv run pytest -k test_second_sync               # one test
uv run poly check                               # Polylith boundaries; CI fails if this fails
uv run poly deps                                # brick dependency matrix

# lint exactly as CI does (CI fails below 7.0; PR template expects >= 8.0)
uv run pylint --fail-under=7.0 --max-args=10 --max-positional-arguments=10 --max-attributes=10 components bases test development

uv run uwqsc --help                             # CLI (sync, sync-sentiment, list-algorithms, backtest)
uv run streamlit run bases/uwqsc/dashboard/app.py
```

Tests import shared fakes from `test/support/uwqsc_test_fakes.py` (on the pytest path). Tests must
not hit the network: `yfinance` is imported lazily inside `YFinanceDataSourceImpl` methods.

## Architecture

Polylith workspace, namespace `uwqsc`, loose theme. Each brick's `__init__.py` is its public API;
import other bricks through it (`from uwqsc.market_data import MarketDataService`).

Dependency rules (enforced by review and visible in `poly deps`):
- `common` ← `algorithm_core` ← `algorithms`
- `common`, `storage` ← `market_data`; `common`, `storage` ← `sentiment`
- `backtesting` → `algorithm_core`, `market_data`, `sentiment`. It never imports a concrete strategy.
- Bases (`cli`, `dashboard`) → `backtesting` + `algorithms`; importing `uwqsc.algorithms` is what
  fills the registry.
- `market_data` and `sentiment` never import each other or any algorithm brick.

Key pieces:
- **storage**: owns the one SQLite file (`DEFAULT_DB_PATH`, env `UWQSC_DB_PATH`). Bricks register
  their DDL with `register_migration(owner, version, sql)` at import time; `connect()` applies
  pending ones. Never edit a released migration; add a new version.
- **algorithm_core**: `IAlgorithm` has class attributes `DEFAULT_PARAMETERS` (merged under caller
  parameters via `merge_parameters`) and `REQUIRED_FEATURES` (`"price"`, `"sentiment"`). The registry
  (`register_algorithm`, `create_algorithm`, `list_algorithms`) finds algorithms by key.
  `IPreProcessData.process_data(df)` is a template method: `missing_values()` →
  `remove_duplicate_timestamps()` → `remove_outliers()`, mutating `__processed_data__` /
  `__data_history__` in place.
- **market_data**: `MarketDataService.sync` is incremental (fetches from the day after each ticker's
  latest stored bar; up-to-date tickers are skipped; metadata refresh is best-effort).
- **sentiment**: scores are `emotional` and `logical` in [-1, 1] plus `volume`. A row's `date` is the
  trading day by whose 16:00 New York close the items were published (`as_of_trading_date`). This
  prevents look-ahead, so `SnapshotBuilder` joins on date with no shift. Only `NullSentimentSource`
  exists today.
- **dashboard**: `app.py` only sets up `st.navigation`; each page is a plain script in `app_pages/`
  (no `pages/`, which Streamlit auto-discovers). Hackathon-parquet loading and the company/month
  picker are shared via `uwqsc.dashboard.hackathon`. Prefer native charts (`st.line_chart`) over
  matplotlib. Headless page tests: `streamlit.testing.v1.AppTest.from_file(".../app.py")` +
  `switch_page("app_pages/<page>.py")`.
- **backtesting**: `SnapshotBuilder` builds the per-date frame for exactly the features an algorithm
  requires. `IBacktestingFramework.run()` feeds one 1-row snapshot per step to `execute_trade` and
  books the returned `{ticker: cost}` in a `Portfolio` (cash -= cost, shares += cost/price, equity
  marked to market). `sweep()` ranks runs by final equity; failing runs are kept with an `error`.

Conventions:
- **One market snapshot per call.** Algorithms that need history keep it themselves (preprocessor
  `__data_history__` or algorithm state).
- **Snapshot columns** are per ticker: `{t}_price`, `{t}_volume`, and with sentiment
  `{t}_sent_emotional`, `{t}_sent_logical`, `{t}_sent_volume`. Algorithms add their own, such as
  `{t}_short`, `{t}_long`.
- Instance "private" state uses dunder-wrapped names (`self.__positions__`); these are not
  name-mangled, so tests set them directly.
- `execute_trade` returns trade value per ticker (`shares * price`): positive buys, negative sells/shorts.
- Abstract methods raise `INTERFACE_NOT_IMPLEMENTED_ERROR` from `uwqsc.common`.
- Tests are `unittest.TestCase` classes with a docstring on every test, in files ending `_test.py`.

## Git / PR conventions

- Every commit message must contain a line consisting solely of `topic/#<issue>` (enforced by the
  commit-msg hook, regex `^topic/#[0-9]*$`).
- Branches are named `topic/<issue_number>`. Changes reach `main` only via PRs; use the
  `Ready for Review` / `Ready for Merge` labels and request `algo-trading-team` for review.
