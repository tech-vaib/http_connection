import time
import logging
import json
import uuid
import inspect
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger("timing_logger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')  # JSON for Splunk
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def _log_event(tag, duration_ms, extra_context, error=None):
    log_data = {
        "event": "timing",
        "tag": tag,
        "duration_ms": duration_ms,
        **extra_context
    }
    if error:
        log_data["error"] = str(error)

    logger.info(json.dumps(log_data))

@contextmanager
def log_time_block(tag: str, extra_context: dict = None):
    extra_context = extra_context or {}
    extra_context.setdefault("trace_id", str(uuid.uuid4()))
    start = time.time()
    error = None

    try:
        yield
    except Exception as e:
        error = e
        raise
    finally:
        duration_ms = int((time.time() - start) * 1000)
        _log_event(tag, duration_ms, extra_context, error)

def log_execution_time(tag: str = "", extra_context: dict = None):
    extra_context = extra_context or {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            error = None

            # Map args to parameter names
            bound_args = inspect.signature(func).bind(*args, **kwargs)
            bound_args.apply_defaults()
            arg_dict = bound_args.arguments

            # Include identifiers
            context = {
                **extra_context,
                "reqid": arg_dict.get("reqid", str(uuid.uuid4())),
                "sessionid": arg_dict.get("sessionid", None),
                "trace_id": str(uuid.uuid4())
            }

            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = e
                raise
            finally:
                duration_ms = int((time.time() - start) * 1000)
                _log_event(tag or func.__name__, duration_ms, context, error)

        return wrapper
    return decorator


    with log_time_block("llm_generate", extra_context={"reqid": reqid, "sessionid": sessionid}):

            with log_time_block("parallel_calls", extra_context={"reqid": reqid, "sessionid": sessionid}):

import uuid
reqid = arg_dict.get("reqid", str(uuid.uuid4()))


with log_time_block("external_llm_call", extra_context={"reqid": "abc-123"}):
    result = call_llm()



from timing_logger import log_execution_time

@log_execution_time(tag="external_api_call", extra_context={"source": "my-service"})
def call_something():
    ...
