import time
import logging
import json
from functools import wraps

logger = logging.getLogger("timing_logger")
logger.setLevel(logging.INFO)

# Ensure only one handler is attached
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')  # Log as raw JSON
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def log_execution_time(tag: str = "", extra_context: dict = None):
    """
    Decorator to log execution time of any function
    """
    extra_context = extra_context or {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                end = time.time()
                duration_ms = int((end - start) * 1000)
                log_data = {
                    "event": "timing",
                    "tag": tag or func.__name__,
                    "duration_ms": duration_ms,
                    **extra_context
                }
                logger.info(json.dumps(log_data))
        return wrapper
    return decorator


from timing_logger import log_execution_time

@log_execution_time(tag="external_api_call", extra_context={"source": "my-service"})
def call_something():
    ...
