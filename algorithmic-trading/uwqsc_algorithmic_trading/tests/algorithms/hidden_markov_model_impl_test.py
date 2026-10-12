"""
Testing the Hidden Markov Model Algorithm
"""

import unittest
from unittest.mock import MagicMock

from uwqsc_algorithmic_trading.interfaces.algorithms.algorithm_interface import StockPosition
from uwqsc_algorithmic_trading.src.algorithms.hidden_markov_model_impl import HiddenMarkovModelImpl
from uwqsc_algorithmic_trading.src.preprocessing.hmm_preprocessor_impl import HMMPreProcessorImpl


class HiddenMarkovModelImplTest(unittest.TestCase):
    """
   This class is used to test each component of Hidden Markov Model Algorithm.
   Following the same testing pattern as SimpleMovingAverageImplTest.
   """

    def setUp(self):
        """
       Set up test fixtures before each test method.
       Similar to SMA tests, we mock the preprocessor and initialize the algorithm.
       """
        self.tickers = ["AAPL", "GOOGL"]  # Test with two popular stocks
        self.preprocessor = MagicMock(spec=HMMPreProcessorImpl)  # Mock preprocessor
        self.parameters = {"position_size": 0.1}  # Same position size as SMA for consistency
        self.algorithm = HiddenMarkovModelImpl(self.tickers, self.parameters)
        # Initialize positions to HOLD
        self.algorithm.__positions__ = {ticker: StockPosition.HOLD for ticker in self.tickers}
        self.algorithm.__trade_count__ = 0
