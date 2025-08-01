import time
import logging
import json
from functools import wraps
import inspect

logger = logging.getLogger("timing_logger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')  # JSON logs for Splunk
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def log_execution_time(tag: str = "", extra_context: dict = None):
    """
    Decorator to log execution time of any function,
    and auto-log named args like reqid, sessionid
    """
    extra_context = extra_context or {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()

            # Get arg names and values using inspect
            bound_args = inspect.signature(func).bind(*args, **kwargs)
            bound_args.apply_defaults()
            arg_dict = bound_args.arguments  # OrderedDict

            # Optionally extract specific values
            reqid = arg_dict.get("reqid")
            sessionid = arg_dict.get("sessionid")

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

                if reqid:
                    log_data["reqid"] = reqid
                if sessionid:
                    log_data["sessionid"] = sessionid

                logger.info(json.dumps(log_data))
        return wrapper
    return decorator



from timing_logger import log_execution_time

@log_execution_time(tag="external_api_call", extra_context={"source": "my-service"})
def call_something():
    ...
