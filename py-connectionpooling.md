pip install httpx[http2] pybreaker motor

import asyncio
import httpx
import pybreaker
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Any, Dict, Optional
import time

# =============================
# 🔧 CONFIGURATION
# =============================

CONFIG = {
    "services": {
        "ai_service": {
            "url": "https://your-ai-service.com/infer",
            "timeout": 10,
            "retries": 3
        },
        "external_api": {
            "url": "https://external.api.com/endpoint",
            "timeout": 8,
            "retries": 2
        }
    },
    "cosmos_mongo": {
        "uri": "mongodb://<your-cosmos-uri>:<port>/?ssl=true&replicaSet=globaldb",
        "db": "your-db"
    }
}

# =============================
# 🔌 GLOBAL CLIENTS
# =============================

# Cosmos MongoDB client (pooling handled internally)
mongo_client = AsyncIOMotorClient(
    CONFIG["cosmos_mongo"]["uri"],
    maxPoolSize=100
)
mongo_db = mongo_client.get_database(CONFIG["cosmos_mongo"]["db"])

# HTTP client (connection pooling)
http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=200, max_keepalive_connections=100),
    http2=True
)

# =============================
# 🔁 RETRY & CIRCUIT BREAKER UTILS
# =============================

def get_circuit_breaker(service_name: str):
    return pybreaker.CircuitBreaker(
        fail_max=5,  # open circuit after 5 failures
        reset_timeout=30,  # stay open for 30s before retrying
        name=service_name
    )

async def call_with_retry_and_cb(
    service_name: str,
    method: str,
    payload: Optional[Dict] = None
) -> Any:
    cfg = CONFIG["services"][service_name]
    url = cfg["url"]
    retries = cfg["retries"]
    timeout = cfg["timeout"]

    breaker = get_circuit_breaker(service_name)

    for attempt in range(retries):
        try:
            async with asyncio.timeout(timeout):
                # Circuit breaker wraps the actual HTTP call
                @breaker
                async def do_request():
                    response = await http_client.request(
                        method, url, json=payload, timeout=timeout
                    )
                    response.raise_for_status()
                    return response.json()

                return await do_request()

        except (httpx.RequestError, httpx.HTTPStatusError, pybreaker.CircuitBreakerError) as e:
            print(f"[{service_name}] Attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

# =============================
# 🧠 BUSINESS LOGIC
# =============================

async def call_ai_service(input_data: dict):
    return await call_with_retry_and_cb("ai_service", "POST", input_data)

async def call_external_api(payload: dict):
    return await call_with_retry_and_cb("external_api", "POST", payload)

async def query_cosmos_mongo(query: dict) -> list:
    cursor = mongo_db["your-collection"].find(query)
    return await cursor.to_list(length=100)

async def handle_task(task_id: str):
    ai_input = {"prompt": f"Process task {task_id}"}
    ai_result = await call_ai_service(ai_input)

    db_result = await query_cosmos_mongo({"taskId": task_id})

    combined = {
        "ai_result": ai_result,
        "db_result": db_result
    }

    final_response = await call_external_api(combined)
    return {
        "task": task_id,
        "response": final_response
    }

# =============================
# 🚀 MAIN RUNNER
# =============================

async def main():
    task_ids = [f"task{i}" for i in range(1, 4)]
    results = await asyncio.gather(*(handle_task(tid) for tid in task_ids), return_exceptions=True)
    for result in results:
        print(result)

# Graceful shutdown
async def shutdown():
    await http_client.aclose()
    mongo_client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        asyncio.run(shutdown())
