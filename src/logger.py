import logging
from typing import Callable, ParamSpec, TypeVar

__doc__ = '''Logging function using decorators
Usage: decorate monitored function with "@logger"'''

P = ParamSpec("P")
R = TypeVar("R")


def logger(f: Callable[P, R]) -> Callable[P, R]:
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        logging.debug(f"start {f}")
        res = f(*args, **kwargs)
        logging.debug(f"end {f}")
        return res

    return wrapped
