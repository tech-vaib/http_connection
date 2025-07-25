# http_connection
microservice/
│
├── config.py               ← Central service config with API keys and base URLs
├── http_client.py          ← Core reusable, non-blocking HTTP client with API key + retry + tracing
├── service_clients.py      ← Instances of services with clean API
└── main.py                 ← FastAPI app using these services

| Feature                     | Support                                |
| --------------------------- | -------------------------------------- |
| 🔁 Retry per service        | `backoff` with custom settings         |
| 🔐 API key auth             | Automatic via config                   |
| 📡 Async non-blocking       | `asyncio.gather()` for concurrency     |
| 🔍 Traceable requests       | `X-Request-ID` propagated              |
| 🔗 Configurable per-service | All headers, timeouts, base URLs, keys |
| 🔁 Reuse client connections | With `httpx.AsyncClient`               |
| 🧼 Clean shutdown           | Closes connections on exit             |
| `create_retry_decorator()` | Returns a custom retry wrapper per service |
| `self._retry`              | Wraps the internal `_do_request()` method  |
| `max_tries`                | Pulled from each service's config          |

## Test Locally
   Start the FastAPI app:
   
    uvicorn main:app --reload

curl -H "X-Request-ID: abc123" http://localhost:8000/aggregate
