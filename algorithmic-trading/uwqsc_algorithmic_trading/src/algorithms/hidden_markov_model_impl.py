"""
Implementation of the Hidden Markov Model (HMM) algorithm.
"""

from typing import Dict, List, Any

from pandas import DataFrame

from uwqsc_algorithmic_trading.interfaces.algorithms.algorithm_interface import IAlgorithm
from uwqsc_algorithmic_trading.src.preprocessing.hmm_preprocessor_impl import HMMPreProcessorImpl


class HiddenMarkovModelImpl(IAlgorithm):
    """
   Working logic for Hidden Markov Model (HMM) algorithm.
   """

    def __init__(self,
                 tickers: List[str],
                 parameters: Dict[str, Any] = None):
        name = "Hidden Markov Model"
        data_processor = HMMPreProcessorImpl()

        super().__init__(name, tickers, data_processor, parameters)

    def generate_signals(self, current_data: DataFrame):
        pass

    def calculate_position_size(self, ticker: str, price: float, portfolio_value: float) -> float:
        pass

    @DeprecationWarning
    def execute_trades(self, capital: float) -> DataFrame:
        """
       Execute trades based on signals and manage portfolio.
       This implementation follows the same pattern as SimpleMovingAverageImpl.execute_trades
       but uses HMM-specific signals and position calculations.


       :param capital: Value of cash allocated to the algorithm
       :returns: DataFrame with portfolio performance tracking capital changes
       """
        # Initialize portfolio DataFrame with same index as data
        portfolio = DataFrame(index=self.__data__.index)
        # Set initial capital
        portfolio['capital'] = capital

        # Iterate through each time period starting from second entry
        for i in range(1, len(portfolio)):
            date = portfolio.index[i]
            prev_date = portfolio.index[i - 1]

            # Generate trading signals using data window up to current date
            self.generate_signals(self.__data__.loc[prev_date:date])

            # Start with previous day's capital
            portfolio.loc[date, 'capital'] = portfolio.loc[prev_date, 'capital']

            # Process each ticker in our trading universe
            for ticker in self.tickers:
                price_col = f"{ticker}_price"

                # Get current price and portfolio value
                current_price: float = self.__data__.at[date, price_col]
                current_portfolio_value = portfolio.loc[date, 'capital']

                # Calculate position size based on signals and current state
                position_size = self.calculate_position_size(
                    ticker,
                    current_price,
                    current_portfolio_value
                )

                # Calculate trade cost and update portfolio value
                cost = position_size * current_price
                portfolio.loc[date, 'capital'] -= cost

                # Track number of trades executed
                if cost != 0:
                    self.__trade_count__ += 1

        return portfolio

    @DeprecationWarning
    def calculate_metrics(self, portfolio: DataFrame) -> Dict[str, float]:
        """
        Calculate performance metrics based on Hidden Markov Model.

        This function is now deprecated.
        """
