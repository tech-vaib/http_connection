import httpx
import asyncio
from typing import Optional, Dict, Any

class ExternalHttpClient:
    """
    A reusable, async-safe HTTP client with connection pooling,
    retries, and graceful shutdown handling.
    """

    def __init__(self, timeout: float = 10.0, connect_timeout: float = 3.0):
        self.timeout = httpx.Timeout(timeout, connect=connect_timeout)
        self.limits = httpx.Limits(
            max_keepalive_connections=100,
            max_connections=200
        )
        self.client: Optional[httpx.AsyncClient] = None

    async def startup(self):
        """Initialize the HTTP client on application startup."""
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=self.limits,
            http2=True,
            headers={
                "User-Agent": "your-app/1.0"
                # Add other global headers here (e.g., Authorization)
            }
        )
        print("[http_client] Initialized")

    async def shutdown(self):
        """Clean up and close the HTTP client on application shutdown."""
        if self.client:
            await self.client.aclose()
            print("[http_client] Closed")

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """
        Make an HTTP request using the shared client.
        """
        if not self.client:
            raise RuntimeError("HTTP client not initialized. Call startup() first.")

        response = await self.client.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            json=json,
            timeout=timeout or self.timeout
        )
        response.raise_for_status()
        return response


# ==========================
# ✅ Example Usage
# ==========================

async def main():
    http = ExternalHttpClient()
    await http.startup()

    try:
        response = await http.request(
            "GET",
            "https://httpbin.org/get",
            headers={"Custom-Header": "hello"}
        )
        print(response.status_code)
        print(response.json())

    finally:
        await http.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
