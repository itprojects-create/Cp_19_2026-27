"""
DPDP Act 2023 consent enforcement layer.

This module provides:
1. A FastAPI dependency that blocks processing without valid consent.
2. Consent receipt recording for immutable evidence.
3. Right-to-erasure execution that removes personal identifiers while preserving
   statutory financial audit records.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import Depends, HTTPException, Path as PathParam

try:
    from backend.config import get_settings
    from backend.core.security import EncryptionService, generate_dpdp_consent_receipt
    from backend.db.database import execute_query, execute_write, get_db
except ModuleNotFoundError:
    from config import get_settings
    from core.security import EncryptionService, generate_dpdp_consent_receipt
    from db.database import execute_query, execute_write, get_db


async def require_consent(
    session_id: str = PathParam(...),
    db=Depends(get_db),
) -> dict:
    rows = await execute_query(
        db,
        "SELECT * FROM sessions WHERE id = ? LIMIT 1",
        (session_id,),
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail={"error": "Session not found", "code": "SESSION_NOT_FOUND"},
        )

    session = rows[0]
    if str(session.get("status", "")).upper() == "ERASED":
        raise HTTPException(
            status_code=410,
            detail={
                "error": "This session has been erased per the Data Principal's right to erasure request under DPDP Act 2023, Section 12.",
                "code": "SESSION_ERASED",
                "note": "The financial audit trail has been preserved per RBI record-keeping requirements. Personal identifiers have been removed.",
            },
        )

    if int(session.get("consent_given", 0) or 0) != 1:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Informed consent is required under the Digital Personal Data Protection Act 2023, Section 6. Cannot process financial data without explicit prior consent.",
                "code": "CONSENT_REQUIRED",
                "legal_basis": "DPDP Act 2023, S.6: A Data Fiduciary shall not process personal data unless consent has been given by the Data Principal.",
            },
        )
    return session


async def record_consent_receipt(
    session_id: str,
    owner_name_hash: str,
    timestamp: str,
    db,
) -> str:
    receipt = generate_dpdp_consent_receipt(
        session_id=session_id,
        owner_name_hash=owner_name_hash,
        timestamp=timestamp,
        data_purposes=["credit_assessment", "document_generation"],
    )
    await execute_write(
        db,
        """
        INSERT INTO audit_log
        (id, session_id, agent_id, action_type, input_hash, output_hash, confidence_score, latency_ms, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            receipt["receipt_id"],
            session_id,
            "SYSTEM_CONSENT",
            "DPDP_CONSENT_RECORDED",
            None,
            EncryptionService(get_settings().MASTER_ENCRYPTION_KEY).hash_for_audit(json.dumps(receipt, sort_keys=True)),
            1.0,
            0,
            timestamp,
        ),
    )
    return receipt["receipt_id"]


async def execute_right_to_erasure(
    session_id: str,
    db,
    audit_logger,
) -> dict:
    settings = get_settings()
    security = EncryptionService(settings.MASTER_ENCRYPTION_KEY)
    now_iso = datetime.utcnow().isoformat() + "Z"

    session_rows = await execute_query(db, "SELECT id FROM sessions WHERE id = ? LIMIT 1", (session_id,))
    if not session_rows:
        raise HTTPException(status_code=404, detail="Session not found")

    artifacts = await execute_query(
        db,
        "SELECT id, encrypted_path FROM artifacts WHERE session_id = ?",
        (session_id,),
    )
    artifact_ids = [a["id"] for a in artifacts]
    erased_artifacts = len(artifact_ids)

    deleted_extractions = 0
    if artifact_ids:
        placeholders = ",".join("?" for _ in artifact_ids)
        count_rows = await execute_query(
            db,
            f"SELECT COUNT(*) AS c FROM extractions WHERE artifact_id IN ({placeholders})",
            tuple(artifact_ids),
        )
        deleted_extractions = int((count_rows[0].get("c") if count_rows else 0) or 0)
        await execute_write(
            db,
            f"DELETE FROM extractions WHERE artifact_id IN ({placeholders})",
            tuple(artifact_ids),
        )

    erased_payload = json.dumps(security.encrypt("ERASED"), separators=(",", ":"))
    await execute_write(
        db,
        """
        UPDATE sessions
        SET owner_name = ?, location_masked = ?, status = 'ERASED'
        WHERE id = ?
        """,
        (erased_payload, "LOCATION_ERASED", session_id),
    )

    await execute_write(
        db,
        """
        UPDATE artifacts
        SET encrypted_path = '', processing_status = 'FAILED'
        WHERE session_id = ?
        """,
        (session_id,),
    )

    await execute_write(
        db,
        "UPDATE credit_assessments SET ocen_payload = NULL WHERE session_id = ?",
        (session_id,),
    )

    data_root = Path(settings.DATABASE_PATH).parent
    for a in artifacts:
        p = str(a.get("encrypted_path") or "").strip()
        if not p:
            continue
        candidate = Path(p)
        if not candidate.is_absolute():
            candidate = (data_root / candidate).resolve()
        try:
            if candidate.exists() and candidate.is_file():
                os.remove(candidate)
        except Exception:
            pass

    output_data = {
        "erased_artifacts": erased_artifacts,
        "deleted_extractions": deleted_extractions,
        "timestamp": now_iso,
        "legal_basis": "DPDP Act 2023 S.12 + RBI Record-Keeping Master Direction",
    }
    await audit_logger.log(
        db=db,
        session_id=session_id,
        agent_id="SYSTEM_CONSENT",
        action_type="RIGHT_TO_ERASURE_EXECUTED",
        output_data=output_data,
    )

    return {
        "erased": True,
        "session_id": session_id,
        "erased_at": now_iso,
        "erased_artifacts": erased_artifacts,
        "deleted_extractions": deleted_extractions,
        "preserved_records": ["audit_log", "credit_assessment_amounts"],
        "legal_basis": "DPDP Act 2023 S.12 + RBI Record-Keeping Master Direction",
        "note": "Personal identifiers removed. Financial audit trail preserved per RBI MSME regulations.",
    }
