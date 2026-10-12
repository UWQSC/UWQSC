"""
Command line entry point: `uwqsc <command>`.
"""

import argparse
import json
from datetime import date
from typing import Any, Dict, List, Optional

# Importing the strategies registers them with the algorithm registry.
from uwqsc import algorithms  # noqa: F401  # pylint: disable=unused-import
from uwqsc.algorithm_core import create_algorithm, list_algorithms
from uwqsc.backtesting import SnapshotBuilder, StoreBackedBacktest
from uwqsc.market_data import MarketDataService, SQLiteMarketDataStoreImpl, YFinanceDataSourceImpl
from uwqsc.sentiment import NullSentimentSource, SentimentService, SQLiteSentimentStoreImpl
from uwqsc.storage import connect


def _parse_param(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _parse_params(pairs: Optional[List[str]]) -> Dict[str, Any]:
    params = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(f"--param expects key=value, got '{pair}'")
        key, value = pair.split("=", 1)
        params[key] = _parse_param(value)
    return params


def _services(db_path: Optional[str]):
    conn = connect(db_path)
    market = MarketDataService(YFinanceDataSourceImpl(), SQLiteMarketDataStoreImpl(conn=conn))
    sentiment = SentimentService(NullSentimentSource(), SQLiteSentimentStoreImpl(conn=conn))
    return market, sentiment


def cmd_sync(args) -> None:
    """Incrementally download daily bars into the database."""
    market, _ = _services(args.db)
    written = market.sync(args.tickers, args.start, args.end, refresh_info=not args.no_info)
    for ticker, count in written.items():
        print(f"{ticker}: {count} new bars")


def cmd_sync_sentiment(args) -> None:
    """Incrementally store sentiment (neutral placeholder source for now)."""
    _, sentiment = _services(args.db)
    written = sentiment.sync(args.tickers, args.start, args.end)
    for ticker, count in written.items():
        print(f"{ticker}: {count} new sentiment rows")


def cmd_list_algorithms(_args) -> None:
    """Print registered algorithms and their default parameters."""
    for key, defaults in list_algorithms().items():
        print(f"{key}: {defaults}")


def cmd_backtest(args) -> None:
    """Run one registered algorithm over stored data."""
    market, sentiment = _services(args.db)
    algorithm = create_algorithm(args.algo, args.tickers, _parse_params(args.param))
    builder = SnapshotBuilder(market, sentiment)
    backtest = StoreBackedBacktest(algorithm, builder, args.capital, args.start, args.end)
    metrics = backtest.run()
    print(json.dumps({"algorithm": args.algo, "parameters": algorithm.parameters, **metrics},
                     indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    """
    :returns: The argument parser for every subcommand
    """

    parser = argparse.ArgumentParser(prog="uwqsc", description="UWQSC trading toolkit")
    parser.add_argument("--db",
                        help="SQLite path (default: $UWQSC_DB_PATH or ~/.uwqsc/uwqsc.sqlite)")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_range(p, start_required=True):
        p.add_argument("--tickers", nargs="+", required=True)
        p.add_argument("--start", type=date.fromisoformat, required=start_required)
        p.add_argument("--end", type=date.fromisoformat, default=None)

    p = sub.add_parser("sync", help="download missing daily bars")
    add_range(p)
    p.add_argument("--no-info", action="store_true", help="skip ticker metadata refresh")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("sync-sentiment", help="store missing sentiment rows")
    add_range(p)
    p.set_defaults(func=cmd_sync_sentiment)

    p = sub.add_parser("list-algorithms", help="show registered algorithms")
    p.set_defaults(func=cmd_list_algorithms)

    p = sub.add_parser("backtest", help="backtest a registered algorithm on stored data")
    p.add_argument("--algo", required=True)
    add_range(p, start_required=False)
    p.add_argument("--capital", type=float, default=10_000.0)
    p.add_argument("--param", action="append", metavar="KEY=VALUE",
                   help="override a parameter; repeatable")
    p.set_defaults(func=cmd_backtest)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    """
    Parse arguments and run the chosen command.
    """

    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
