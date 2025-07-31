The Problem: Python’s Global Interpreter Lock (GIL)

    Python's GIL prevents more than one thread from executing Python bytecode at the same time in a single process.

    This means multi-threading in one process won't fully utilize multiple CPU cores.

    This is especially problematic for CPU-bound workloads (e.g., LLM calls, tokenization, data parsing, encryption).

    Pod CPU/Memory/GC pressure

    Cause: Python is single-threaded per core, and CPU-bound tasks (e.g. JSON parsing, tokenization) can block others.
    Solution: Run multiple gunicorn or Uvicorn workers, 
    gunicorn app:app -k uvicorn.workers.UvicornWorker --workers 4 --threads 2


| Feature                  | Uvicorn (alone)      | Gunicorn + Uvicorn                      |
| ------------------------ | -------------------- | --------------------------------------- |
| 🧠 Multi-core support    | ❌ Single process     | ✅ Multi-process (via `--workers`)       |
| 🚀 Concurrent processing | ✅ Async, single loop | ✅ Parallel processes (each async)       |
| 🔁 Resilience            | ❌ One crash = down   | ✅ Restart crashed workers               |
| 🔥 Worker timeouts       | ❌ None               | ✅ Configurable (`--timeout`)            |
| 🔁 Worker recycling      | ❌ No support         | ✅ Avoid memory leaks (`--max-requests`) |
| 🧪 Proven under load     | ✅ Limited            | ✅ Battle-tested at scale                |


**Defaults When Using Uvicorn Alone (without Gunicorn)
**
uvicorn app:app

| Setting                | Default Value                                 | Notes                                              |
| ---------------------- | --------------------------------------------- | -------------------------------------------------- |
| `--workers`            | ❌ Not supported (unless run with `--factory`) | Only **one process** is used                       |
| `--host`               | `127.0.0.1`                                   | Not accessible outside container unless overridden |
| `--port`               | `8000`                                        | Standard                                           |
| `--loop`               | `auto`                                        | Chooses `uvloop` if installed (good)               |
| `--http`               | `auto`                                        | Uses h11                                           |
| `--timeout-keep-alive` | `5s`                                          | Idle client connections timeout                    |
| `--limit-concurrency`  | Unlimited                                     | Can lead to event loop overload                    |
| `--limit-max-requests` | Unlimited                                     | No auto-recycling of workers                       |
| `--reload`             | `False`                                       | Development-only feature                           |


🔧 Gunicorn Handles Production Features That Uvicorn Lacks:

    Process management: Spawns and monitors multiple worker processes

    Crash recovery: Restarts failed workers automatically

    Timeout protection: Kills hung workers (--timeout)

    Horizontal scale: Works well with Kubernetes HPA or KEDA

    Tuning knobs for concurrency (--workers, --threads, --keep-alive)


** But Why Not Use Uvicorn Alone?
**
Uvicorn is fast and simple — great for development or small apps.

But it's not a process manager, so:

    It runs as a single process

    If the app blocks or crashes, the whole service goes down

    You can't use --workers without --factory mode, which has its own limitations

**Summary: When to Use Gunicorn + Uvicorn
**
Use Case	Recommendation
Local dev or small POC	✅ Uvicorn standalone is fine
LLM/chatbot API under moderate–high load	✅ Use Gunicorn with Uvicorn workers
AKS, Docker, ECS, etc.	✅ Gunicorn (handles crashes + concurrency)
Long-running or blocking tasks	✅ Gunicorn (with timeouts + isolation)    


gunicorn app:app \
  -k uvicorn.workers.UvicornWorker \
  --workers 4 \
  --threads 2 \
  --timeout 60 \
  --keep-alive 5 \
  --bind 0.0.0.0:8000
  
**  Adapt --workers to match pod CPU limits.
**


 1. Application-Level Issues
| Cause                             | What to Check                                                           |
| --------------------------------- | ----------------------------------------------------------------------- |
| **Blocking code** in async routes | Use `async def`, avoid `time.sleep`, use `await` properly               |
| **Large payloads**                | Use pagination, compression, or streaming                               |
| **Synchronous DB calls**          | Ensure Cosmos DB or Mongo clients are async if you're using `async def` |
| **Unoptimized queries**           | Indexing in Cosmos DB, bad filter usage, missing partition key          |
| **Inefficient LLM usage**         | Long prompts, multiple API calls, large context windows                 |
| **Slow cold starts**              | Heavy startup logic in `@app.on_event("startup")`                       |



=====================
import httpx

client: httpx.AsyncClient = None

def get_httpx_client():
    global client
    if client is None:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(10),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
    return client

@app.get("/data")
async def fetch_data():
    client = get_httpx_client()
    resp = await client.get("https://api.example.com/data")
    return resp.json()
@app.on_event("shutdown")
async def shutdown_event():
    global client
    if client:
        await client.aclose()

Things to check:
Kubernetes Networking & DNS Latency
Cause: AKS networking plugins (especially kubenet) may add overhead; DNS can be slow in bursty workloads.
1. Enable CoreDNS caching.
2. Use VNET CNI if available.
3. Measure DNS lookup time inside pod: (time nslookup cosmos.mongo.cosmos.azure.com
)
4. Offload LLM calls to background workers if not needed synchronously.
5. Batch prompt generations or cache results when possible.
6. Avoid querying Cosmos via public IP from inside AKS:- Use VNet-injected AKS + private endpoint for Cosmos.

7. **Check these in API:**
   Backend health probes:
Enable and configure to avoid sending traffic to unhealthy endpoints.(APIM)
Connection reuse (keep-alive):
Enable HTTP/2 and keep-alive connections for performance.(APIM)
APIM has a default timeout of 240 seconds (4 minutes)
API gateway timeouts: Match or slightly exceed APIM timeout settings to avoid premature drops.
LB: Default Azure Load Balancer timeout is 4 minutes.

kubectl logs -n istio-system istio-ingressgateway-xxx
az network lb probe show --name <probe> --resource-group <rg> --lb-name <lb-name>

