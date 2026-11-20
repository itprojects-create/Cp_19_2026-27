from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

try:
    from backend.config import get_settings
    from backend.core.security import EncryptionService
    from backend.db.database import execute_query, get_db
except ModuleNotFoundError:
    from config import get_settings
    from core.security import EncryptionService
    from db.database import execute_query, get_db


router = APIRouter(tags=["verification"])


def limit_band(final_limit: float) -> str:
    value = float(final_limit or 0.0)
    if value <= 50_000:
        return "Up to ₹50,000"
    if value <= 1_00_000:
        return "₹50,001 – ₹1,00,000"
    if value <= 2_00_000:
        return "₹1,00,001 – ₹2,00,000"
    if value <= 3_00_000:
        return "₹2,00,001 – ₹3,00,000"
    if value <= 5_00_000:
        return "₹3,00,001 – ₹5,00,000"
    return "Above ₹5,00,000"


@router.get("/verify/{assessment_id}", response_model=None)
async def verify_assessment(assessment_id: str):
    settings = get_settings()
    security_service = EncryptionService(settings.MASTER_ENCRYPTION_KEY)
    now_iso = datetime.utcnow().isoformat() + "Z"

    async with get_db() as db:
        rows = await execute_query(
            db,
            """
            SELECT
                ca.id,
                ca.session_id,
                ca.credit_grade,
                ca.warmth_score,
                ca.final_limit,
                ca.created_at,
                ca.pdf_hash_sha256,
                s.demo_mode,
                s.location_masked,
                s.status
            FROM credit_assessments ca
            JOIN sessions s ON ca.session_id = s.id
            WHERE ca.id = ? OR ca.session_id = ?
            LIMIT 1
            """,
            (assessment_id, assessment_id),
        )

    if not rows:
        return JSONResponse(
            status_code=404,
            content={
                "valid": False,
                "error": "Assessment not found",
                "assessment_id": assessment_id,
            },
        )

    row = rows[0]
    stored_hash = row.get("pdf_hash_sha256")
    session_id = row["session_id"]

    reports_root = Path(settings.DATABASE_PATH).parent / "reports" / session_id
    pdf_path = reports_root / f"{assessment_id}_credit_memo.pdf"
    if not pdf_path.exists():
        alt = reports_root.glob("*_credit_memo.pdf")
        pdf_path = next(iter(alt), pdf_path)

    hash_verified = False
    note = "No stored PDF hash"
    if stored_hash:
        if pdf_path.exists():
            try:
                hash_verified = security_service.verify_pdf_integrity(str(pdf_path), stored_hash)
                note = "SHA-256 of original PDF matches stored hash" if hash_verified else "PDF hash mismatch — possible tampering"
            except FileNotFoundError:
                hash_verified = False
                note = "PDF not found on server"
        else:
            note = "PDF not found on server"

    demo_mode = bool(int(row.get("demo_mode", 0) or 0))
    warmth_value = row.get("warmth_score")
    return {
        "valid": True,
        "assessment_id": assessment_id,
        "verified_at": now_iso,
        "document_integrity": {
            "hash_verified": bool(hash_verified),
            "hash_prefix": f"{str(stored_hash)[:16]}..." if stored_hash else None,
            "generated_at": row.get("created_at"),
            "note": note,
        },
        "credit_profile": {
            "grade": row.get("credit_grade"),
            "warmth_score": "REDACTED" if demo_mode else (round(float(warmth_value), 3) if warmth_value is not None else None),
            "recommended_limit_band": limit_band(float(row.get("final_limit") or 0.0)),
            "location": row.get("location_masked"),
            "assessment_date": str(row.get("created_at") or "")[:10],
            "status": row.get("status"),
        },
        "issuer": {
            "system": "Shadow Credit v1.0",
            "agents": 7,
            "compliance": "RBI MSME Framework 2025 + DPDP Act 2023",
            "verification_url": f"http://localhost:8000/verify/{assessment_id}",
        },
        "demo_mode": demo_mode,
    }
