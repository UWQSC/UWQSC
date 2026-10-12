"""
This file serves as a sample interface for other projects to see.

This is how the Algorithmic Trading APIs will be visible to other teams. It is the duty of the AT
team to make sure that the code implementations follow these public APIs

You can create an abstract class by inheriting "Abstract Base Class" (abc). Functions of abstract
base class must be decorated with @abstractmethod. Following is an example for the same.
"""

from abc import ABC, abstractmethod
from uwqsc_algorithmic_trading.src.common.config import INTERFACE_NOT_IMPLEMENTED_ERROR


class ISampleClass(ABC):
    """
    An interface class must have an "I" before the class name.
    """

    @abstractmethod
    def say_hi_to_mom(self) -> str:
        """
        This is an abstract method that should be implemented in a subclass.

        Calling this method from the interface class should raise an exception, as you are
        supposed to call it from the Implementation class. However, do note that the implementation
        class must have an implementation of this method.

        :returns: This will return a String object.
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def say_hi_to_dad(self) -> int:
        """
        Same as above

        :return: Int
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR
