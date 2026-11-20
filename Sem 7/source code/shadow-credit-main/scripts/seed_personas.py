import json, sqlite3, uuid, sys
from pathlib import Path
from datetime import datetime

DB = Path(__file__).parent.parent / "data" / "shadow_credit.db"
PERSONAS_DIR = Path(__file__).parent.parent / "data" / "personas"
OUT_JSON = Path(__file__).parent / "demo_sessions.json"

PERSONAS = [
    ("persona01_clean",       "Suresh Kumar",  "Sadashiv Peth, Pune"),
    ("persona02_discrepancy", "Rajesh Sharma", "Kothrud, Pune"),
    ("persona03_seasonal",    "Akbar Khan",    "Camp Area, Pune"),
]

def seed():
    if not DB.exists():
        print(f"❌ DB not found at {DB}"); sys.exit(1)

    conn = sqlite3.connect(DB)

    # Wipe old seeded rows
    conn.execute("DELETE FROM artifacts WHERE agent_id='SEED_SCRIPT'")
    conn.execute("DELETE FROM sessions  WHERE status='SEEDED'")
    conn.commit()

    session_ids = {}

    for pid, name, loc in PERSONAS:
        persona_dir = PERSONAS_DIR / pid
        persona_file = persona_dir / "persona.json"

        if not persona_file.exists():
            print(f"⚠️  Skipping {pid} — persona.json missing at {persona_file}")
            continue

        sid = f"sc_{uuid.uuid4().hex[:8]}"
        session_ids[pid] = sid

        conn.execute("""
            INSERT INTO sessions
              (id, created_at, owner_name, location_masked, consent_given, status)
            VALUES (?,?,?,?,?,?)
        """, (sid, datetime.utcnow().isoformat(), name, loc, 1, "SEEDED"))

        aid = f"art_{uuid.uuid4().hex[:8]}"
        conn.execute("""
            INSERT INTO artifacts
              (id, session_id, artifact_type, file_hash,
               ocr_confidence, extracted_at, agent_id)
            VALUES (?,?,?,?,?,?,?)
        """, (aid, sid, "PERSONA_SEED", f"demo_hash_{pid}",
              1.0, datetime.utcnow().isoformat(), "SEED_SCRIPT"))

        print(f"  ✅ {pid} → session {sid}")

    conn.commit()
    conn.close()

    OUT_JSON.write_text(json.dumps({
        "persona01": session_ids.get("persona01_clean",    ""),
        "persona02": session_ids.get("persona02_discrepancy",""),
        "persona03": session_ids.get("persona03_seasonal", ""),
    }, indent=2), encoding="utf-8")

    print(f"\n✅ demo_sessions.json written → {OUT_JSON}")
    print(f"✅ {len(session_ids)} personas seeded into {DB}")

if __name__ == "__main__":
    seed()