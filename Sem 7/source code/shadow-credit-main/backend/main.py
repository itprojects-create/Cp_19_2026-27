from __future__ import annotations

import asyncio
import json
import logging
import traceback
import importlib
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address
except ModuleNotFoundError:
    class RateLimitExceeded(Exception):
        def __init__(self, detail: str = "100/minute"):
            self.detail = detail

    def _rate_limit_exceeded_handler(request, exc):
        return JSONResponse(status_code=429, content={"detail": str(getattr(exc, "detail", "rate limit exceeded"))})

    class SlowAPIMiddleware:  # pragma: no cover - fallback when slowapi missing
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            await self.app(scope, receive, send)

    class Limiter:  # pragma: no cover - fallback when slowapi missing
        def __init__(self, key_func=None, default_limits=None):
            self.key_func = key_func
            self.default_limits = default_limits or []

        def limit(self, _rule: str):
            def decorator(fn):
                return fn

            return decorator

    def get_remote_address(request):
        return getattr(getattr(request, "client", None), "host", "unknown")

import aiosqlite
try:
    from backend.api import health, sessions
    from backend.api.ingest import router as ingest_router
    from backend.api.verify import router as verify_router
    from backend.api.websocket import websocket_router
    from backend.config import get_settings
    from backend.db.database import DatabaseError, executescript_file
except ModuleNotFoundError:
    # Force local backend/api modules first to avoid collisions with unrelated `api` packages.
    _this_dir = Path(__file__).resolve().parent
    if str(_this_dir) not in sys.path:
        sys.path.insert(0, str(_this_dir))
    health = importlib.import_module("api.health")
    sessions = importlib.import_module("api.sessions")
    ingest_router = importlib.import_module("api.ingest").router
    verify_router = importlib.import_module("api.verify").router
    websocket_router = importlib.import_module("api.websocket").websocket_router
    from config import get_settings
    from db.database import DatabaseError, executescript_file


class ResponseMeta(BaseModel):
    session_id: str | None = None
    agent_id: str | None = None
    latency_ms: int = 0
    timestamp: str


class APIResponse(BaseModel):
    success: bool
    data: Any
    meta: ResponseMeta


def wrap_response(
    data: Any,
    session_id: str = None,
    agent_id: str = None,
    latency_ms: int = 0,
) -> dict:
    return APIResponse(
        success=True,
        data=data,
        meta=ResponseMeta(
            session_id=session_id,
            agent_id=agent_id,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow().isoformat() + "Z",
        ),
    ).model_dump()


logger = logging.getLogger("shadow_credit")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _log_json(level: str, message: str, extra: dict | None = None) -> None:
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level.upper(),
        "message": message,
        "extra": extra or {},
    }
    getattr(logger, level.lower(), logger.info)(json.dumps(payload))


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        settings = get_settings()
    except Exception as exc:
        _log_json(
            "error",
            "configuration_validation_failed",
            {"error": "Invalid or missing required environment configuration"},
        )
        raise RuntimeError("Configuration error") from exc

    if not settings.MASTER_ENCRYPTION_KEY:
        _log_json("error", "configuration_validation_failed", {"error": "MASTER_ENCRYPTION_KEY is missing"})
        raise RuntimeError("Configuration error")

    data_path = Path(settings.DATABASE_PATH)
    data_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        async with aiosqlite.connect(settings.DATABASE_PATH) as db:
            await db.execute("PRAGMA journal_mode = WAL")
            await db.execute("PRAGMA foreign_keys = ON")
            await executescript_file(db, str(Path(__file__).parent / "db" / "schema.sql"))
            await db.commit()
    except asyncio.CancelledError:
        # Handle graceful shutdown during reload
        raise
    except Exception as exc:
        raise DatabaseError("Failed to initialize database schema") from exc

    app.state.started_at = datetime.utcnow()
    app.state.settings = settings
    health.APP_STARTED_AT = app.state.started_at

    _log_json(
        "info",
        "application_startup",
        {"event": "startup", "app": settings.APP_NAME, "version": settings.APP_VERSION, "agents": 7},
    )
    try:
        yield
    finally:
        _log_json("info", "application_shutdown", {"event": "shutdown", "app": settings.APP_NAME})


try:
    _bootstrap_settings = get_settings()
except Exception:
    _bootstrap_settings = None

app = FastAPI(
    title=_bootstrap_settings.APP_NAME if _bootstrap_settings else "Shadow Credit",
    version=_bootstrap_settings.APP_VERSION if _bootstrap_settings else "1.0.0",
    lifespan=lifespan,
)

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.state._rate_limit_events = {}
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_bootstrap_settings.ALLOWED_ORIGINS if _bootstrap_settings else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    latency_ms = int((perf_counter() - start) * 1000)
    _log_json(
        "info",
        "http_request",
        {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )
    return response


def _limit_for_request(method: str, path: str) -> int:
    if method == "POST" and path.startswith("/api/v1/ingest/") and not path.endswith("/status"):
        return 10
    if method == "POST" and path == "/api/v1/sessions":
        return 20
    if method == "POST" and path.startswith("/api/v1/sessions/") and path.endswith("/clarify"):
        return 30
    if method == "GET" and path.startswith("/api/v1/sessions/") and "/export/" in path:
        return 5
    if method == "GET" and (path.startswith("/api/v1/verify/") or path.startswith("/verify/")):
        return 60
    return 100


@app.middleware("http")
async def endpoint_rate_limit_middleware(request: Request, call_next):
    limit_per_minute = _limit_for_request(request.method, request.url.path)
    now_ts = perf_counter()
    client = get_remote_address(request) or "unknown"
    key = f"{client}:{request.method}:{request.url.path}"
    bucket = app.state._rate_limit_events.get(key, [])
    bucket = [t for t in bucket if now_ts - t < 60.0]
    if len(bucket) >= limit_per_minute:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "data": None,
                "error": f"Rate limit exceeded. Limit: {limit_per_minute}/minute. Please wait before retrying.",
                "code": "RATE_LIMIT_EXCEEDED",
                "meta": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "retry_after_seconds": 60,
                },
            },
        )
    bucket.append(now_ts)
    app.state._rate_limit_events[key] = bucket
    return await call_next(request)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "data": None,
            "error": f"Rate limit exceeded. Limit: {exc.detail}. Please wait before retrying.",
            "code": "RATE_LIMIT_EXCEEDED",
            "meta": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "retry_after_seconds": 60,
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    _log_json(
        "error",
        "unhandled_exception",
        {"path": request.url.path, "traceback": traceback.format_exc()},
    )
    env = getattr(getattr(request.app.state, "settings", None), "ENVIRONMENT", "development")
    message = "Internal server error" if env == "production" else str(exc)
    payload = wrap_response(
        data={"error": message, "type": type(exc).__name__},
    )
    payload["success"] = False
    return JSONResponse(status_code=500, content=payload)


@app.get("/")
async def root():
    app_settings = getattr(app.state, "settings", _bootstrap_settings)
    return wrap_response(
        {
            "name": app_settings.APP_NAME if app_settings else "Shadow Credit",
            "version": app_settings.APP_VERSION if app_settings else "1.0.0",
            "agent_count": 7,
            "status": "operational",
            "docs": "/docs",
            "health": "/api/v1/health",
        }
    )


app.include_router(health.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(ingest_router, prefix="/api/v1")
app.include_router(verify_router, prefix="/api/v1")
app.include_router(websocket_router)
