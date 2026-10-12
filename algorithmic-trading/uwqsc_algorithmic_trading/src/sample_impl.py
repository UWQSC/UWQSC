"""
This file serves as a sample implementation of the interfaces we have defined.

This is how the logic will be implemented. This is a good practice to make sure that your code  
is not in the hand of the public to be modified.

You can implement an abstract class by inheriting from it. Functions of abstract
base class must be decorated with @abstractmethod. Following is an example for the same.
"""

from uwqsc_algorithmic_trading.interfaces.sample_interface import ISampleClass


class SampleClassImpl(ISampleClass):
    """
    There is no naming convention for Implementation classes. However, if there is only one
    implementation for an interface, it is best practice to end the class name with "Impl"
    """

    def say_hi_to_mom(self) -> str:
        """
        We are "implementing" the interfaces' defined functions. This is what other people will use,
        but not see.

        :returns: String
        """

        return "Hi Mom"

    def say_hi_to_dad(self) -> int:
        """
        Same as above

        :returns: Int
        """

        return 0
