import logging
from typing import Callable, ParamSpec, TypeVar

__doc__ = '''Logging function using decorators
Usage: decorate monitored function with "@debug_logger"'''

logger = logging.getLogger("debug_logger")

P = ParamSpec("P")
R = TypeVar("R")


def debug_logger(f: Callable[P, R]) -> Callable[P, R]:
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        logger.debug(f"start {f}")
        res = f(*args, **kwargs)
        logger.debug(f"end {f}")
        return res

    return wrapped
