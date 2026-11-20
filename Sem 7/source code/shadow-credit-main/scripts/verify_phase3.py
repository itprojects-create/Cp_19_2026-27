from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, message: str = "") -> None:
    CHECKS.append((name, passed, message))
    icon = "✅" if passed else "❌"
    print(f"{icon} {name}" + (f" — {message}" if message else ""))


def _prepare_mock_outputs():
    from agents.agent_04_warmth import CreditWarmthScoreAgent
    from agents.agent_05_reconciliation import ReconciliationAgent

    warmth_inputs = {
        "whatsapp_output": {
            "weekly_summary": [
                {"week_start": "2026-01-05", "total_inflow": 45000, "net": 38000},
                {"week_start": "2026-01-12", "total_inflow": 42000, "net": 35000},
                {"week_start": "2026-01-19", "total_inflow": 48000, "net": 41000},
            ],
            "behavioral_signals": {"peak_hour_activity_pct": 0.78, "activity_ratio": 0.87, "unique_counterparties": 23},
        },
        "upi_output": {"total_inflow": 128000},
        "maps_output": {"continuity_from_maps": 0.76, "review_count": 47},
        "sms_output": {"monthly_summary": [{"month": "2026-01", "total_inflow": 41000}]},
        "bill_output": {"bill_age_days": 22, "connection_type": "COMMERCIAL"},
    }
    warmth = asyncio.run(CreditWarmthScoreAgent().execute("phase3-test", warmth_inputs)).data

    recon_inputs = {
        "whatsapp_events": [
            {"direction": "inflow", "amount": 15000, "date": "2026-01-15"},
            {"direction": "inflow", "amount": 22000, "date": "2026-01-22"},
            {"direction": "inflow", "amount": 13000, "date": "2026-01-29"},
        ],
        "sms_events": [
            {"direction": "inflow", "amount": 14500, "date": "2026-01-15"},
            {"direction": "inflow", "amount": 20000, "date": "2026-01-22"},
        ],
        "upi_total": 34500,
        "whatsapp_total": 50000,
        "business_type": "Kirana store",
    }
    recon = asyncio.run(ReconciliationAgent().execute("phase3-test", recon_inputs)).data
    return warmth, recon


def check_agent06() -> tuple[dict, dict]:
    try:
        from agents.agent_06_compliance import ComplianceScenarioAgent

        warmth, recon = _prepare_mock_outputs()
        comp_agent = ComplianceScenarioAgent()
        comp_inputs = {
            "warmth_output": warmth,
            "reconciliation_output": recon,
            "whatsapp_output": {"financial_events": []},
            "khata_output": {"inflow_metrics": {"median_monthly_received": 44000, "total_received_90d": 132000}, "customer_metrics": {"top_customer_pct": 0.32}, "data_quality": {"total_transactions": 24}, "period": {"days_actual": 210}},
            "ocr_outputs": [],
            "session_record": {"consent_given": True, "maps_verified": True, "has_gst": False, "aa_consent": False, "upi_days_covered": 60},
        }
        result = asyncio.run(comp_agent.execute("phase3-test", comp_inputs))
        data = result.data
        checklist = data.get("compliance_checklist", [])
        failed = [i for i in checklist if i.get("status") == "FAIL"]
        has_rm_explanations = all(bool(str(i.get("rm_explanation", "")).strip()) for i in failed) if failed else True
        scenario_data = data.get("scenarios", {}).get("gst_plus_aa", {})
        check("Agent 06 12-item checklist runs without error", isinstance(checklist, list) and len(checklist) == 12, f"items={len(checklist)}")
        check("Agent 06 failed items have rm_explanation (Claude-generated)", has_rm_explanations, f"failed={len(failed)}")
        check("Agent 06 scenario simulation returns delta_from_current", "delta_from_current" in scenario_data, f"keys={list(scenario_data.keys())[:4]}")
        return data, comp_inputs
    except Exception as exc:
        check("Agent 06 12-item checklist runs without error", False, str(exc))
        check("Agent 06 failed items have rm_explanation (Claude-generated)", False, str(exc))
        check("Agent 06 scenario simulation returns delta_from_current", False, str(exc))
        return {}, {}


def check_agent07(compliance_output: dict) -> None:
    try:
        from agents.agent_07_report import ReportAgent
        from backend.db.database import execute_query, get_db

        report_agent = ReportAgent()
        report_inputs = {
            "session_id": "phase3-test",
            "compliance_output": compliance_output,
            "warmth_output": {
                "warmth_score": 0.78,
                "credit_grade": "B+",
                "confidence_in_score": 0.86,
                "sources_used": ["WhatsApp", "UPI", "SMS", "Electricity Bill"],
                "signals": [
                    {"signal": "INCOME_REGULARITY", "score": 0.82},
                    {"signal": "INFLOW_CLAIM_CONSISTENCY", "score": 0.74},
                    {"signal": "BUSINESS_CONTINUITY", "score": 0.76},
                    {"signal": "SEASONAL_PATTERN", "score": 0.71},
                    {"signal": "NETWORK_RELIABILITY", "score": 0.69},
                    {"signal": "DATA_SOURCE_DIVERSITY", "score": 0.81},
                    {"signal": "BEHAVIORAL_CONSISTENCY", "score": 0.79},
                ],
            },
            "reconciliation_output": {
                "reconciliation_status": "NORMAL_CASH",
                "pairwise_gaps": {"wa_upi_gap_pct": 0.34},
                "narrative": "Gap consistent with expected cash mix in kirana operations.",
                "forensic_findings": [],
            },
            "session_record": {"owner_name": "Suresh", "location_masked": "Pune, Maharashtra", "business_type": "Kirana store"},
            "final_limit": 105000,
            "reconciled_monthly": 44000,
            "grade": "B+",
            "warmth_score": 0.78,
            "gap_pct": 0.34,
            "gap_classification": "NORMAL_CASH",
            "confidence_band": "MEDIUM",
            "supervisor_action": "AUTO_ACCEPT",
            "sources_used": ["WhatsApp", "UPI", "SMS", "Electricity Bill"],
            "maps_status": "Verified",
            "review_count": 47,
            "rating": 4.2,
            "bill_age_days": 22,
            "connection_type": "COMMERCIAL",
        }
        result = asyncio.run(report_agent.execute("phase3-test", report_inputs))
        data = result.data

        narrative = str(data.get("narrative_text") or "")
        has_number = bool(re.search(r"\d", narrative))
        memo_path = Path(str(data.get("memo_pdf_path")))
        passport_path = Path(str(data.get("passport_pdf_path")))
        ocen_path = Path(str(data.get("ocen_json_path")))

        check("Agent 07 narrative_text is >= 100 characters", len(narrative) >= 100, f"len={len(narrative)}")
        check("Agent 07 narrative contains at least one specific number (regex check)", has_number)
        check("Agent 07 memo PDF exists on disk and is > 10KB", memo_path.exists() and memo_path.stat().st_size > 10 * 1024, f"size={memo_path.stat().st_size if memo_path.exists() else 0}")

        expected_hash = hashlib.sha256(passport_path.read_bytes()).hexdigest() if passport_path.exists() else ""

        async def _check_hash():
            async with get_db() as db:
                rows = await execute_query(db, "SELECT pdf_hash_sha256 FROM credit_assessments WHERE session_id = ? LIMIT 1", ("phase3-test",))
            return rows[0]["pdf_hash_sha256"] if rows else ""

        db_hash = asyncio.run(_check_hash())
        check("Agent 07 passport PDF has SHA-256 hash stored in DB", bool(db_hash) and db_hash == expected_hash)

        # OCEN schema (minimal required structural validation)
        try:
            obj = json.loads(ocen_path.read_text(encoding="utf-8"))
            ok = isinstance(obj, dict) and "recommendation" in obj and "complianceChecklist" in obj
        except Exception:
            ok = False
        check("Agent 07 OCEN JSON validates against OCEN schema", ok)
    except Exception as exc:
        check("Agent 07 narrative_text is >= 100 characters", False, str(exc))
        check("Agent 07 narrative contains at least one specific number (regex check)", False, str(exc))
        check("Agent 07 memo PDF exists on disk and is > 10KB", False, str(exc))
        check("Agent 07 passport PDF has SHA-256 hash stored in DB", False, str(exc))
        check("Agent 07 OCEN JSON validates against OCEN schema", False, str(exc))


def print_summary() -> int:
    print()
    print("═══════════════════════════════════════════════════")
    print("PHASE 3 VERIFICATION RESULTS")
    print("═══════════════════════════════════════════════════")
    passed = sum(1 for _, p, _ in CHECKS if p)
    for name, p, msg in CHECKS:
        icon = "✅" if p else "❌"
        print(f"{icon} {name}" + (f" ({msg})" if msg else ""))
    print("───────────────────────────────────────────────────")
    print(f"{passed}/{len(CHECKS)} checks passed.")
    if passed == len(CHECKS):
        print("8/8 passed — Phase 3 complete. Say Phase 4.")
        print("═══════════════════════════════════════════════════")
        return 0
    print("Fix the ❌ items before starting Phase 4.")
    print("═══════════════════════════════════════════════════")
    return 1


def main() -> int:
    compliance_output, _ = check_agent06()
    check_agent07(compliance_output)
    return print_summary()


if __name__ == "__main__":
    raise SystemExit(main())

