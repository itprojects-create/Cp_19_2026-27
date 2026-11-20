from __future__ import annotations

import argparse
import asyncio
import uuid
from datetime import datetime
from pathlib import Path

from backend.agents.supervisor import SupervisorAgent
from backend.config import get_settings
from backend.db.database import execute_query, execute_write, get_db


def _resolve_persona_from_location(location_masked: str) -> str | None:
    loc = (location_masked or "").lower()
    if "sadashiv" in loc:
        return "persona01_clean"
    if "kothrud" in loc:
        return "persona02_discrepancy"
    if "camp" in loc:
        return "persona03_seasonal"
    return None


async def _build_demo_artifacts(session_id: str, persona_id: str) -> list[dict]:
    persona_dir = Path("data") / "personas" / persona_id
    required = {
        "WHATSAPP": persona_dir / "whatsapp.txt",
        "UPI": persona_dir / "upi_events.json",
        "KHATA": persona_dir / "khata.csv",
        "BILL": persona_dir / "bill_metadata.json",
        "MAPS": persona_dir / "maps_data.json",
    }
    missing = [f"{k}:{v}" for k, v in required.items() if not v.exists()]
    if missing:
        raise FileNotFoundError(f"Missing persona files: {missing}")

    artifacts = []
    async with get_db() as db:
        await execute_write(db, "DELETE FROM artifacts WHERE session_id = ?", (session_id,))
        for artifact_type, file_path in required.items():
            artifact_id = f"art_{uuid.uuid4().hex[:8]}"
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
                    artifact_type,
                    f"demo_hash_{persona_id}_{artifact_type.lower()}",
                    str(file_path),
                    1.0,
                    datetime.utcnow().isoformat() + "Z",
                    "SEED_SCRIPT",
                    "PENDING",
                ),
            )
            artifacts.append(
                {
                    "artifact_id": artifact_id,
                    "artifact_type": artifact_type,
                    "saved_path": str(file_path),
                }
            )
    return artifacts


async def run_pipeline(session_id: str, persona_id: str | None) -> None:
    settings = get_settings()

    async with get_db() as db:
        rows = await execute_query(
            db,
            "SELECT id, demo_mode, location_masked FROM sessions WHERE id = ? LIMIT 1",
            (session_id,),
        )
        if not rows:
            raise ValueError(f"Session not found: {session_id}")
        row = rows[0]
        is_demo = int(row.get("demo_mode", 0) or 0) == 1
        if is_demo and not persona_id:
            persona_id = _resolve_persona_from_location(str(row.get("location_masked", "")))
        await execute_write(db, "UPDATE sessions SET status = 'PROCESSING' WHERE id = ?", (session_id,))

    if int(row.get("demo_mode", 0) or 0) == 1:
        if not persona_id:
            raise ValueError("Demo session requires --persona-id or recognizable location mapping.")
        artifacts = await _build_demo_artifacts(session_id=session_id, persona_id=persona_id)
    else:
        async with get_db() as db:
            rows_art = await execute_query(
                db,
                "SELECT id, artifact_type, encrypted_path FROM artifacts WHERE session_id = ? ORDER BY extracted_at ASC",
                (session_id,),
            )
        artifacts = [{"artifact_id": r["id"], "artifact_type": r["artifact_type"], "saved_path": r["encrypted_path"]} for r in rows_art]

    supervisor = SupervisorAgent(settings=settings)
    state = await supervisor.run_session(session_id=session_id, artifact_records=artifacts)
    print(f"session_id={session_id} complete={state.pipeline_complete} phase={state.phase} failed={state.agents_failed}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Shadow Credit supervisor pipeline for a session.")
    parser.add_argument("--session-id", required=True, help="Session ID (e.g., sc_ee73adbc)")
    parser.add_argument("--persona-id", required=False, help="Persona folder name (e.g., persona01_clean)")
    args = parser.parse_args()
    asyncio.run(run_pipeline(session_id=args.session_id, persona_id=args.persona_id))


if __name__ == "__main__":
    main()
