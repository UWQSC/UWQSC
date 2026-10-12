"""
Concrete trading strategies. Importing this package registers every strategy with
uwqsc.algorithm_core's registry. To add a strategy, create a subpackage that decorates its
IAlgorithm subclass with @register_algorithm("<key>") and import it below.
"""

from uwqsc.algorithms.hmm import HiddenMarkovModelImpl
from uwqsc.algorithms.sma import SimpleMovingAverageImpl

__all__ = ["HiddenMarkovModelImpl", "SimpleMovingAverageImpl"]
