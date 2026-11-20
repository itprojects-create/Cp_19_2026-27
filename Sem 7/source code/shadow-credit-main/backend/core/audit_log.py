from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

try:
    from backend.core.security import EncryptionService
    from backend.db.database import DatabaseError, execute_query, execute_write
except ModuleNotFoundError:
    from core.security import EncryptionService
    from db.database import DatabaseError, execute_query, execute_write


class AuditWriteError(Exception):
    pass


class AuditLogger:
    def __init__(self, encryption_service: EncryptionService):
        self.encryption_service = encryption_service

    async def log(
        self,
        db,
        session_id: str,
        agent_id: str,
        action_type: str,
        input_data: Any = None,
        output_data: Any = None,
        confidence_score: float = None,
        latency_ms: int = None,
    ) -> str:
        entry_id = str(uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        input_serialized = None
        output_serialized = None
        input_hash = None
        output_hash = None

        if input_data is not None:
            input_serialized = json.dumps(input_data, default=str, sort_keys=True)
            input_hash = self.encryption_service.hash_for_audit(input_serialized)
        if output_data is not None:
            output_serialized = json.dumps(output_data, default=str, sort_keys=True)
            output_hash = self.encryption_service.hash_for_audit(output_serialized)

        try:
            await execute_write(
                db,
                """
                INSERT INTO audit_log (
                    id,
                    session_id,
                    agent_id,
                    action_type,
                    input_hash,
                    output_hash,
                    confidence_score,
                    latency_ms,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    session_id,
                    agent_id,
                    action_type,
                    input_hash,
                    output_hash,
                    confidence_score,
                    latency_ms,
                    timestamp,
                ),
            )
            return entry_id
        except DatabaseError as exc:
            cause = exc.__cause__
            if isinstance(cause, sqlite3.IntegrityError) and "immutable" in str(cause).lower():
                raise
            raise AuditWriteError("failed to write audit log entry") from exc

    async def get_session_trail(self, db, session_id: str) -> list[dict]:
        try:
            return await execute_query(
                db,
                """
                SELECT
                    id,
                    session_id,
                    agent_id,
                    action_type,
                    input_hash,
                    output_hash,
                    confidence_score,
                    latency_ms,
                    timestamp
                FROM audit_log
                WHERE session_id = ?
                ORDER BY timestamp ASC
                """,
                (session_id,),
            )
        except DatabaseError as exc:
            raise AuditWriteError("failed to fetch session audit trail") from exc

    async def get_agent_summary(self, db, session_id: str) -> dict:
        trail = await self.get_session_trail(db, session_id)
        summary: dict[str, dict[str, Any]] = {}

        for row in trail:
            agent_id = row["agent_id"]
            if agent_id not in summary:
                summary[agent_id] = {
                    "actions": [],
                    "total_latency_ms": 0,
                    "avg_confidence": 0.0,
                    "started_at": None,
                    "completed_at": None,
                    "_conf_values": [],
                }

            bucket = summary[agent_id]
            bucket["actions"].append(row["action_type"])

            latency = row.get("latency_ms")
            if isinstance(latency, int):
                bucket["total_latency_ms"] += latency

            conf = row.get("confidence_score")
            if isinstance(conf, (int, float)):
                bucket["_conf_values"].append(float(conf))

            ts = row.get("timestamp")
            if bucket["started_at"] is None or (ts is not None and ts < bucket["started_at"]):
                bucket["started_at"] = ts
            if bucket["completed_at"] is None or (ts is not None and ts > bucket["completed_at"]):
                bucket["completed_at"] = ts

        for agent_id, bucket in summary.items():
            conf_values = bucket.pop("_conf_values")
            bucket["avg_confidence"] = (
                round(sum(conf_values) / len(conf_values), 4) if conf_values else 0.0
            )

        return summary
