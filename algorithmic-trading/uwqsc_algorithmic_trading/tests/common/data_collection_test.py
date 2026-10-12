"""
This python file tests the data collection module and the constants.
"""

import unittest
import os.path

from uwqsc_algorithmic_trading.src.common.data_collection import setup_data
from uwqsc_algorithmic_trading.src.common.config import SRC_DIR, COMMON_DIR, DATA_DIR, PROJECT_DIR


class DataCollectionTests(unittest.TestCase):
    """
    Tests for data-collection Python.
    """

    def test_data_setup_does_not_crash(self):
        """
        Testing that this function does not crash, and that it doesn't return anything
        """

        setup_data()
        self.assertEqual(setup_data(), None)

    def test_config_global_constants(self):
        """
        Testing that the global constants store the right value
        """

        src_dir = SRC_DIR
        common_dir = COMMON_DIR
        data_dir = DATA_DIR
        project_dir = PROJECT_DIR

        current_dir = os.path.dirname(os.path.abspath(__file__))
        testing_dir = os.path.dirname(current_dir)
        test_project_dir = os.path.dirname(testing_dir)
        test_src_dir = os.path.join(test_project_dir, "src")
        test_common_dir = os.path.join(test_src_dir, "common")
        test_data_dir = os.path.join(test_project_dir, "data")

        self.assertEqual(src_dir, test_src_dir)
        self.assertEqual(common_dir, test_common_dir)
        self.assertEqual(data_dir, test_data_dir)
        self.assertEqual(project_dir, test_project_dir)
