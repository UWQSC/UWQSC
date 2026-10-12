"""
Sample test file
"""

import unittest

from uwqsc_algorithmic_trading.interfaces.sample_interface import ISampleClass
from uwqsc_algorithmic_trading.src.sample_impl import SampleClassImpl


class SampleTest(unittest.TestCase):
    """
    This class tests sample cases
    """

    def setUp(self):
        """
        This function runs before every unit test.
        """

    def tearDown(self):
        """
        This function runs after every unit test.
        """

    def test_sample(self):
        """
        This function tests sample cases
        """

        self.assertEqual(2 + 2, 4)

    def test_sample_implementation_does_not_raise_exception(self):
        """
        Testing our sample implementation
        """

        interface_class: ISampleClass = SampleClassImpl()
        self.assertEqual(interface_class.say_hi_to_mom(), "Hi Mom")
        self.assertEqual(interface_class.say_hi_to_dad(), 0)
        