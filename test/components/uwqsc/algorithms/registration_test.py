"""
Testing that the strategies register themselves and read their parameters
"""

import unittest

import uwqsc.algorithms  # pylint: disable=unused-import
from uwqsc.algorithm_core import create_algorithm, list_algorithms
from uwqsc.algorithms import HiddenMarkovModelImpl, SimpleMovingAverageImpl


class RegistrationTest(unittest.TestCase):
    """
    This class is used to test strategy registration
    """

    def test_strategies_registered(self):
        """
        Testing that importing uwqsc.algorithms registers sma and hmm
        """

        listed = list_algorithms()
        self.assertIn("sma", listed)
        self.assertIn("hmm", listed)
        self.assertIsInstance(create_algorithm("hmm", ["AAPL"]), HiddenMarkovModelImpl)

    def test_sma_parameters_reach_preprocessor(self):
        """
        Testing that SMA windows and position size come from parameters
        """

        algorithm = create_algorithm("sma", ["AAPL"], {"short_window": 5, "position_size": 0.2})

        self.assertIsInstance(algorithm, SimpleMovingAverageImpl)
        self.assertEqual(algorithm.parameters["position_size"], 0.2)
        self.assertEqual(algorithm.parameters["long_window"], 200)
        # pylint: disable=protected-access
        self.assertEqual(algorithm.__data_processor__.short_window, 5)
        self.assertEqual(algorithm.__data_processor__.long_window, 200)

    def test_sma_defaults(self):
        """
        Testing that SMA works with no parameters at all
        """

        algorithm = SimpleMovingAverageImpl(["AAPL"])
        self.assertEqual(algorithm.parameters,
                         {"position_size": 0.1, "short_window": 50, "long_window": 200})


if __name__ == "__main__":
    unittest.main()
