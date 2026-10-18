import time
import uuid
from typing import List

from fastapi import FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGIN = "https://dash-1wxh1c.example.com"
EMAIL = "23f3002008@ds.study.iitm.ac.in"

app = FastAPI()

# CORS: allow ONLY the assigned origin. Do not use "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_required_headers(request: Request, call_next):
    start = time.perf_counter()

    response: Response = await call_next(request)

    elapsed = max(0.0, time.perf_counter() - start)

    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"

    return response


@app.get("/stats")
def stats(values: str = Query(...)):
    try:
        numbers: List[int] = [int(item.strip()) for item in values.split(",") if item.strip() != ""]
    except ValueError:
        return {"error": "All values must be integers separated by commas."}

    if not numbers:
        return {"error": "Provide at least one integer in the values parameter."}

    count = len(numbers)
    total = sum(numbers)
    minimum = min(numbers)
    maximum = max(numbers)
    mean = total / count

    return {
        "email": EMAIL,
        "count": count,
        "sum": total,
        "min": minimum,
        "max": maximum,
        "mean": mean,
    }