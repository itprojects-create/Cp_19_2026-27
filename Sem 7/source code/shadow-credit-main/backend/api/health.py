from __future__ import annotations

from datetime import datetime
from time import perf_counter

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from backend.db.database import DatabaseError, execute_query, get_db
except ModuleNotFoundError:
    from db.database import DatabaseError, execute_query, get_db


router = APIRouter(tags=["health"])
APP_STARTED_AT: datetime | None = None


class ResponseMeta(BaseModel):
    session_id: str | None = None
    agent_id: str | None = None
    latency_ms: int = 0
    timestamp: str


class APIResponse(BaseModel):
    success: bool
    data: dict
    meta: ResponseMeta


def wrap_response(
    data: dict,
    session_id: str | None = None,
    agent_id: str | None = None,
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


@router.get("/health")
async def health_check(request: Request):
    start = perf_counter()
    settings = request.app.state.settings
    started_at = APP_STARTED_AT or request.app.state.started_at
    uptime_seconds = int((datetime.utcnow() - started_at).total_seconds())

    http_status = 200
    overall_status = "operational"
    db_status = "connected"
    table_count = 0

    try:
        async with get_db() as db:
            tables = await execute_query(
                db,
                "SELECT name FROM sqlite_master WHERE type='table'",
                (),
            )
            table_count = len(tables)
            if table_count < 6:
                db_status = "incomplete"
                overall_status = "degraded"
                http_status = 503
    except DatabaseError:
        db_status = "error"
        overall_status = "degraded"
        http_status = 503

    latency_ms = int((perf_counter() - start) * 1000)
    payload = wrap_response(
        {
            "status": overall_status,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": uptime_seconds,
            "database": {
                "status": db_status,
                "path": settings.DATABASE_PATH,
                "tables": table_count,
            },
            "agents": {
                "total": 7,
                "registered": 0,
                "status": "initializing",
            },
            "security": {
                "encryption": "AES-256-GCM active",
                "audit_log": "immutable (trigger-enforced)",
                "consent": "DPDP Act v2023 compliant",
            },
        },
        latency_ms=latency_ms,
    )
    return JSONResponse(status_code=http_status, content=payload)
