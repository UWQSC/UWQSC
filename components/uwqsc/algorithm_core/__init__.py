"""
Interfaces every trading algorithm implements, plus the algorithm registry.
"""

from uwqsc.algorithm_core.algorithm_interface import IAlgorithm, StockPosition
from uwqsc.algorithm_core.preprocessor_interface import IPreProcessData
from uwqsc.algorithm_core.registry import (
    create_algorithm,
    get_algorithm_class,
    list_algorithms,
    register_algorithm,
    unregister_algorithm,
)

__all__ = [
    "IAlgorithm",
    "IPreProcessData",
    "StockPosition",
    "create_algorithm",
    "get_algorithm_class",
    "list_algorithms",
    "register_algorithm",
    "unregister_algorithm",
]
