import logging

__doc__ = '''Logging function using decorators
Usage: decorate monitored function with "@logger"'''


def logger(f):
    def wrapped(*args, **kwargs):
        logging.debug("start {}".format(f))
        res = f(*args, **kwargs)
        logging.debug("end {}".format(f))
        return res

    return wrapped
