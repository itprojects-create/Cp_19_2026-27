"""
Realistic 3-persona mock analysis pipeline for Shadow Credit demo.

Three personas with different characteristics:
- Suresh: Clean happy path (Grade A)
- Meena: Has discrepancy, requires clarification (Grade B)
- Raju: Seasonal business pattern (Grade A-)
"""

import asyncio
from datetime import datetime, timezone

try:
    from backend.core.event_bus import event_bus
except ModuleNotFoundError:
    from core.event_bus import event_bus


def ts():
    return datetime.now(timezone.utc).isoformat() + "Z"


# ─── PERSONA DEFINITIONS ──────────────────────────────────────────────────────

PERSONAS = {
    "suresh": {
        "name": "Suresh Kirana Store",
        "location": "Sadashiv Peth, Pune",
        "result": {
            "credit_grade": "A",
            "final_limit": 65000,
            "warmth_score": 0.84,
            "reconciliation_status": "NORMAL_CASH",
            "monthly_inflow": 44000,
            "sources_verified": 4,
            "assessment_date": "27 March 2026",
        }
    },
    "meena": {
        "name": "Meena Fashion House",
        "location": "Kalyani Nagar, Pune",
        "result": {
            "credit_grade": "B",
            "final_limit": 38000,
            "warmth_score": 0.67,
            "reconciliation_status": "FLAGGED",
            "monthly_inflow": 28000,
            "sources_verified": 3,
            "assessment_date": "27 March 2026",
            "clarification_required": True,
            "clarification_question": "We detected a cash gap of ₹18,000 (36%). Does your business accept a significant portion in cash?",
        }
    },
    "raju": {
        "name": "Raju Tent & Decoration",
        "location": "Pimpri, Pune",
        "result": {
            "credit_grade": "A-",
            "final_limit": 58000,
            "warmth_score": 0.79,
            "reconciliation_status": "NORMAL_CASH",
            "monthly_inflow": 52000,
            "sources_verified": 4,
            "assessment_date": "27 March 2026",
            "seasonal_detected": True,
        }
    }
}


async def run_mock_analysis_pipeline(session_id: str, persona_key: str = "suresh"):
    """
    Realistic 3-persona pipeline simulation.
    persona_key: "suresh" | "" | "raju"
    """
    persona = PERSONAS.get(persona_key, PERSONAS["suresh"])
    result = persona["result"]

    # ── PHASE A: INGESTION ──────────────────────────────────────────────────

    await asyncio.sleep(1.5)

    # AGENT 00 — Maps Verification
    await event_bus.publish_agent_event(
        session_id=session_id,
        agent_id="AGENT_00_MAPS",
        status="STARTED",
        message=f"Verifying {persona['name']} on Google Maps...",
    )
    await asyncio.sleep(3)
    await event_bus.publish_agent_event(
        session_id=session_id,
        agent_id="AGENT_00_MAPS",
        status="COMPLETE",
        message="Business verified — 4.2★ rating, 47 reviews, OPERATIONAL",
        confidence=0.85,
    )
    await asyncio.sleep(0.5)

    # AGENT 01 — OCR
    await event_bus.publish_agent_event(
        session_id=session_id,
        agent_id="AGENT_01_OCR",
        status="STARTED",
        message="Reading MSEDCL electricity bill and UPI screenshots...",
    )
    await asyncio.sleep(4)
    await event_bus.publish_agent_event(
        session_id=session_id,
        agent_id="AGENT_01_OCR",
        status="COMPLETE",
        message="OCR complete — COMMERCIAL connection confirmed. 6 UPI transactions extracted.",
        confidence=0.88,
    )
    await asyncio.sleep(0.5)

    # AGENT 02 — WhatsApp Parser
    await event_bus.publish_agent_event(
        session_id=session_id,
        agent_id="AGENT_02_WHATSAPP",
        status="STARTED",
        message="Parsing WhatsApp chat — filtering noise, classifying transactions...",
    )
    await asyncio.sleep(6)

    if persona_key == "":
        await event_bus.publish_agent_event(
            session_id=session_id,
            agent_id="AGENT_02_WHATSAPP",
            status="COMPLETE",
            message="Parsed 134 messages → 61 financial events. HIGH cash payment ratio detected (40%).",
            confidence=0.73,
        )
    elif persona_key == "raju":
        await event_bus.publish_agent_event(
            session_id=session_id,
            agent_id="AGENT_02_WHATSAPP",
            status="COMPLETE",
            message="Parsed 160 messages → 48 financial events. Seasonal pattern detected — peak Oct–Mar.",
            confidence=0.81,
        )
    else:
        await event_bus.publish_agent_event(
            session_id=session_id,
            agent_id="AGENT_02_WHATSAPP",
            status="COMPLETE",
            message="Parsed 120 messages → 53 financial events. Consistent inflow ₹44,000/mo. Quality: HIGH.",
            confidence=0.87,
        )
    await asyncio.sleep(0.5)

    # ── PHASE B: INTELLIGENCE ───────────────────────────────────────────────

    # AGENT 04 — CreditWarmthScore
    await event_bus.publish_agent_event(
        session_id=session_id,
        agent_id="AGENT_04_WARMTH",
        status="STARTED",
        message="Computing CreditWarmthScore — 7 behavioral signals...",
    )
    await asyncio.sleep(4)

    if persona_key == "raju":
        await event_bus.publish_agent_event(
            session_id=session_id,
            agent_id="AGENT_04_WARMTH",
            status="COMPLETE",
            message=f"CreditWarmthScore: {result['warmth_score']} | Grade: {result['credit_grade']} | Seasonal pattern: DETECTED — adjusting to annual median.",
            confidence=result["warmth_score"],
        )
    else:
        await event_bus.publish_agent_event(
            session_id=session_id,
            agent_id="AGENT_04_WARMTH",
            status="COMPLETE",
            message=f"CreditWarmthScore: {result['warmth_score']} | Grade: {result['credit_grade']} | Income regularity: 0.84",
            confidence=result["warmth_score"],
        )
    await asyncio.sleep(0.5)

    # AGENT 05 — Reconciliation / Forensics
    await event_bus.publish_agent_event(
        session_id=session_id,
        agent_id="AGENT_05_RECONCILIATION",
        status="STARTED",
        message="Reconciling WhatsApp ↔ UPI ↔ SMS — forensic gap analysis...",
    )
    await asyncio.sleep(5)

    if persona_key == "meena":
        # Dramatic pause before flagging
        await event_bus.publish_agent_event(
            session_id=session_id,
            agent_id="AGENT_05_RECONCILIATION",
            status="PROGRESS",
            message="FORENSIC: Gap detected — WhatsApp ₹48,000 stated vs UPI ₹28,000 confirmed. Gap: ₹20,000 (41.7%). Analyzing...",
            confidence=0.71,
        )
        await asyncio.sleep(1.5)
        
        # Clarification required
        await event_bus.publish(
            "CLARIFICATION_REQUIRED",
            {
                "event_type": "CLARIFICATION_REQUIRED",
                "session_id": session_id,
                "timestamp": ts(),
                "data": {
                    "agent_id": "SUPERVISOR",
                    "message": "PIPELINE PAUSED — Supervisor requires RM input",
                    "question": result.get("clarification_question"),
                    "options": ["Yes, significant cash payments", "No, most payments are digital"],
                }
            }
        )
        
        await asyncio.sleep(8)  # Simulate RM answering
        
        await event_bus.publish_agent_event(
            session_id=session_id,
            agent_id="SUPERVISOR",
            status="COMPLETE",
            message="Pipeline resumed — Cash gap reclassified as NORMAL_CASH per RBI MSME norms (36% cash ratio documented).",
            confidence=0.78,
        )
    else:
        await event_bus.publish_agent_event(
            session_id=session_id,
            agent_id="AGENT_05_RECONCILIATION",
            status="COMPLETE",
            message="Reconciliation: NORMAL_CASH. WA ↔ UPI gap within RBI 36% cash-ratio norm. Cross-verified 3 transactions.",
            confidence=0.87,
        )
    await asyncio.sleep(0.5)

    # ── PHASE C: COMPLIANCE + REPORT ────────────────────────────────────────

    # AGENT 06 — Compliance
    await event_bus.publish_agent_event(
        session_id=session_id,
        agent_id="AGENT_06_COMPLIANCE",
        status="STARTED",
        message="Running 12-item RBI MSME compliance checklist...",
    )
    await asyncio.sleep(3)
    await event_bus.publish_agent_event(
        session_id=session_id,
        agent_id="AGENT_06_COMPLIANCE",
        status="COMPLETE",
        message="Compliance: 10/12 checks PASS. GST not registered — limit capped at ₹3,00,000. DPDP consent verified.",
        confidence=0.92,
    )
    await asyncio.sleep(0.5)

    # AGENT 07 — Report
    await event_bus.publish_agent_event(
        session_id=session_id,
        agent_id="AGENT_07_REPORT",
        status="STARTED",
        message="Generating Credit Memo PDF and Credit Passport...",
    )
    await asyncio.sleep(4)
    await event_bus.publish_agent_event(
        session_id=session_id,
        agent_id="AGENT_07_REPORT",
        status="COMPLETE",
        message=f"Done — Credit Memo ({result['final_limit']//1000}K limit), Passport PDF, OCEN 4.0 JSON generated. SHA-256 signed.",
        confidence=0.95,
    )
    await asyncio.sleep(1)

    # ── SESSION COMPLETE ─────────────────────────────────────────────────────

    await event_bus.publish(
        "SESSION_COMPLETE",
        {
            "event_type": "SESSION_COMPLETE",
            "session_id": session_id,
            "timestamp": ts(),
            "data": {
                "message": "Assessment complete — 7/7 agents done",
                **result
            }
        }
    )
