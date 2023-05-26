import logging

from functools import wraps
from typing import Dict


def lab_logger(function):
    """
    A decorator that logs lab step output
    """
    @wraps(function)
    def wrapper(*args, **kwargs):

        try:
            items: Dict = args[0]
            funcname = function.__name__

            logging.info('Running lab step: ' + funcname)

            items["msgs"] = ''
            items["exception"] = ''

            output = function(*args, **kwargs)

            if output:
                logging.error("There was an error in " + funcname)
                if items["msgs"]:
                    logging.error("msgs:")
                    logging.error(items["msgs"])
                if items["exception"]:
                    logging.error("exception:")
                    logging.error(items["exception"])

            return function(*args, **kwargs)

        except Exception:
            funcname = function.__name__
            logging.error("There was an error in " + funcname)
            raise

    return wrapper
