import httpx
import backoff
import uuid
import logging
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def create_retry_decorator(max_tries: int) -> Callable:
    return backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, httpx.TimeoutException),
        max_tries=max_tries,
        jitter=backoff.full_jitter,
    )

class AsyncServiceClient:
    def __init__(self, name: str, config: dict):
        self.name = name
        self.base_url = config["base_url"]
        self.timeout = config.get("timeout", 5)
        self.api_key = config.get("api_key", None)
        self.max_tries = config.get("max_tries", 3)

        default_headers = {}
        if self.api_key:
            default_headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(
                max_connections=config.get("max_connections", 100),
                max_keepalive_connections=config.get("max_keepalive_connections", 20)
            ),
            headers=default_headers,
        )

        self._retry = create_retry_decorator(self.max_tries)

    async def close(self):
        await self.client.aclose()

    async def _do_request(
        self,
        method: str,
        endpoint: str,
        request_id: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        merged_headers = {
            "X-Request-ID": request_id,
            **(headers or {})
        }

        try:
            response = await self.client.request(
                method=method,
                url=endpoint,
                headers=merged_headers,
                params=params,
                json=json
            )
            response.raise_for_status()
            logger.info(f"[{request_id}] {self.name} {method} {endpoint} - {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"[{request_id}] Error in {self.name}: {str(e)}")
            raise

    async def request(
        self,
        method: str,
        endpoint: str,
        request_id: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        decorated = self._retry(self._do_request)
        return await decorated(method, endpoint, request_id, params, json, headers)
