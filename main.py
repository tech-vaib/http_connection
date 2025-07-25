from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uuid
import asyncio

from service_clients import user_service, inventory_service

app = FastAPI()

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.get("/aggregate")
async def aggregate_data(request: Request):
    request_id = request.state.request_id

    # Non-blocking parallel service calls
    try:
        user_task = user_service.request("GET", "/users/1", request_id)
        inventory_task = inventory_service.request("GET", "/items/42", request_id)
        
        user_resp, inv_resp = await asyncio.gather(user_task, inventory_task)

        return {
            "user": user_resp.json(),
            "inventory": inv_resp.json(),
            "request_id": request_id
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "request_id": request_id}
        )

@app.on_event("shutdown")
async def shutdown_event():
    await user_service.close()
    await inventory_service.close()
