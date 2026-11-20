-- ══════════════════════════════════════════════════════════════════════════════
-- Shadow Credit — SQLite Schema
-- Production-grade DDL for regulated financial data processing
-- Tables: sessions, artifacts, audit_log, extractions, decisions,
--         credit_assessments
-- ══════════════════════════════════════════════════════════════════════════════

-- ── PRAGMA Configuration (applied at connection time in database.py) ────────
-- PRAGMA journal_mode = WAL;
-- PRAGMA foreign_keys = ON;


-- ════════════════════════════════════════════
-- TABLE: sessions
-- ════════════════════════════════════════════
-- One row per credit assessment session. Owner identity is AES-256-GCM
-- encrypted at the application layer before INSERT.

CREATE TABLE IF NOT EXISTS sessions (
    id                TEXT PRIMARY KEY,
    created_at        TEXT NOT NULL,
    owner_name        TEXT NOT NULL,
    location_masked   TEXT,
    consent_given     INTEGER NOT NULL DEFAULT 0
        CHECK (consent_given IN (0, 1)),
    session_key_hash  TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETE', 'FAILED', 'ERASED')),
    demo_mode         INTEGER NOT NULL DEFAULT 0
        CHECK (demo_mode IN (0, 1))
);


-- ════════════════════════════════════════════
-- TABLE: artifacts
-- ════════════════════════════════════════════
-- Every document uploaded or ingested during a session. File content is
-- encrypted at rest; only the encrypted path and content hash are stored here.

CREATE TABLE IF NOT EXISTS artifacts (
    id                  TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL
        REFERENCES sessions(id) ON DELETE RESTRICT,
    artifact_type       TEXT NOT NULL
        CHECK (artifact_type IN ('WHATSAPP', 'UPI', 'BILL', 'KHATA', 'MAPS')),
    file_hash           TEXT NOT NULL,
    encrypted_path      TEXT NOT NULL,
    ocr_confidence      REAL,
    extracted_at        TEXT,
    agent_id            TEXT NOT NULL,
    processing_status   TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (processing_status IN ('PENDING', 'PROCESSING', 'COMPLETE', 'FAILED'))
);


-- ════════════════════════════════════════════
-- TABLE: audit_log
-- ════════════════════════════════════════════
-- Append-only, immutable record of every agent action. UPDATE and DELETE are
-- physically blocked by triggers — this table withstands regulatory audit.

CREATE TABLE IF NOT EXISTS audit_log (
    id                TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL
        REFERENCES sessions(id) ON DELETE RESTRICT,
    agent_id          TEXT NOT NULL,
    action_type       TEXT NOT NULL,
    input_hash        TEXT,
    output_hash       TEXT,
    confidence_score  REAL,
    latency_ms        INTEGER,
    timestamp         TEXT NOT NULL
);

-- CRITICAL: Immutability triggers — the database itself prevents tampering.
-- If a regulator asks "what stops manipulation of the audit trail?", the
-- answer is: SQLite raises an exception before the statement executes.

CREATE TRIGGER IF NOT EXISTS audit_log_prevent_update
    BEFORE UPDATE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'Audit log is immutable — UPDATE prohibited');
END;

CREATE TRIGGER IF NOT EXISTS audit_log_prevent_delete
    BEFORE DELETE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'Audit log is immutable — DELETE prohibited');
END;


-- ════════════════════════════════════════════
-- TABLE: extractions
-- ════════════════════════════════════════════
-- Individual data fields extracted from artifacts by OCR, LLM, or CSV parsing.
-- Each row is one field from one artifact.

CREATE TABLE IF NOT EXISTS extractions (
    id                  TEXT PRIMARY KEY,
    artifact_id         TEXT NOT NULL
        REFERENCES artifacts(id) ON DELETE RESTRICT,
    field_name          TEXT NOT NULL,
    raw_value           TEXT,
    normalized_value    TEXT,
    confidence_score    REAL,
    extraction_method   TEXT NOT NULL
        CHECK (extraction_method IN ('OCR', 'LLM', 'CSV_PARSE', 'MANUAL')),
    flagged             INTEGER NOT NULL DEFAULT 0
        CHECK (flagged IN (0, 1))
);


-- ════════════════════════════════════════════
-- TABLE: decisions
-- ════════════════════════════════════════════
-- Supervisor agent routing decisions. Every confidence-band triage is logged
-- here with the action taken and optional human resolution.

CREATE TABLE IF NOT EXISTS decisions (
    id                  TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL
        REFERENCES sessions(id) ON DELETE RESTRICT,
    supervisor_action   TEXT NOT NULL
        CHECK (supervisor_action IN ('AUTO_ACCEPT', 'CLARIFY', 'FALLBACK')),
    confidence_band     TEXT NOT NULL
        CHECK (confidence_band IN ('HIGH', 'MEDIUM', 'LOW')),
    reason              TEXT,
    timestamp           TEXT NOT NULL,
    resolved            INTEGER NOT NULL DEFAULT 0
        CHECK (resolved IN (0, 1)),
    resolution_input    TEXT
);


-- ════════════════════════════════════════════
-- TABLE: credit_assessments
-- ════════════════════════════════════════════
-- Final credit assessment output. One per session (UNIQUE on session_id).
-- Contains scoring components, the OCEN payload, and a SHA-256 hash of
-- the generated credit memo PDF for tamper detection.

CREATE TABLE IF NOT EXISTS credit_assessments (
    id                  TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL UNIQUE
        REFERENCES sessions(id) ON DELETE RESTRICT,
    base_limit          REAL,
    regularity_score    REAL,
    concentration_risk  REAL,
    continuity_score    REAL,
    final_limit         REAL,
    warmth_score        REAL,
    credit_grade        TEXT
        CHECK (credit_grade IN ('A+', 'A', 'B+', 'B', 'C')),
    formula_json        TEXT,
    ocen_payload        TEXT,
    pdf_hash_sha256     TEXT,
    created_at          TEXT NOT NULL
);


-- ════════════════════════════════════════════
-- PERFORMANCE INDEXES
-- ════════════════════════════════════════════
-- Named explicitly for debuggability in EXPLAIN QUERY PLAN output.

CREATE INDEX IF NOT EXISTS idx_audit_session
    ON audit_log(session_id);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp
    ON audit_log(timestamp);

CREATE INDEX IF NOT EXISTS idx_artifacts_session
    ON artifacts(session_id);

CREATE INDEX IF NOT EXISTS idx_artifacts_type
    ON artifacts(artifact_type);

CREATE INDEX IF NOT EXISTS idx_extractions_artifact
    ON extractions(artifact_id);

CREATE INDEX IF NOT EXISTS idx_extractions_field
    ON extractions(field_name);

CREATE INDEX IF NOT EXISTS idx_decisions_session
    ON decisions(session_id);
