import os
import logging
import uvicorn
from .rate_limiter import limiter
from starlette.routing import Match
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from fastapi.middleware.cors import CORSMiddleware
from .middlewares.pii_firewall import PIIFirewallMiddleware
from .routers import (
    health,
    chat
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info("Started the server!")
    yield
    # shutdown
    logger.info("Shutdown the server!")


app = FastAPI(
    title="AI-Powered Privacy Firewall for LLMs",
    version="0.0.1",
    contact={"name": "Kaushik", "email": "13kaushikk@gmail.com"},
    debug=True,
    lifespan=lifespan,
)

redis_uri = os.getenv("REDIS_URL", "redis://localhost:6379/0")


@app.middleware("https")
async def log_middlewear(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    routes = request.app.router.routes
    logger.info("Params: ")
    for route in routes:
        match, scope = route.matches(request)
        if match == Match.FULL:
            for name, value in scope["path_params"].items():
                logger.info(f"{name}: {value}")
    logger.info("Headers: ")
    for name, value in request.headers.items():
        logger.info(f"{name}: {value}")

    response = await call_next(request)
    logger.info(f"{request.method} {request.url} {response.status_code}")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter

app.add_middleware(PIIFirewallMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.include_router(health.router, prefix="/v1")
app.include_router(chat.router, prefix="/v1")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
