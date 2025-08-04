from fastapi import FastAPI, Request
import time
import logging
import json
import inspect

logger = logging.getLogger("timing_logger")
logging.basicConfig(level=logging.INFO)

app = FastAPI()

@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()

    try:
        response = await call_next(request)
    except Exception as e:
        # Log exception and re-raise
        logger.error({
            "path": request.url.path,
            "method": request.method,
            "error": str(e),
            "client": request.client.host
        })
        raise

    duration_ms = int((time.time() - start_time) * 1000)

    # Try to extract some headers
    headers_to_log = ["user-agent", "authorization", "x-request-id"]
    headers = {h: request.headers.get(h) for h in headers_to_log if request.headers.get(h)}

    # Optionally: get handler route (endpoint function name)
    route_name = None
    for route in app.router.routes:
        if request.url.path == route.path:
            route_name = getattr(route.endpoint, "__name__", None)
            break

    log_data = {
        "event": "timing",
        "path": request.url.path,
        "method": request.method,
        "duration_ms": duration_ms,
        "client": request.client.host,
        "status_code": response.status_code,
        "handler": route_name,
        **headers
    }

    logger.info(json.dumps(log_data))
    return response
