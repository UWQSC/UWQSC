"""
Testing sentiment bucketing, the null source, storage and the sync service
"""

import unittest
from datetime import date, datetime, timezone

import pandas as pd

from uwqsc.sentiment import (
    SENTIMENT_COLUMNS,
    NullSentimentSource,
    SentimentScore,
    SentimentService,
    SQLiteSentimentStoreImpl,
    as_of_trading_date,
)


def _utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


class BucketingTest(unittest.TestCase):
    """
    This class is used to test that items map to the close they precede
    """

    def test_before_and_after_close(self):
        """
        Testing 15:59 vs 16:01 New York time on a winter (EST, UTC-5) weekday
        """

        self.assertEqual(as_of_trading_date(_utc(2024, 1, 10, 20, 59)), date(2024, 1, 10))
        self.assertEqual(as_of_trading_date(_utc(2024, 1, 10, 21, 1)), date(2024, 1, 11))

    def test_daylight_saving(self):
        """
        Testing the cutoff moves with EDT (UTC-4) in summer
        """

        self.assertEqual(as_of_trading_date(_utc(2024, 7, 10, 19, 59)), date(2024, 7, 10))
        self.assertEqual(as_of_trading_date(_utc(2024, 7, 10, 20, 1)), date(2024, 7, 11))

    def test_weekend_rolls_to_monday(self):
        """
        Testing Friday evening and Saturday items count toward Monday
        """

        self.assertEqual(as_of_trading_date(_utc(2024, 1, 12, 22, 0)), date(2024, 1, 15))
        self.assertEqual(as_of_trading_date(_utc(2024, 1, 13, 15, 0)), date(2024, 1, 15))

    def test_naive_timestamp_rejected(self):
        """
        Testing that timestamps without a timezone are refused
        """

        with self.assertRaises(ValueError):
            as_of_trading_date(datetime(2024, 1, 10, 12, 0))


class SentimentScoreTest(unittest.TestCase):
    """
    This class is used to test score validation
    """

    def test_range_validation(self):
        """
        Testing that scores outside [-1, 1] and negative volume are rejected
        """

        SentimentScore("AAPL", date(2024, 1, 2), 0.5, -0.5, 3, "x")
        with self.assertRaises(ValueError):
            SentimentScore("AAPL", date(2024, 1, 2), 1.5, 0.0, 3, "x")
        with self.assertRaises(ValueError):
            SentimentScore("AAPL", date(2024, 1, 2), 0.0, 0.0, -1, "x")


class SentimentServiceTest(unittest.TestCase):
    """
    This class is used to test the null source, the store and incremental sync
    """

    def setUp(self):
        self.store = SQLiteSentimentStoreImpl(":memory:")
        self.service = SentimentService(NullSentimentSource(), self.store)

    def test_null_source_is_neutral_on_trading_days(self):
        """
        Testing that the null source yields zero scores on weekdays only
        """

        scores = NullSentimentSource().fetch_daily_sentiment(
            ["AAPL"], date(2024, 1, 12), date(2024, 1, 15)
        )
        self.assertEqual(list(scores.columns), SENTIMENT_COLUMNS)
        self.assertEqual(list(scores["date"]), [date(2024, 1, 12), date(2024, 1, 15)])
        self.assertTrue((scores[["emotional", "logical", "volume"]] == 0).all().all())

    def test_incremental_sync(self):
        """
        Testing that a re-sync only writes the new days
        """

        self.service.sync(["AAPL"], date(2024, 1, 1), date(2024, 1, 5))
        written = self.service.sync(["AAPL"], date(2024, 1, 1), date(2024, 1, 10))

        self.assertEqual(written, {"AAPL": 3})
        self.assertEqual(self.store.latest_date("AAPL", "null"), date(2024, 1, 10))

    def test_load_wide_volume_weights_sources(self):
        """
        Testing the wide layout and that multiple sources are volume-weighted
        """

        self.store.upsert(pd.DataFrame([
            ("AAPL", date(2024, 1, 2), 1.0, 0.0, 3, "a"),
            ("AAPL", date(2024, 1, 2), -1.0, 1.0, 1, "b"),
        ], columns=SENTIMENT_COLUMNS))

        wide = self.service.load_wide(["AAPL", "MSFT"])

        self.assertEqual(wide.loc["2024-01-02", "AAPL_sent_emotional"], 0.5)
        self.assertEqual(wide.loc["2024-01-02", "AAPL_sent_logical"], 0.25)
        self.assertEqual(wide.loc["2024-01-02", "AAPL_sent_volume"], 4)
        self.assertTrue(pd.isna(wide.loc["2024-01-02", "MSFT_sent_emotional"]))


if __name__ == "__main__":
    unittest.main()
