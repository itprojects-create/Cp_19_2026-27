from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from copy import deepcopy
from datetime import datetime


class EventBusError(Exception):
    pass


logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, event_type: str, payload: dict) -> None:
        required = {"event_type", "session_id", "timestamp", "data"}
        if not isinstance(payload, dict):
            raise EventBusError("payload must be a dict")
        missing = sorted(required.difference(payload.keys()))
        if missing:
            raise EventBusError(f"payload missing required keys: {missing}")

        async with self._lock:
            subscribers = list(self._subscribers.get(event_type, []))

        for queue in subscribers:
            try:
                queue.put_nowait(deepcopy(payload))
            except asyncio.QueueFull:
                continue

        logger.debug(
            "event_published event_type=%s session_id=%s",
            event_type,
            payload.get("session_id"),
        )

    def subscribe(self, event_type: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers[event_type].append(queue)
        return queue

    def unsubscribe(self, event_type: str, queue: asyncio.Queue) -> None:
        subscribers = self._subscribers.get(event_type)
        if not subscribers:
            return
        try:
            subscribers.remove(queue)
        except ValueError:
            return

    async def publish_agent_event(
        self,
        session_id: str,
        agent_id: str,
        status: str,
        message: str = "",
        data: dict = None,
        confidence: float = None,
        latency_ms: int = None,
    ) -> None:
        event_type = f"AGENT_{status}"
        payload = {
            "event_type": event_type,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": {
                "agent_id": agent_id,
                "status": status,
                "message": message,
                "confidence": confidence,
                "latency_ms": latency_ms,
                "payload": data or {},
            },
        }
        await self.publish(event_type, payload)


event_bus = EventBus()
