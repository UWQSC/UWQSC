"""
Registry that lets algorithms be found by name and created with parameters.
"""

from typing import Any, Callable, Dict, List, Optional, Type

from uwqsc.algorithm_core.algorithm_interface import IAlgorithm

_REGISTRY: Dict[str, Type[IAlgorithm]] = {}


def register_algorithm(key: str) -> Callable[[Type[IAlgorithm]], Type[IAlgorithm]]:
    """
    Class decorator that registers an algorithm under a unique key.

    :param key: String. Name the algorithm is looked up by
    :returns: The decorator, which returns the class unchanged
    """

    def decorator(cls: Type[IAlgorithm]) -> Type[IAlgorithm]:
        if key in _REGISTRY:
            raise ValueError(f"Algorithm '{key}' is already registered")
        _REGISTRY[key] = cls
        return cls

    return decorator


def create_algorithm(key: str,
                     tickers: List[str],
                     parameters: Optional[Dict[str, Any]] = None) -> IAlgorithm:
    """
    Create a registered algorithm.

    :param key: String. Registered algorithm name
    :param tickers: List. Tickers to trade
    :param parameters: Dictionary. Overrides for the algorithm's DEFAULT_PARAMETERS
    :returns: The algorithm instance
    """

    if key not in _REGISTRY:
        raise KeyError(f"Unknown algorithm '{key}'. Registered: {sorted(_REGISTRY)}")
    return _REGISTRY[key](tickers, parameters)


def get_algorithm_class(key: str) -> Type[IAlgorithm]:
    """
    :param key: String. Registered algorithm name
    :returns: The registered class
    """

    return _REGISTRY[key]


def list_algorithms() -> Dict[str, Dict[str, Any]]:
    """
    :returns: Each registered key mapped to a copy of its DEFAULT_PARAMETERS
    """

    return {key: dict(cls.DEFAULT_PARAMETERS) for key, cls in sorted(_REGISTRY.items())}


def unregister_algorithm(key: str) -> None:
    """
    Remove a registration. Intended for tests.

    :param key: String. Registered algorithm name
    """

    _REGISTRY.pop(key, None)
