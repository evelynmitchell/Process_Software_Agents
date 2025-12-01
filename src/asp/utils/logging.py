"""
Logging utilities for the ASP platform.
"""

import logging


def telemetry_logger(func):
    """
    A decorator that logs the execution of a function.
    """
    def wrapper(*args, **kwargs):
        logging.info(f"Executing {func.__name__}")
        result = func(*args, **kwargs)
        logging.info(f"Finished executing {func.__name__}")
        return result
    return wrapper
