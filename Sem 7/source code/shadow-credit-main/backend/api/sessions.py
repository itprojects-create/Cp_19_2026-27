from __future__ import annotations

import asyncio
import json
import uuid
import importlib
import sys
from datetime import datetime, timedelta
from pathlib import Path
from time import perf_counter
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
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
    from backend.agents.supervisor import SupervisorAgent
    from backend.config import get_settings
    from backend.core.audit_log import AuditLogger
    from backend.core.event_bus import event_bus
    from backend.core.security import EncryptionService
    from backend.db.database import DatabaseError, execute_query, execute_write, get_db
    from backend.api.consent import execute_right_to_erasure, record_consent_receipt, require_consent
    from backend.agents.agent_06_compliance import simulate_scenario
except ModuleNotFoundError:
    _backend_root = Path(__file__).resolve().parents[1]
    if str(_backend_root) not in sys.path:
        sys.path.insert(0, str(_backend_root))
    SupervisorAgent = importlib.import_module("agents.supervisor").SupervisorAgent
    get_settings = importlib.import_module("config").get_settings
    _audit = importlib.import_module("core.audit_log")
    _event = importlib.import_module("core.event_bus")
    _security = importlib.import_module("core.security")
    _db = importlib.import_module("db.database")
    _consent = importlib.import_module("api.consent")
    simulate_scenario = importlib.import_module("agents.agent_06_compliance").simulate_scenario
    AuditLogger = _audit.AuditLogger
    event_bus = _event.event_bus
    EncryptionService = _security.EncryptionService
    DatabaseError = _db.DatabaseError
    execute_query = _db.execute_query
    execute_write = _db.execute_write
    get_db = _db.get_db
    execute_right_to_erasure = _consent.execute_right_to_erasure
    record_consent_receipt = _consent.record_consent_receipt
    require_consent = _consent.require_consent


router = APIRouter(tags=["sessions"])
limiter = Limiter(key_func=get_remote_address)


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


class CreateSessionRequest(BaseModel):
    owner_name: str
    location_district: str
    consent_given: bool
    demo_mode: bool = False


class AnalyzeSessionRequest(BaseModel):
    persona_id: str | None = None


class ClarificationResponse(BaseModel):
    clarification_id: str
    response: str | bool
    response_label: str = ""


class ScenarioRequest(BaseModel):
    scenario: Literal["current", "gst_registered", "aa_consent", "gst_plus_aa"]


async def require_consent_local(session_id: str) -> dict:
    async with get_db() as db:
        return await require_consent(session_id=session_id, db=db)


def _json_error(status_code: int, body: dict):
    response = APIResponse(
        success=False,
        data=body,
        meta=ResponseMeta(timestamp=datetime.utcnow().isoformat() + "Z"),
    ).model_dump()
    return JSONResponse(status_code=status_code, content=response)


@router.post("/sessions")
@limiter.limit("20/minute")
async def create_session(payload: CreateSessionRequest, request: Request):
    start = perf_counter()
    settings = request.app.state.settings

    if payload.consent_given is not True:
        return _json_error(
            status_code=422,
            body={
                "success": False,
                "error": (
                    "Informed consent is required under the DPDP Act 2023. "
                    "Cannot process financial data without explicit consent."
                ),
                "code": "CONSENT_REQUIRED",
            },
        )

    session_id = str(uuid.uuid4())
    now = datetime.utcnow()
    created_at = now.isoformat() + "Z"

    try:
        encryption_service = EncryptionService(settings.MASTER_ENCRYPTION_KEY)
        encrypted_name = encryption_service.encrypt(payload.owner_name)
        encrypted_name_json = json.dumps(encrypted_name, separators=(",", ":"))
        session_key_hash = encryption_service.generate_session_key_hash(session_id)
        owner_name_hash = encryption_service.hash_for_audit(payload.owner_name)
        consent_hash = encryption_service.generate_consent_hash(session_id, created_at)

        async with get_db() as db:
            await execute_write(
                db,
                """
                INSERT INTO sessions (
                    id, created_at, owner_name, location_masked, consent_given,
                    session_key_hash, status, demo_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    created_at,
                    encrypted_name_json,
                    payload.location_district,
                    1,
                    session_key_hash,
                    "PENDING",
                    1 if payload.demo_mode else 0,
                ),
            )

            audit_logger = AuditLogger(encryption_service)
            await audit_logger.log(
                db=db,
                session_id=session_id,
                agent_id="SYSTEM_API",
                action_type="SESSION_CREATED",
                input_data={"location_district": payload.location_district, "demo_mode": payload.demo_mode},
                output_data={"session_id": session_id, "consent_hash": consent_hash},
            )
            await record_consent_receipt(
                session_id=session_id,
                owner_name_hash=owner_name_hash,
                timestamp=created_at,
                db=db,
            )

        latency_ms = int((perf_counter() - start) * 1000)
        return wrap_response(
            {
                "session_id": session_id,
                "consent_hash": consent_hash,
                "expires_at": (now + timedelta(hours=24)).isoformat() + "Z",
                "demo_mode": payload.demo_mode,
                "status": "PENDING",
            },
            session_id=session_id,
            latency_ms=latency_ms,
        )
    except (DatabaseError, Exception) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions/{session_id}")
@limiter.limit("100/minute")
async def get_session(session_id: str, request: Request):
    start = perf_counter()
    import sqlite3 as _sq, os as _os
    for _p in ['backend/data/shadow_credit.db', 'data/shadow_credit.db']:
        if _os.path.exists(_p):
            _c = _sq.connect(_p)
            _c.row_factory = _sq.Row
            _cu = _c.cursor()
            _cu.execute("SELECT * FROM sessions WHERE id=?", (session_id,))
            _r = _cu.fetchone()
            if _r:
                _cu.execute("SELECT * FROM credit_assessments WHERE session_id=?", (session_id,))
                _a = _cu.fetchone()
                _cu.execute("SELECT agent_id FROM audit_log WHERE session_id=? GROUP BY agent_id", (session_id,))
                _ag = [x[0] for x in _cu.fetchall()]
                _c.close()
                from fastapi.responses import JSONResponse
                return JSONResponse({
                    "success": True,
                    "data": {
                        "session": dict(_r),
                        "assessment": dict(_a) if _a else None,
                        "audit_summary": {"agents_involved": _ag},
                    },
                    "meta": {"session_id": session_id, "latency_ms": 1}
                })
            _c.close()
            break
    try:
        async with get_db() as db:
            sessions = await execute_query(
                db,
                """
                SELECT id, created_at, owner_name, location_masked, consent_given, status, demo_mode
                FROM sessions
                WHERE id = ?
                """,
                (session_id,),
            )
            if not sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = sessions[0]
            if str(session.get("status", "")).upper() == "ERASED":
                raise HTTPException(status_code=410, detail="Session erased")
            demo_mode = int(session.get("demo_mode", 0) or 0) == 1
            if demo_mode:
                session["owner_name"] = "████████"

            summary_rows = await execute_query(
                db,
                """
                SELECT COUNT(*) AS audit_count, MAX(timestamp) AS last_action_at
                FROM audit_log
                WHERE session_id = ?
                """,
                (session_id,),
            )
            agent_rows = await execute_query(
                db,
                "SELECT DISTINCT agent_id FROM audit_log WHERE session_id = ?",
                (session_id,),
            )

        audit_summary = summary_rows[0] if summary_rows else {"audit_count": 0, "last_action_at": None}
        audit_summary["agents"] = [row["agent_id"] for row in agent_rows]

        latency_ms = int((perf_counter() - start) * 1000)
        return wrap_response({"session": session, "audit_summary": audit_summary}, session_id=session_id, latency_ms=latency_ms)
    except DatabaseError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/sessions/{session_id}")
@limiter.limit("20/minute")
async def erase_session(session_id: str, request: Request):
    start = perf_counter()
    settings = request.app.state.settings
    try:
        encryption_service = EncryptionService(settings.MASTER_ENCRYPTION_KEY)
        async with get_db() as db:
            audit_logger = AuditLogger(encryption_service)
            result = await execute_right_to_erasure(session_id=session_id, db=db, audit_logger=audit_logger)
        latency_ms = int((perf_counter() - start) * 1000)
        return wrap_response(result, session_id=session_id, latency_ms=latency_ms)
    except DatabaseError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


async def _build_demo_artifacts(session_id: str, persona_id: str):
    persona_dir = Path("data") / "personas" / persona_id
    required = {
        "WHATSAPP": persona_dir / "whatsapp.txt",
        "UPI": persona_dir / "upi_events.json",
        "KHATA": persona_dir / "khata.csv",
        "BILL": persona_dir / "bill_metadata.json",
        "MAPS": persona_dir / "maps_data.json",
    }

    missing = [f"{k}:{str(v)}" for k, v in required.items() if not v.exists()]
    if missing:
        raise HTTPException(status_code=409, detail={"error": "Persona data missing", "missing": missing})

    artifacts = []
    for artifact_type, file_path in required.items():
        artifacts.append(
            {
                "artifact_id": f"art_{uuid.uuid4().hex[:8]}",
                "artifact_type": artifact_type,
                "saved_path": str(file_path),
                "file_hash": f"demo_hash_{persona_id}_{artifact_type.lower()}",
                "agent_id": "SEED_SCRIPT",
            }
        )
    return artifacts



async def _run_supervisor_pipeline(session_id: str, persona_id: str | None, settings) -> None:
    is_demo = False
    try:
        async with get_db() as db:
            await execute_write(db, "UPDATE sessions SET status = 'PROCESSING' WHERE id = ?", (session_id,))
            rows = await execute_query(db, "SELECT id, demo_mode FROM sessions WHERE id = ? LIMIT 1", (session_id,))
            if not rows:
                return
            session = rows[0]
            is_demo = int(session.get("demo_mode", 0) or 0) == 1

            if is_demo:
                # Use realistic mock pipeline for demo mode
                from backend.api.mock_pipeline import run_mock_analysis_pipeline
                
                # Auto-resolve persona_id from location if not provided
                if not persona_id:
                    mapped = await execute_query(
                        db,
                        """
                        SELECT location_masked
                        FROM sessions
                        WHERE id = ?
                        LIMIT 1
                        """,
                        (session_id,),
                    )
                    location = str((mapped[0] or {}).get("location_masked", "") if mapped else "").lower()
                    if "sadashiv" in location:
                        persona_id = "persona01_clean"
                    elif "kothrud" in location or "kalyani" in location:
                        persona_id = "persona02_discrepancy"
                    elif "camp" in location or "pimpri" in location:
                        persona_id = "persona03_seasonal"
                    else:
                        # Default to clean persona if location doesn't match
                        persona_id = "persona01_clean"
                
                # Map persona_id to mock pipeline persona keys
                persona_map = {
                    "persona01_clean": "suresh",
                    "persona02_discrepancy": "meena",
                    "persona03_seasonal": "raju",
                }
                persona_key = persona_map.get(persona_id, "suresh")
                
                # Run the mock pipeline in background and return immediately
                asyncio.create_task(run_mock_analysis_pipeline(session_id, persona_key))
                return  # Mock pipeline handles everything, exit early

            # Real mode: fetch artifacts from database
            rows_art = await execute_query(
                db,
                """
                SELECT id, artifact_type, encrypted_path
                FROM artifacts
                WHERE session_id = ?
                ORDER BY extracted_at ASC
                """,
                (session_id,),
            )
            artifacts = [
                {
                    "artifact_id": r["id"],
                    "artifact_type": r["artifact_type"],
                    "saved_path": r["encrypted_path"],
                }
                for r in rows_art
            ]

        # Run real supervisor for non-demo mode
        supervisor = SupervisorAgent(settings=settings)
        await supervisor.run_session(session_id=session_id, artifact_records=artifacts)
    except Exception:
        async with get_db() as db:
            await execute_write(db, "UPDATE sessions SET status = 'FAILED' WHERE id = ?", (session_id,))
        raise


@router.post("/sessions/{session_id}/analyze")
@limiter.limit("30/minute")
async def analyze_session(
    session_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    body: AnalyzeSessionRequest | None = None,
    session: dict = Depends(require_consent_local),
):
    start = perf_counter()
    settings = request.app.state.settings

    async with get_db() as db:
        rows = await execute_query(
            db,
            "SELECT id, status, demo_mode FROM sessions WHERE id = ? LIMIT 1",
            (session_id,),
        )
        if not rows:
            raise HTTPException(status_code=404, detail={"error": "Session not found", "code": "SESSION_NOT_FOUND"})

        current_status = str(rows[0].get("status", "")).upper()
        if current_status == "PROCESSING":
            return JSONResponse(
                status_code=202,
                content=wrap_response(
                    {
                        "accepted": True,
                        "session_id": session_id,
                        "status": "PROCESSING",
                        "message": "Pipeline already running.",
                        "websocket_url": f"ws://localhost:8000/ws/{session_id}",
                    },
                    session_id=session_id,
                    latency_ms=int((perf_counter() - start) * 1000),
                ),
            )

        await execute_write(db, "UPDATE sessions SET status = 'PROCESSING' WHERE id = ?", (session_id,))

    background_tasks.add_task(
        _run_supervisor_pipeline,
        session_id=session_id,
        persona_id=(body.persona_id if body else None),
        settings=settings,
    )

    latency_ms = int((perf_counter() - start) * 1000)
    return JSONResponse(
        status_code=202,
        content=wrap_response(
            {
                "accepted": True,
                "session_id": session_id,
                "status": "PROCESSING",
                "message": "Analysis started. Monitor real-time progress in the WebSocket stream.",
                "websocket_url": f"ws://localhost:8000/ws/{session_id}",
            },
            session_id=session_id,
            latency_ms=latency_ms,
        ),
    )


@router.post("/sessions/{session_id}/clarify")
@limiter.limit("30/minute")
async def submit_clarification(
    session_id: str,
    request: Request,
    body: ClarificationResponse,
    background_tasks: BackgroundTasks,
    session: dict = Depends(require_consent_local),
):
    start = perf_counter()
    settings = request.app.state.settings
    encryption_service = EncryptionService(settings.MASTER_ENCRYPTION_KEY)
    supervisor = SupervisorAgent(settings=settings)

    async with get_db() as db:
        rows = await execute_query(
            db,
            "SELECT * FROM decisions WHERE id = ? AND session_id = ? LIMIT 1",
            (body.clarification_id, session_id),
        )
        if not rows:
            raise HTTPException(status_code=404, detail={"error": "Clarification not found", "code": "CLARIFICATION_NOT_FOUND"})
        decision = rows[0]
        if int(decision.get("resolved", 0) or 0) == 1:
            raise HTTPException(status_code=400, detail={"error": "Clarification already resolved"})

        await execute_write(
            db,
            "UPDATE decisions SET resolved = 1, resolution_input = ? WHERE id = ?",
            (json.dumps(body.model_dump(), separators=(",", ":")), body.clarification_id),
        )
        await AuditLogger(encryption_service).log(
            db=db,
            session_id=session_id,
            agent_id="SYSTEM_API",
            action_type="CLARIFICATION_SUBMITTED",
            input_data={
                "clarification_id": body.clarification_id,
                "response": body.response,
                "response_label": body.response_label,
            },
        )

    background_tasks.add_task(
        supervisor.resume_after_clarification,
        session_id=session_id,
        clarification_id=body.clarification_id,
        user_response=str(body.response),
    )

    latency_ms = int((perf_counter() - start) * 1000)
    return JSONResponse(
        status_code=202,
        content=wrap_response(
            {
                "resumed": True,
                "session_id": session_id,
                "clarification_id": body.clarification_id,
                "response_recorded": body.response_label or str(body.response),
                "message": "Pipeline resumed. Watch WebSocket for next agent actions.",
                "websocket_url": f"ws://localhost:8000/ws/{session_id}",
            },
            session_id=session_id,
            latency_ms=latency_ms,
        ),
    )


@router.post("/sessions/{session_id}/scenario")
@limiter.limit("30/minute")
async def run_scenario(
    session_id: str,
    request: Request,
    body: ScenarioRequest,
    session: dict = Depends(require_consent_local),
):
    start = perf_counter()
    settings = request.app.state.settings
    async with get_db() as db:
        ca_rows = await execute_query(
            db,
            """
            SELECT id, base_limit, regularity_score, concentration_risk, continuity_score,
                   final_limit, warmth_score, credit_grade, formula_json, created_at
            FROM credit_assessments
            WHERE session_id = ?
            LIMIT 1
            """,
            (session_id,),
        )
        if not ca_rows:
            raise HTTPException(
                status_code=409,
                detail={"error": "No credit assessment found for this session. Run full analysis first."},
            )

        s_rows = await execute_query(
            db,
            """
            SELECT id, consent_given, demo_mode, location_masked, status
            FROM sessions
            WHERE id = ?
            LIMIT 1
            """,
            (session_id,),
        )
        if not s_rows:
            raise HTTPException(status_code=404, detail={"error": "Session not found", "code": "SESSION_NOT_FOUND"})

    ca = ca_rows[0]
    session_data = {
        "consent_given": int(s_rows[0].get("consent_given", 0) or 0),
        "data_sources": ["WHATSAPP", "UPI", "KHATA", "BILL"],
        "days_of_data": 90,
        "upi_days_covered": 90,
        "khata_total_90d": 0.0,
        "median_monthly_inflow": float(ca.get("base_limit") or 0.0) / 3.0 if ca.get("base_limit") else 0.0,
        "income_regularity_score": float(ca.get("regularity_score") or 0.70),
        "top_customer_pct": float(ca.get("concentration_risk") or 0.50),
        "business_continuity_score": float(ca.get("continuity_score") or 0.75),
        "has_gst": False,
        "has_aa_consent": False,
        "final_credit_limit": float(ca.get("final_limit") or 0.0),
        "warmth_score": float(ca.get("warmth_score") or 0.0),
        "credit_grade": ca.get("credit_grade") or "C",
        "bill_extracted": True,
        "bill_days_old": 90,
        "maps_verified": False,
    }

    result = simulate_scenario(body.scenario, session_data, settings)
    latency_ms = int((perf_counter() - start) * 1000)
    return wrap_response(
        {
            "scenario": result["scenario"],
            "scenario_label": result["scenario_label"],
            "credit_limit": result["credit_limit"],
            "delta_from_current": result["delta_from_current"],
            "delta_pct": result["delta_pct"],
            "newly_unlocked_items": result["newly_unlocked_items"],
            "compliance_score_pct": result["compliance_score_pct"],
            "formalisation_steps": result["formalisation_steps"],
            "narrative": result["narrative"],
        },
        session_id=session_id,
        latency_ms=latency_ms,
    )


@router.get("/sessions/{session_id}/export/{format}")
@limiter.limit("5/minute")
async def export_document(
    session_id: str,
    format: str,
    request: Request,
    session: dict = Depends(require_consent_local),
):
    normalized = (format or "").strip().lower()
    valid = {"memo_pdf", "passport_pdf", "ocen_json"}
    if normalized not in valid:
        raise HTTPException(status_code=422, detail={"error": "Invalid format. Valid: memo_pdf, passport_pdf, ocen_json"})

    async with get_db() as db:
        rows = await execute_query(
            db,
            "SELECT id FROM credit_assessments WHERE session_id = ? LIMIT 1",
            (session_id,),
        )
        if not rows:
            raise HTTPException(status_code=404, detail={"error": "Document not yet generated. Run full analysis first."})
        assessment_id = str(rows[0]["id"])

    reports_dir = Path(request.app.state.settings.DATABASE_PATH).parent / "reports" / session_id
    name_map = {
        "memo_pdf": f"{assessment_id}_credit_memo.pdf",
        "passport_pdf": f"{assessment_id}_passport.pdf",
        "ocen_json": f"{assessment_id}_ocen.json",
    }
    file_path = reports_dir / name_map[normalized]
    if not file_path.exists():
        pattern_map = {
            "memo_pdf": "*_credit_memo.pdf",
            "passport_pdf": "*_passport.pdf",
            "ocen_json": "*_ocen.json",
        }
        candidates = sorted(reports_dir.glob(pattern_map[normalized]))
        if not candidates:
            raise HTTPException(status_code=404, detail={"error": "Document not yet generated. Run full analysis first."})
        file_path = candidates[-1]

    if normalized == "ocen_json":
        media_type = "application/json"
        filename = f"shadow_credit_ocen_{assessment_id[:8]}.json"
    elif normalized == "memo_pdf":
        media_type = "application/pdf"
        filename = f"shadow_credit_memo_pdf_{assessment_id[:8]}.pdf"
    else:
        media_type = "application/pdf"
        filename = f"shadow_credit_passport_pdf_{assessment_id[:8]}.pdf"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Assessment-ID": assessment_id,
            "X-Generated-By": "Shadow Credit v1.0",
            "X-DPDP-Notice": "This document contains PII. Handle per DPDP Act 2023.",
        },
    )


@router.get("/sessions")
async def list_sessions():
    import sqlite3, os
    candidates = [
        'backend/data/shadow_credit.db',
        'data/shadow_credit.db',
    ]
    conn = None
    for p in candidates:
        if os.path.exists(p):
            conn = sqlite3.connect(p)
            conn.row_factory = sqlite3.Row
            break
    if not conn:
        return {"success": True, "sessions": [], "total": 0}
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.id, s.created_at, s.owner_name,
                   s.location_masked, s.status, s.demo_mode,
                   ca.final_limit, ca.credit_grade
            FROM sessions s
            LEFT JOIN credit_assessments ca ON ca.session_id = s.id
            ORDER BY s.created_at DESC LIMIT 50
        """)
        rows = cur.fetchall()
        sessions = [{
            "id":           row[0],
            "created_at":   row[1],
            "owner_name":   row[2],
            "location":     row[3],
            "status":       row[4],
            "demo_mode":    bool(row[5]),
            "final_limit":  row[6],
            "credit_grade": row[7],
        } for row in rows]
        return {"success": True, "sessions": sessions, "total": len(sessions)}
    except Exception as e:
        return {"success": True, "sessions": [], "total": 0, "error": str(e)}
    finally:
        conn.close()


@router.get("/sessions/{session_id}/direct")
async def get_session_direct(session_id: str):
    import sqlite3
    candidates = [
        'backend/data/shadow_credit.db',
        'data/shadow_credit.db',
    ]
    for p in candidates:
        import os
        if os.path.exists(p):
            conn = sqlite3.connect(p)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM sessions WHERE id=?", (session_id,))
            row = cur.fetchone()
            if row:
                cur.execute("SELECT * FROM credit_assessments WHERE session_id=?", (session_id,))
                ca = cur.fetchone()
                conn.close()
                return {
                    "success": True,
                    "session": dict(row),
                    "assessment": dict(ca) if ca else None,
                }
            conn.close()
    return {"detail": "Session not found"}
