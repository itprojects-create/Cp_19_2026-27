from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = ROOT / "backend"
sys.path.insert(0, str(ROOT))

CHECKS: list[tuple[str, bool, str]] = []

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def record(name: str, passed: bool, message: str) -> None:
    CHECKS.append((name, passed, message))


def check_core_imports() -> None:
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        import aiosqlite  # noqa: F401
        import pydantic  # noqa: F401
        import cryptography  # noqa: F401
        import anthropic  # noqa: F401

        record("Core packages import", True, "All critical packages available")
    except ImportError as exc:
        record("Core packages import", False, str(exc))


def check_settings_load() -> None:
    try:
        env_file = BACKEND_PATH / ".env"
        if not env_file.exists():
            record("Settings load and validate", False, "backend/.env not found")
            return
        from backend.config import get_settings

        s = get_settings()
        _ = s.MASTER_ENCRYPTION_KEY
        record("Settings load and validate", True, "Settings loaded successfully")
    except Exception as exc:
        record("Settings load and validate", False, str(exc))


def check_encryption_roundtrip() -> None:
    try:
        from backend.core.security import EncryptionService

        key_hex = "a" * 64
        service = EncryptionService(key_hex)
        enc = service.encrypt("hello shadow credit")
        dec = service.decrypt(enc["ciphertext"], enc["nonce"])
        if dec != "hello shadow credit":
            raise RuntimeError("Round-trip mismatch")
        record("AES-256-GCM encrypt/decrypt", True, "Round-trip successful")
    except Exception as exc:
        record("AES-256-GCM encrypt/decrypt", False, str(exc))


def check_confidence_logic() -> None:
    try:
        from backend.core.confidence import (
            ConfidenceBand,
            SupervisorAction,
            classify_confidence,
        )

        a = classify_confidence(0.90)
        b = classify_confidence(0.65)
        c = classify_confidence(0.30)
        ok = (
            a == (ConfidenceBand.HIGH, SupervisorAction.AUTO_ACCEPT)
            and b == (ConfidenceBand.MEDIUM, SupervisorAction.CLARIFY)
            and c == (ConfidenceBand.LOW, SupervisorAction.FALLBACK)
        )
        if not ok:
            raise RuntimeError("Classifier returned unexpected mapping")
        record("Confidence classifier logic", True, "Threshold mapping verified")
    except Exception as exc:
        record("Confidence classifier logic", False, str(exc))


def check_event_bus() -> None:
    async def _run() -> None:
        from backend.core.event_bus import EventBus

        bus = EventBus()
        q = bus.subscribe("AGENT_STARTED")
        payload = {
            "event_type": "AGENT_STARTED",
            "session_id": "s1",
            "timestamp": "2026-01-01T00:00:00Z",
            "data": {"agent_id": "A1"},
        }
        await bus.publish("AGENT_STARTED", payload)
        received = await asyncio.wait_for(q.get(), timeout=1.0)
        if received["session_id"] != "s1":
            raise RuntimeError("Received wrong payload")

    try:
        asyncio.run(_run())
        record("EventBus publish/subscribe", True, "Queue received published event")
    except Exception as exc:
        record("EventBus publish/subscribe", False, str(exc))


def check_schema_tables() -> None:
    try:
        schema_path = BACKEND_PATH / "db" / "schema.sql"
        sql = schema_path.read_text(encoding="utf-8")
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            tmp_db = tf.name
        conn = sqlite3.connect(tmp_db)
        try:
            conn.executescript(sql)
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            user_tables = {r[0] for r in rows}
            required = {
                "sessions",
                "artifacts",
                "audit_log",
                "extractions",
                "decisions",
                "credit_assessments",
            }
            if not required.issubset(user_tables):
                raise RuntimeError(f"Missing tables: {sorted(required - user_tables)}")
        finally:
            conn.close()
            os.remove(tmp_db)
        record("Database schema loads (6 tables)", True, "All required tables present")
    except Exception as exc:
        record("Database schema loads (6 tables)", False, str(exc))


def check_audit_immutability() -> None:
    try:
        schema_path = BACKEND_PATH / "db" / "schema.sql"
        sql = schema_path.read_text(encoding="utf-8")
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            tmp_db = tf.name
        conn = sqlite3.connect(tmp_db)
        try:
            conn.executescript(sql)
            conn.execute(
                """
                INSERT INTO sessions (
                    id, created_at, owner_name, location_masked, consent_given, session_key_hash, status, demo_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("s1", "2026-01-01T00:00:00Z", "x", "y", 1, "h", "PENDING", 0),
            )
            conn.execute(
                """
                INSERT INTO audit_log (
                    id, session_id, agent_id, action_type, timestamp
                ) VALUES (?, ?, ?, ?, ?)
                """,
                ("a1", "s1", "SYS", "TEST", "2026-01-01T00:00:00Z"),
            )
            conn.commit()

            update_err = None
            delete_err = None
            try:
                conn.execute("UPDATE audit_log SET action_type='X' WHERE id='a1'")
                conn.commit()
            except Exception as exc:
                update_err = str(exc).lower()
            try:
                conn.execute("DELETE FROM audit_log WHERE id='a1'")
                conn.commit()
            except Exception as exc:
                delete_err = str(exc).lower()

            if not update_err or "immutable" not in update_err:
                raise RuntimeError("UPDATE did not raise immutable trigger")
            if not delete_err or "immutable" not in delete_err:
                raise RuntimeError("DELETE did not raise immutable trigger")
        finally:
            conn.close()
            os.remove(tmp_db)
        record("Immutable audit log triggers", True, "UPDATE/DELETE correctly blocked")
    except Exception as exc:
        record("Immutable audit log triggers", False, str(exc))


def check_health_endpoint() -> None:
    proc = None
    try:
        env = os.environ.copy()
        env["MASTER_ENCRYPTION_KEY"] = env.get("MASTER_ENCRYPTION_KEY", "b" * 64)
        env["ANTHROPIC_API_KEY"] = env.get("ANTHROPIC_API_KEY", "sk-ant-test")
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8010"],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)
        with urlopen("http://127.0.0.1:8010/api/v1/health", timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        ok = body.get("success") is True and body.get("data", {}).get("status") == "operational"
        if not ok:
            raise RuntimeError(f"Unexpected health response: {body}")
        record("FastAPI server health endpoint", True, "Health endpoint returned operational")
    except Exception as exc:
        record("FastAPI server health endpoint", False, str(exc))
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()


def print_results() -> int:
    print("═══════════════════════════════════════════")
    print("  PHASE 0 VERIFICATION RESULTS")
    print("═══════════════════════════════════════════")

    passed = 0
    for name, ok, message in CHECKS:
        if ok:
            passed += 1
            print(f"  {GREEN}✅ PASS{RESET}: {name}")
        else:
            print(f"  {RED}❌ FAIL{RESET}: {name}")
            print(f"       Error: {message}")

    print("───────────────────────────────────────────")
    if passed == len(CHECKS):
        print(f"  {passed}/8 checks passed. Phase 0 complete. ✅")
        print("  Ready to build Phase 1 — Data Ingestion Layer.")
        print("═══════════════════════════════════════════")
        return 0
    print(f"  {passed}/8 checks passed. Fix the ❌ items before starting Phase 1.")
    print("═══════════════════════════════════════════")
    return 1


def main() -> int:
    check_core_imports()
    check_settings_load()
    check_encryption_roundtrip()
    check_confidence_logic()
    check_event_bus()
    check_schema_tables()
    check_audit_immutability()
    check_health_endpoint()
    return print_results()


if __name__ == "__main__":
    sys.exit(main())
