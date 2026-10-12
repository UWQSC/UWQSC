"""
Testing the algorithm registry
"""

import unittest

from uwqsc.algorithm_core import (
    IAlgorithm,
    IPreProcessData,
    create_algorithm,
    list_algorithms,
    register_algorithm,
    unregister_algorithm,
)


class _NoOpPreProcessor(IPreProcessData):
    def missing_values(self):
        pass

    def remove_duplicate_timestamps(self):
        pass

    def remove_outliers(self):
        pass


class _DummyAlgorithm(IAlgorithm):
    DEFAULT_PARAMETERS = {"alpha": 1, "beta": 2}

    def __init__(self, tickers, parameters=None):
        super().__init__("Dummy", tickers, _NoOpPreProcessor(), parameters)

    def generate_signals(self, current_data):
        pass

    def calculate_position_size(self, ticker, price, portfolio_value):
        return 0.0


class RegistryTest(unittest.TestCase):
    """
    This class is used to test registering, creating and listing algorithms
    """

    def setUp(self):
        register_algorithm("dummy_test")(_DummyAlgorithm)

    def tearDown(self):
        unregister_algorithm("dummy_test")

    def test_create_merges_defaults(self):
        """
        Testing that created algorithms get defaults overridden by caller parameters
        """

        algorithm = create_algorithm("dummy_test", ["AAPL"], {"beta": 5})

        self.assertIsInstance(algorithm, _DummyAlgorithm)
        self.assertEqual(algorithm.parameters, {"alpha": 1, "beta": 5})
        self.assertEqual(algorithm.tickers, ["AAPL"])

    def test_list_returns_defaults_copy(self):
        """
        Testing that listing shows default parameters without exposing the class dict
        """

        listed = list_algorithms()
        self.assertEqual(listed["dummy_test"], {"alpha": 1, "beta": 2})

        listed["dummy_test"]["alpha"] = 99
        self.assertEqual(_DummyAlgorithm.DEFAULT_PARAMETERS["alpha"], 1)

    def test_duplicate_key_raises(self):
        """
        Testing that a key cannot be registered twice
        """

        with self.assertRaises(ValueError):
            register_algorithm("dummy_test")(_DummyAlgorithm)

    def test_unknown_key_raises(self):
        """
        Testing that creating an unregistered algorithm fails clearly
        """

        with self.assertRaises(KeyError):
            create_algorithm("does_not_exist", ["AAPL"])

    def test_default_required_features(self):
        """
        Testing that algorithms need only price data unless they say otherwise
        """

        self.assertEqual(_DummyAlgorithm.REQUIRED_FEATURES, frozenset({"price"}))


if __name__ == "__main__":
    unittest.main()
