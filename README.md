# UWQSC

The University of Waterloo Quantitative Analysis Stocks Club monorepo. It holds algorithmic
trading strategies, the backtesting framework, the market data layer and crowd sentiment
analysis, organised as a [Polylith](https://davidvujic.github.io/python-polylith-docs/) workspace.

Project Board: https://github.com/orgs/UWQSC/projects/1

## Setup

Install [uv](https://docs.astral.sh/uv/), then:

```bash
./setup.sh        # uv sync (Python 3.12 + all deps into .venv) and installs the commit-msg hook
```

## Layout

| Brick | Kind | What it does |
| --- | --- | --- |
| `common` | component | Shared constants (`INTERFACE_NOT_IMPLEMENTED_ERROR`) |
| `storage` | component | The single SQLite DB: path, connections, per-brick migrations |
| `algorithm_core` | component | `IAlgorithm`, `IPreProcessData`, `StockPosition`, algorithm registry |
| `algorithms` | component | Strategies, one subpackage each (`sma/`, `hmm/`) |
| `market_data` | component | yfinance source, SQLite store, incremental sync |
| `sentiment` | component | Emotional/logical crowd sentiment per ticker, aligned to market close |
| `backtesting` | component | Snapshot assembly, `Portfolio` accounting, backtests and sweeps |
| `cli` | base | `uwqsc` command line |
| `dashboard` | base | Streamlit app |

Code lives in `components/uwqsc/<brick>/` and `bases/uwqsc/<brick>/`, tests in `test/`, and the
deployable package is `projects/backtester`. Everything imports as `uwqsc.<brick>`.

## Usage

```bash
uv run uwqsc sync --tickers AAPL MSFT --start 2023-01-01         # incremental: re-runs fetch only new days
uv run uwqsc sync-sentiment --tickers AAPL MSFT --start 2023-01-01   # neutral placeholder source for now
uv run uwqsc list-algorithms
uv run uwqsc backtest --algo sma --tickers AAPL MSFT --start 2023-01-01 --param short_window=20
uv run streamlit run bases/uwqsc/dashboard/app.py
```

The database defaults to `~/.uwqsc/uwqsc.sqlite`; override with `--db` or `UWQSC_DB_PATH`.

### Adding a strategy

1. Create `components/uwqsc/algorithms/<name>/` with an `IAlgorithm` subclass (and its preprocessor).
2. Decorate it with `@register_algorithm("<name>")` and set `DEFAULT_PARAMETERS`.
3. Set `REQUIRED_FEATURES = frozenset({"price", "sentiment"})` if it reads sentiment columns.
4. Import the subpackage in `components/uwqsc/algorithms/__init__.py`.

## Development

```bash
uv run pytest                       # all tests (unittest-style, files end in _test.py)
uv run poly check                   # brick boundaries and project wiring
uv run poly info / poly deps / poly libs
uv run pylint --max-args=10 --max-positional-arguments=10 --max-attributes=10 components bases test development
```

Large datasets for the dashboard's hackathon pages (`data/hackathon_sample_v2.parquet`) are not
committed. Download the CSV from
[Google Drive](https://drive.google.com/file/d/1H3ktLEsd3Bg9A9Rx5P45OdnYMEdkX29s/view?usp=sharing)
into `data/` and convert it with `development/conv_to_parquet.py`.

## Conventions

- Every commit message must have a line consisting only of `topic/#<issue>` (checked by the
  commit-msg hook), e.g.

  ```text
  Writing Unit Test for black_litterman.py

  topic/#100

  - Code coverage 80%.
  ```
- Name branches `topic/<issue_number>`.
- Changes reach `main` only through PRs with descriptive descriptions (preferably a list of commit
  descriptions). Add the `Ready for Review` label and request `algo-trading-team`; add
  `Ready for Merge` when approved.
- Pylint must stay above 8.0.
