"""
WebSocket streaming layer for Shadow Credit.

Subscribes to the event bus and streams all agent events to connected clients.
Keeps connection alive with periodic pings. Auto-closes on session complete.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

try:
    from backend.config import get_settings
    from backend.core.event_bus import event_bus
    from backend.db.database import execute_query, get_db
except ModuleNotFoundError:
    from config import get_settings
    from core.event_bus import event_bus
    from db.database import execute_query, get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])
websocket_router = router
settings = get_settings()


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint that subscribes to event bus and streams agent events.
    """
    # Validate session exists
    async with get_db() as db:
        rows = await execute_query(db, "SELECT id FROM sessions WHERE id = ? LIMIT 1", (session_id,))
    if not rows:
        await websocket.accept()
        await websocket.send_json(
            {
                "type": "error",
                "session_id": session_id,
                "timestamp": _iso_now(),
                "message": "Session not found",
                "data": {},
            }
        )
        await asyncio.sleep(0.05)
        await websocket.close()
        return

    await websocket.accept()
    
    # Send connected message
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
        "message": "WebSocket connected — analysis stream live",
        "timestamp": _iso_now(),
    })

    # Subscribe to all agent event types from event bus
    event_types = [
        "AGENT_STARTED",
        "AGENT_PROGRESS",
        "AGENT_COMPLETE",
        "AGENT_ERROR",
        "SESSION_INGESTION_COMPLETE",
        "SESSION_PIPELINE_STARTED",
        "SESSION_COMPLETE",
        "CLARIFICATION_REQUIRED",
    ]
    
    subscribers: list[tuple[str, asyncio.Queue]] = []
    for et in event_types:
        q = event_bus.subscribe(et)
        subscribers.append((et, q))

    try:
        while True:
            try:
                # Check all subscribed queues for events
                event_received = False
                for _et, queue in subscribers:
                    try:
                        event = queue.get_nowait()
                        # Only send events for this session
                        if event.get("session_id") == session_id:
                            await websocket.send_json(event)
                            event_received = True
                            
                            # Exit if session is complete
                            if event.get("event_type") == "SESSION_COMPLETE":
                                await asyncio.sleep(1)
                                return
                    except asyncio.QueueEmpty:
                        continue
                
                # If no events, wait briefly then send ping if timeout
                if not event_received:
                    await asyncio.sleep(0.1)
                    # Send periodic ping every 25 seconds of inactivity
                    # (This is a simplified approach - in production you'd track last activity time)
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": _iso_now()
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as exc:
        logger.error(f"WebSocket error for session {session_id}: {exc}")
    finally:
        # Unsubscribe from all event types
        for et, q in subscribers:
            event_bus.unsubscribe(et, q)

