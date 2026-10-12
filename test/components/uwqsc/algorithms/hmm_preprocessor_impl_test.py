"""
Testing the Hidden Markov Model Preprocessor
"""

import unittest
import pandas as pd

from uwqsc_algorithmic_trading.src.preprocessing.hmm_preprocessor_impl import HMMPreProcessorImpl


class HMMPreprocessorImplTest(unittest.TestCase):
    """
    This class is used to test each component of Hidden Markov Model's preprocessor
    """

    def setUp(self):
        self.tickers = ["AAPL", "GOOGL"]
        self.short_window = 50
        self.long_window = 200

        self.preprocessor = HMMPreProcessorImpl()

    def test_remove_duplicate_timestamps_removes_duplicates(self):
        """
        Test that we remove duplicate timestamps
        """

        # Create a DataFrame with duplicate 'Date' entries.
        data = pd.DataFrame({
            'Date': ['2025-03-13', '2025-03-13', '2025-03-14', '2025-03-15', '2025-03-15'],
            'Price': [10, 10, 20, 30, 30]
        })

        # Inject the stubbed data into the preprocessor.
        # Note: __raw_data__ and __processed_data__ are defined in the base class, and we access
        # them via name mangling.
        self.preprocessor.__processed_data__ = data

        # Call the function under test.
        self.preprocessor.remove_duplicate_timestamps()

        # Assert that the size is reduced after duplicates are removed.
        self.assertFalse(self.preprocessor.__processed_data__.duplicated().any())

    def test_missing_values_removes_missing_values(self):
        """
        Test that missing values are filled using forward and backward fill.
        """
        # Create a DataFrame with missing values.
        data = pd.DataFrame({
            'Date': ['2025-03-13', '2025-03-14', '2025-03-15', '2025-03-16', '2025-03-17'],
            'Price': [10, None, 20, None, 30]
        })

        # Inject the stubbed data into the preprocessor.
        self.preprocessor.__processed_data__ = data

        # Call the function under test.
        self.preprocessor.missing_values()

        # Assert that there are no remaining missing values.
        self.assertFalse(self.preprocessor.__processed_data__.isnull().any().any())
