"""
Testing the command line parser and offline commands
"""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date

from uwqsc.cli import build_parser, main


class CliTest(unittest.TestCase):
    """
    This class is used to test argument parsing and commands that need no network
    """

    def test_parse_backtest(self):
        """
        Testing backtest arguments and repeatable parameters
        """

        args = build_parser().parse_args([
            "backtest", "--algo", "sma", "--tickers", "AAPL", "MSFT",
            "--start", "2023-01-01", "--param", "short_window=5"
        ])

        self.assertEqual(args.tickers, ["AAPL", "MSFT"])
        self.assertEqual(args.start, date(2023, 1, 1))
        self.assertEqual(args.param, ["short_window=5"])

    def test_list_algorithms(self):
        """
        Testing that registered algorithms are printed
        """

        out = io.StringIO()
        with redirect_stdout(out):
            main(["list-algorithms"])

        self.assertIn("sma:", out.getvalue())
        self.assertIn("hmm:", out.getvalue())

    def test_sync_sentiment_and_backtest_offline(self):
        """
        Testing the null sentiment sync and a backtest over an empty database
        """

        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "t.sqlite")
            out = io.StringIO()
            with redirect_stdout(out):
                main(["--db", db, "sync-sentiment", "--tickers", "AAPL",
                      "--start", "2024-01-01", "--end", "2024-01-05"])
                main(["--db", db, "backtest", "--algo", "sma", "--tickers", "AAPL",
                      "--param", "short_window=5"])

            self.assertIn("AAPL: 5 new sentiment rows", out.getvalue())
            self.assertIn('"short_window": 5', out.getvalue())


if __name__ == "__main__":
    unittest.main()
