from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
except ModuleNotFoundError:
    class Limiter:  # pragma: no cover - fallback when slowapi missing
        def __init__(self, key_func=None):
            self.key_func = key_func

        def limit(self, _rule: str):
            def decorator(fn):
                return fn

            return decorator

    def get_remote_address(request):
        return getattr(getattr(request, "client", None), "host", "unknown")

try:
    from backend.agents import AgentOutput
    from backend.agents.supervisor import SupervisorAgent
    from backend.config import get_settings
    from backend.core.audit_log import AuditLogger
    from backend.core.event_bus import event_bus
    from backend.core.security import EncryptionService
    from backend.db.database import execute_query, execute_write, get_db
    from backend.api.sessions import wrap_response
except ModuleNotFoundError:
    from agents import AgentOutput
    from agents.supervisor import SupervisorAgent
    from config import get_settings
    from core.audit_log import AuditLogger
    from core.event_bus import event_bus
    from core.security import EncryptionService
    from db.database import execute_query, execute_write, get_db
    from api.sessions import wrap_response

try:
    from backend.agents.agent_01_ocr import OCRIngestionAgent
    from backend.agents.agent_02_whatsapp import WhatsAppParserAgent
    from backend.agents.agent_03_khata import KhataBookAgent
except ModuleNotFoundError:
    from agents.agent_01_ocr import OCRIngestionAgent
    from agents.agent_02_whatsapp import WhatsAppParserAgent
    from agents.agent_03_khata import KhataBookAgent


logger = logging.getLogger(__name__)
router = APIRouter(tags=["ingestion"])
limiter = Limiter(key_func=get_remote_address)
settings = get_settings()


ALLOWED_EXTENSIONS = {".txt", ".jpg", ".jpeg", ".png", ".csv", ".pdf"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
MAX_FILES_PER_REQUEST = 10

ARTIFACT_TYPE_TO_AGENT = {
    "WHATSAPP": "AGENT_02_WHATSAPP",
    "UPI": "AGENT_01_OCR",
    "BILL": "AGENT_01_OCR",
    "INVOICE": "AGENT_01_OCR",
    "RECEIPT": "AGENT_01_OCR",
    "KHATA": "AGENT_03_KHATA",
}
VALID_ARTIFACT_TYPES = set(ARTIFACT_TYPE_TO_AGENT.keys())


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_upload_file(file: UploadFile, artifact_type: str) -> None:
    """
    Validates a single uploaded file before processing.
    """
    if not (file.filename or "").strip():
        raise HTTPException(status_code=400, detail="Empty filename")

    normalized_type = (artifact_type or "").strip().upper()
    if normalized_type not in VALID_ARTIFACT_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid artifact_type: {artifact_type}")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail=f"Unsupported extension for {file.filename}: {extension}")

    size_header = file.headers.get("content-length") if file.headers else None
    if size_header:
        try:
            if int(size_header) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(status_code=422, detail=f"Header size exceeds 20MB for {file.filename}")
        except ValueError:
            pass


async def save_artifact_to_disk(
    file: UploadFile,
    session_id: str,
    artifact_id: str,
    settings_obj,
) -> tuple[str, str, int]:
    """
    Reads file bytes, saves to disk, returns (file_hash, saved_path, file_size_bytes).
    """
    content = await file.read()
    size_bytes = len(content)
    if size_bytes > MAX_FILE_SIZE_BYTES:
        size_mb = size_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File {file.filename} exceeds 20MB limit ({size_mb:.1f}MB)",
        )

    sha256_hash = hashlib.sha256(content).hexdigest()
    base_dir = Path(settings_obj.DATABASE_PATH).resolve().parent
    save_dir = base_dir / "artifacts" / session_id / artifact_id
    save_dir.mkdir(parents=True, exist_ok=True)
    extension = Path(file.filename or "upload.bin").suffix.lower() or ".bin"
    save_path = save_dir / f"{artifact_id}{extension}"
    save_path.write_bytes(content)
    return sha256_hash, str(save_path), size_bytes


async def register_artifact_in_db(
    db,
    artifact_id: str,
    session_id: str,
    artifact_type: str,
    file_hash: str,
    encrypted_path: str,
    agent_id: str,
    audit_logger: AuditLogger,
    filename: str,
) -> None:
    """
    Inserts artifact record into artifacts table and logs to audit_log.
    """
    store_type = "BILL" if artifact_type in {"INVOICE", "RECEIPT"} else artifact_type
    try:
        await execute_write(
            db,
            """
            INSERT INTO artifacts (
                id, session_id, artifact_type, file_hash, encrypted_path,
                ocr_confidence, extracted_at, agent_id, processing_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                session_id,
                store_type,
                file_hash,
                encrypted_path,
                None,
                None,
                agent_id,
                "PROCESSING",
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to register artifact: {exc}") from exc

    await audit_logger.log(
        db=db,
        session_id=session_id,
        agent_id="INGEST_API",
        action_type="ARTIFACT_UPLOADED",
        input_data={"filename": filename, "artifact_type": artifact_type, "file_hash": file_hash},
        output_data={"artifact_id": artifact_id, "saved_path": encrypted_path},
    )


def estimate_processing_time(artifacts: list[dict]) -> int:
    """
    Returns rough estimate of seconds for the pipeline to complete.
    """
    total = 5
    for art in artifacts:
        kind = str(art.get("artifact_type", "")).upper()
        if kind == "WHATSAPP":
            total += 15
        elif kind in {"UPI", "BILL", "INVOICE", "RECEIPT"}:
            total += 8
        elif kind == "KHATA":
            total += 3
    return int(min(90, total))


class _CompatibleEventBus:
    def __init__(self, delegate):
        self._delegate = delegate

    async def publish(self, event_type_or_payload, payload: dict | None = None):
        if isinstance(event_type_or_payload, dict) and payload is None:
            p = event_type_or_payload
            event_type = p.get("event_type", "AGENT_PROGRESS")
            mapped = {
                "event_type": event_type,
                "session_id": p.get("session_id", ""),
                "timestamp": p.get("timestamp", _utc_iso()),
                "data": p,
            }
            await self._delegate.publish(event_type, mapped)
            return
        await self._delegate.publish(event_type_or_payload, payload or {})

    async def publish_agent_event(self, *args, **kwargs):
        await self._delegate.publish_agent_event(*args, **kwargs)

    def subscribe(self, *args, **kwargs):
        return self._delegate.subscribe(*args, **kwargs)

    def unsubscribe(self, *args, **kwargs):
        return self._delegate.unsubscribe(*args, **kwargs)


class _CompatibleAuditLogger:
    def __init__(self, delegate: AuditLogger):
        self._delegate = delegate

    async def log(self, db, session_id: str, agent_id: str, *args, **kwargs):
        action_type = kwargs.pop("action_type", None) or kwargs.pop("event_type", None) or "AGENT_EVENT"
        input_data = kwargs.pop("input_data", None)
        output_data = kwargs.pop("output_data", None) or kwargs.pop("details", None)
        confidence_score = kwargs.pop("confidence_score", None)
        latency_ms = kwargs.pop("latency_ms", None)
        return await self._delegate.log(
            db=db,
            session_id=session_id,
            agent_id=agent_id,
            action_type=action_type,
            input_data=input_data,
            output_data=output_data,
            confidence_score=confidence_score,
            latency_ms=latency_ms,
        )


@router.post("/ingest/{session_id}", status_code=202)
@limiter.limit("10/minute")
async def ingest_files(
    session_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    artifact_types: List[str] = Form(...),
    metadata: Optional[str] = Form(None),
):
    """
    Accepts multipart file upload and starts async ingestion pipeline.
    """
    start = time.perf_counter()

    async with get_db() as db:
        session_rows = await execute_query(
            db,
            "SELECT id, status, consent_given, demo_mode FROM sessions WHERE id = ?",
            (session_id,),
        )
        if not session_rows:
            raise HTTPException(status_code=404, detail={"error": "Session not found", "code": "SESSION_NOT_FOUND"})
        session = session_rows[0]
        if session.get("status") == "ERASED":
            raise HTTPException(status_code=410, detail={"error": "Session has been erased per DPDP Act request"})
        if int(session.get("consent_given", 0)) == 0:
            raise HTTPException(status_code=403, detail={"error": "Consent not recorded for this session"})

    if len(files) == 0:
        raise HTTPException(status_code=422, detail={"error": "No files uploaded"})
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=422,
            detail={"error": f"Too many files: {len(files)} uploaded, max allowed {MAX_FILES_PER_REQUEST}"},
        )
    if len(files) != len(artifact_types):
        raise HTTPException(
            status_code=422,
            detail={"error": f"Mismatch: {len(files)} files but {len(artifact_types)} artifact_types"},
        )

    validation_errors: list[str] = []
    normalized_types: list[str] = []
    for f, t in zip(files, artifact_types):
        norm_t = (t or "").strip().upper()
        normalized_types.append(norm_t)
        try:
            validate_upload_file(f, norm_t)
        except HTTPException as exc:
            if isinstance(exc.detail, dict):
                validation_errors.append(str(exc.detail.get("error", exc.detail)))
            else:
                validation_errors.append(str(exc.detail))
    if validation_errors:
        raise HTTPException(status_code=422, detail={"errors": validation_errors})

    metadata_obj = {}
    if metadata:
        try:
            parsed = json.loads(metadata)
            if isinstance(parsed, dict):
                metadata_obj = parsed
        except Exception:
            metadata_obj = {}

    ingestion_id = str(uuid.uuid4())
    encryption_service = EncryptionService(settings.MASTER_ENCRYPTION_KEY)
    audit_logger = AuditLogger(encryption_service)
    artifacts_registered: list[dict] = []

    for file, artifact_type in zip(files, normalized_types):
        artifact_id = str(uuid.uuid4())
        file_hash, saved_path, file_size = await save_artifact_to_disk(file, session_id, artifact_id, settings)

        async with get_db() as db:
            await register_artifact_in_db(
                db=db,
                artifact_id=artifact_id,
                session_id=session_id,
                artifact_type=artifact_type,
                file_hash=file_hash,
                encrypted_path=saved_path,
                agent_id=ARTIFACT_TYPE_TO_AGENT[artifact_type],
                audit_logger=audit_logger,
                filename=file.filename or "unknown",
            )
            await audit_logger.log(
                db=db,
                session_id=session_id,
                agent_id="INGEST_API",
                action_type="INGEST_METADATA",
                input_data={"artifact_id": artifact_id},
                output_data={"metadata": metadata_obj},
            )

        artifacts_registered.append(
            {
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "filename": file.filename or "unknown",
                "file_size_kb": round(file_size / 1024, 2),
                "saved_path": saved_path,
                "status": "PROCESSING",
            }
        )

    background_tasks.add_task(
        run_ingestion_pipeline,
        session_id=session_id,
        artifacts=artifacts_registered,
        ingestion_id=ingestion_id,
    )

    payload = {
        "ingestion_id": ingestion_id,
        "session_id": session_id,
        "artifact_count": len(files),
        "artifacts": [
            {
                "artifact_id": a["artifact_id"],
                "artifact_type": a["artifact_type"],
                "filename": a["filename"],
                "file_size_kb": a["file_size_kb"],
                "status": "PROCESSING",
            }
            for a in artifacts_registered
        ],
        "message": "Processing started. Connect to WebSocket for live updates.",
        "websocket_url": f"ws://localhost:8000/ws/{session_id}",
        "estimated_seconds": estimate_processing_time(artifacts_registered),
    }
    latency_ms = int((time.perf_counter() - start) * 1000)
    return wrap_response(payload, session_id=session_id, agent_id="INGEST_API", latency_ms=latency_ms)


async def run_whatsapp_agents(
    session_id: str,
    artifacts: list[dict],
    agent: WhatsAppParserAgent,
) -> list[AgentOutput]:
    """
    Runs WhatsApp parser per artifact and returns AgentOutput list.
    """
    if not artifacts:
        return []
    outputs: list[AgentOutput] = []

    async with get_db() as db:
        for artifact in artifacts:
            try:
                content = Path(artifact["saved_path"]).read_text(encoding="utf-8", errors="replace")
                inputs = {"file_content": content, "file_path": artifact["saved_path"]}
                out = await agent.run(db, session_id, inputs)
                if isinstance(out.data, dict):
                    out.data["artifact_id"] = artifact.get("artifact_id")
                outputs.append(out)
            except Exception as exc:
                outputs.append(
                    AgentOutput(
                        agent_id=agent.agent_id,
                        agent_name=agent.name,
                        session_id=session_id,
                        success=False,
                        data={"artifact_id": artifact.get("artifact_id", "")},
                        confidence_score=0.0,
                        latency_ms=0,
                        errors=[f"File read error: {exc}"],
                        warnings=[],
                        fallback_used=False,
                    )
                )
    return outputs


async def run_ocr_agents(
    session_id: str,
    artifacts: list[dict],
    agent: OCRIngestionAgent,
) -> list[AgentOutput]:
    """
    Runs OCR artifacts sequentially to avoid PaddleOCR thread-safety issues.
    """
    if not artifacts:
        return []
    outputs: list[AgentOutput] = []

    async with get_db() as db:
        for artifact in artifacts:
            normalized_type = "BILL" if artifact["artifact_type"] in {"INVOICE", "RECEIPT"} else artifact["artifact_type"]
            inputs = {
                "image_path": artifact["saved_path"],
                "artifact_type": normalized_type,
                "artifact_id": artifact["artifact_id"],
            }
            out = await agent.run(db, session_id, inputs)
            outputs.append(out)
    return outputs


async def run_khata_agents(
    session_id: str,
    artifacts: list[dict],
    agent: KhataBookAgent,
) -> list[AgentOutput]:
    """
    Runs Khata parser per artifact and returns AgentOutput list.
    """
    if not artifacts:
        return []
    outputs: list[AgentOutput] = []

    async with get_db() as db:
        for artifact in artifacts:
            saved_path = artifact["saved_path"]
            content = None
            for enc in ("utf-8", "utf-8-sig", "latin-1"):
                try:
                    content = Path(saved_path).read_text(encoding=enc, errors="strict")
                    break
                except Exception:
                    continue
            if content is None:
                content = Path(saved_path).read_text(encoding="utf-8", errors="replace")

            inputs = {
                "file_content": content,
                "file_path": saved_path,
                "artifact_id": artifact["artifact_id"],
            }
            out = await agent.run(db, session_id, inputs)
            outputs.append(out)
    return outputs


async def run_ingestion_pipeline(
    session_id: str,
    artifacts: list[dict],
    ingestion_id: str,
) -> None:
    try:
        supervisor = SupervisorAgent(settings=settings)
        final_state = await supervisor.run_session(session_id=session_id, artifact_records=artifacts)
        async with get_db() as db:
            await execute_write(
                db,
                "UPDATE sessions SET status = ? WHERE id = ?",
                ("COMPLETE" if final_state.pipeline_complete else "PROCESSING", session_id),
            )
    except Exception as exc:
        logger.exception("Ingestion pipeline crashed for session %s", session_id)
        try:
            async with get_db() as db:
                await execute_write(db, "UPDATE sessions SET status = 'FAILED' WHERE id = ?", (session_id,))
                await AuditLogger(EncryptionService(settings.MASTER_ENCRYPTION_KEY)).log(
                    db=db,
                    session_id=session_id,
                    agent_id="INGEST_PIPELINE",
                    action_type="AGENT_ERROR",
                    output_data={"error": str(exc)},
                )
            await event_bus.publish_agent_event(
                session_id=session_id,
                agent_id="INGEST_PIPELINE",
                status="ERROR",
                message=str(exc),
            )
        except Exception:
            logger.exception("Failed to mark ingestion pipeline failure for session %s", session_id)


@router.get("/ingest/{session_id}/status")
async def get_ingestion_status(session_id: str):
    """
    Returns current ingestion status with artifact and audit rollups.
    """
    async with get_db() as db:
        session_rows = await execute_query(
            db,
            "SELECT id, status, created_at, demo_mode FROM sessions WHERE id = ?",
            (session_id,),
        )
        if not session_rows:
            raise HTTPException(status_code=404, detail="Session not found")
        session = session_rows[0]

        artifact_rows = await execute_query(
            db,
            """
            SELECT id, artifact_type, processing_status, ocr_confidence, extracted_at, encrypted_path
            FROM artifacts
            WHERE session_id = ?
            ORDER BY extracted_at ASC
            """,
            (session_id,),
        )

        artifacts: list[dict] = []
        total_extractions = 0
        for row in artifact_rows:
            ext_count_rows = await execute_query(
                db,
                "SELECT COUNT(*) as cnt FROM extractions WHERE artifact_id = ?",
                (row["id"],),
            )
            ext_count = int(ext_count_rows[0]["cnt"]) if ext_count_rows else 0
            total_extractions += ext_count
            artifacts.append(
                {
                    "artifact_id": row["id"],
                    "artifact_type": row["artifact_type"],
                    "processing_status": row["processing_status"],
                    "ocr_confidence": row["ocr_confidence"],
                    "extraction_count": ext_count,
                    "extracted_at": row["extracted_at"],
                    "saved_path": None if int(session.get("demo_mode", 0)) == 1 else row.get("encrypted_path"),
                }
            )

        audit_rows = await execute_query(
            db,
            """
            SELECT agent_id, action_type, timestamp
            FROM audit_log
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT 5
            """,
            (session_id,),
        )

    agents_active = list({row["agent_id"] for row in audit_rows if row.get("agent_id")})
    last_activity = audit_rows[0]["timestamp"] if audit_rows else None
    terminal_states = {"COMPLETE", "FAILED"}
    pipeline_complete = bool(artifacts) and all(a["processing_status"] in terminal_states for a in artifacts)

    payload = {
        "session_id": session_id,
        "session_status": session["status"],
        "artifacts": [
            {k: v for k, v in a.items() if k != "saved_path"} if int(session.get("demo_mode", 0)) == 1 else a
            for a in artifacts
        ],
        "total_extractions": total_extractions,
        "agents_active": agents_active,
        "last_activity": last_activity,
        "pipeline_complete": pipeline_complete,
    }
    return wrap_response(payload, session_id=session_id, agent_id="INGEST_API", latency_ms=0)
