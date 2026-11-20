"""
Pydantic v2 models for Shadow Credit database tables.

Every model mirrors its schema.sql table exactly — column names, types,
nullability, and CHECK constraints are kept in strict 1:1 correspondence.
Enum classes enforce the same value sets as the SQLite CHECK constraints.

Conventions:
    - All IDs are ``str`` (UUIDs serialized to TEXT in SQLite).
    - All timestamps are ``str`` in ISO 8601 (SQLite has no native datetime).
    - ``*Create`` variants omit server-generated fields (id, timestamps).
    - Every model exposes ``from_db_row(row: dict)`` for coercion from
      SQLite's loosely typed output.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ══════════════════════════════════════════════
# ENUM CLASSES — match CHECK constraints exactly
# ══════════════════════════════════════════════


class SessionStatus(str, Enum):
    """sessions.status CHECK constraint."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    ERASED = "ERASED"


class ArtifactType(str, Enum):
    """artifacts.artifact_type CHECK constraint."""

    WHATSAPP = "WHATSAPP"
    UPI = "UPI"
    BILL = "BILL"
    KHATA = "KHATA"
    MAPS = "MAPS"


class ProcessingStatus(str, Enum):
    """artifacts.processing_status CHECK constraint."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ExtractionMethod(str, Enum):
    """extractions.extraction_method CHECK constraint."""

    OCR = "OCR"
    LLM = "LLM"
    CSV_PARSE = "CSV_PARSE"
    MANUAL = "MANUAL"


class SupervisorAction(str, Enum):
    """decisions.supervisor_action CHECK constraint."""

    AUTO_ACCEPT = "AUTO_ACCEPT"
    CLARIFY = "CLARIFY"
    FALLBACK = "FALLBACK"


class ConfidenceBand(str, Enum):
    """decisions.confidence_band CHECK constraint."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CreditGrade(str, Enum):
    """credit_assessments.credit_grade CHECK constraint."""

    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C = "C"


# ══════════════════════════════════════════════
# SESSION
# ══════════════════════════════════════════════


class Session(BaseModel):
    """Mirrors the ``sessions`` table."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: str
    owner_name: str
    location_masked: Optional[str] = None
    consent_given: int
    session_key_hash: str
    status: SessionStatus
    demo_mode: int

    @classmethod
    def from_db_row(cls, row: dict) -> Session:
        return cls(
            id=str(row["id"]),
            created_at=str(row["created_at"]),
            owner_name=str(row["owner_name"]),
            location_masked=row.get("location_masked"),
            consent_given=int(row["consent_given"]),
            session_key_hash=str(row["session_key_hash"]),
            status=SessionStatus(row["status"]),
            demo_mode=int(row["demo_mode"]),
        )


class SessionCreate(BaseModel):
    """Input model for creating a session (no id — generated server-side)."""

    model_config = ConfigDict(from_attributes=True)

    created_at: str
    owner_name: str
    location_masked: Optional[str] = None
    consent_given: int
    session_key_hash: str
    status: SessionStatus = SessionStatus.PENDING
    demo_mode: int = 0


# ══════════════════════════════════════════════
# ARTIFACT
# ══════════════════════════════════════════════


class Artifact(BaseModel):
    """Mirrors the ``artifacts`` table."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    artifact_type: ArtifactType
    file_hash: str
    encrypted_path: str
    ocr_confidence: Optional[float] = None
    extracted_at: Optional[str] = None
    agent_id: str
    processing_status: ProcessingStatus

    @classmethod
    def from_db_row(cls, row: dict) -> Artifact:
        return cls(
            id=str(row["id"]),
            session_id=str(row["session_id"]),
            artifact_type=ArtifactType(row["artifact_type"]),
            file_hash=str(row["file_hash"]),
            encrypted_path=str(row["encrypted_path"]),
            ocr_confidence=float(row["ocr_confidence"]) if row.get("ocr_confidence") is not None else None,
            extracted_at=str(row["extracted_at"]) if row.get("extracted_at") is not None else None,
            agent_id=str(row["agent_id"]),
            processing_status=ProcessingStatus(row["processing_status"]),
        )


class ArtifactCreate(BaseModel):
    """Input model for creating an artifact (no id)."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    artifact_type: ArtifactType
    file_hash: str
    encrypted_path: str
    ocr_confidence: Optional[float] = None
    extracted_at: Optional[str] = None
    agent_id: str
    processing_status: ProcessingStatus = ProcessingStatus.PENDING


# ══════════════════════════════════════════════
# AUDIT LOG
# ══════════════════════════════════════════════


class AuditLog(BaseModel):
    """Mirrors the ``audit_log`` table. Immutable — no update model exists."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    agent_id: str
    action_type: str
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    confidence_score: Optional[float] = None
    latency_ms: Optional[int] = None
    timestamp: str

    @classmethod
    def from_db_row(cls, row: dict) -> AuditLog:
        return cls(
            id=str(row["id"]),
            session_id=str(row["session_id"]),
            agent_id=str(row["agent_id"]),
            action_type=str(row["action_type"]),
            input_hash=row.get("input_hash"),
            output_hash=row.get("output_hash"),
            confidence_score=float(row["confidence_score"]) if row.get("confidence_score") is not None else None,
            latency_ms=int(row["latency_ms"]) if row.get("latency_ms") is not None else None,
            timestamp=str(row["timestamp"]),
        )


class AuditLogCreate(BaseModel):
    """Input model for appending to the audit log (no id)."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    agent_id: str
    action_type: str
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    confidence_score: Optional[float] = None
    latency_ms: Optional[int] = None
    timestamp: str


# ══════════════════════════════════════════════
# EXTRACTION
# ══════════════════════════════════════════════


class Extraction(BaseModel):
    """Mirrors the ``extractions`` table."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    artifact_id: str
    field_name: str
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    confidence_score: Optional[float] = None
    extraction_method: ExtractionMethod
    flagged: int

    @classmethod
    def from_db_row(cls, row: dict) -> Extraction:
        return cls(
            id=str(row["id"]),
            artifact_id=str(row["artifact_id"]),
            field_name=str(row["field_name"]),
            raw_value=row.get("raw_value"),
            normalized_value=row.get("normalized_value"),
            confidence_score=float(row["confidence_score"]) if row.get("confidence_score") is not None else None,
            extraction_method=ExtractionMethod(row["extraction_method"]),
            flagged=int(row["flagged"]),
        )


class ExtractionCreate(BaseModel):
    """Input model for creating an extraction (no id)."""

    model_config = ConfigDict(from_attributes=True)

    artifact_id: str
    field_name: str
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    confidence_score: Optional[float] = None
    extraction_method: ExtractionMethod
    flagged: int = 0


# ══════════════════════════════════════════════
# DECISION
# ══════════════════════════════════════════════


class Decision(BaseModel):
    """Mirrors the ``decisions`` table."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    supervisor_action: SupervisorAction
    confidence_band: ConfidenceBand
    reason: Optional[str] = None
    timestamp: str
    resolved: int
    resolution_input: Optional[str] = None

    @classmethod
    def from_db_row(cls, row: dict) -> Decision:
        return cls(
            id=str(row["id"]),
            session_id=str(row["session_id"]),
            supervisor_action=SupervisorAction(row["supervisor_action"]),
            confidence_band=ConfidenceBand(row["confidence_band"]),
            reason=row.get("reason"),
            timestamp=str(row["timestamp"]),
            resolved=int(row["resolved"]),
            resolution_input=row.get("resolution_input"),
        )


class DecisionCreate(BaseModel):
    """Input model for creating a decision (no id)."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    supervisor_action: SupervisorAction
    confidence_band: ConfidenceBand
    reason: Optional[str] = None
    timestamp: str
    resolved: int = 0
    resolution_input: Optional[str] = None


# ══════════════════════════════════════════════
# CREDIT ASSESSMENT
# ══════════════════════════════════════════════


class CreditAssessment(BaseModel):
    """Mirrors the ``credit_assessments`` table."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    base_limit: Optional[float] = None
    regularity_score: Optional[float] = None
    concentration_risk: Optional[float] = None
    continuity_score: Optional[float] = None
    final_limit: Optional[float] = None
    warmth_score: Optional[float] = None
    credit_grade: Optional[CreditGrade] = None
    formula_json: Optional[str] = None
    ocen_payload: Optional[str] = None
    pdf_hash_sha256: Optional[str] = None
    created_at: str

    @classmethod
    def from_db_row(cls, row: dict) -> CreditAssessment:
        return cls(
            id=str(row["id"]),
            session_id=str(row["session_id"]),
            base_limit=float(row["base_limit"]) if row.get("base_limit") is not None else None,
            regularity_score=float(row["regularity_score"]) if row.get("regularity_score") is not None else None,
            concentration_risk=float(row["concentration_risk"]) if row.get("concentration_risk") is not None else None,
            continuity_score=float(row["continuity_score"]) if row.get("continuity_score") is not None else None,
            final_limit=float(row["final_limit"]) if row.get("final_limit") is not None else None,
            warmth_score=float(row["warmth_score"]) if row.get("warmth_score") is not None else None,
            credit_grade=CreditGrade(row["credit_grade"]) if row.get("credit_grade") is not None else None,
            formula_json=row.get("formula_json"),
            ocen_payload=row.get("ocen_payload"),
            pdf_hash_sha256=row.get("pdf_hash_sha256"),
            created_at=str(row["created_at"]),
        )


class CreditAssessmentCreate(BaseModel):
    """Input model for creating a credit assessment (no id)."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    base_limit: Optional[float] = None
    regularity_score: Optional[float] = None
    concentration_risk: Optional[float] = None
    continuity_score: Optional[float] = None
    final_limit: Optional[float] = None
    warmth_score: Optional[float] = None
    credit_grade: Optional[CreditGrade] = None
    formula_json: Optional[str] = None
    ocen_payload: Optional[str] = None
    pdf_hash_sha256: Optional[str] = None
    created_at: str
