from __future__ import annotations

import asyncio
import json
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


def check_agent04_warmth() -> tuple[dict, dict]:
    try:
        from agents.agent_04_warmth import CreditWarmthScoreAgent

        mock_inputs = {
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
        agent = CreditWarmthScoreAgent()
        result = asyncio.run(agent.execute("phase2-test", mock_inputs))
        data = result.data
        signal_breakdown = data.get("signal_breakdown", [])
        shap_values = data.get("shap_values", [])
        check("Agent 04 warmth_score computed with 7 signals", 0.0 <= float(data.get("warmth_score", -1)) <= 1.0 and len(signal_breakdown) == 7, f"signals={len(signal_breakdown)}")
        check("Agent 04 SHAP values present for all signals", isinstance(shap_values, list) and len(shap_values) == 7, f"shap_values={len(shap_values) if isinstance(shap_values, list) else 'n/a'}")
        return data, mock_inputs
    except Exception as exc:
        check("Agent 04 warmth_score computed with 7 signals", False, str(exc))
        check("Agent 04 SHAP values present for all signals", False, str(exc))
        return {}, {}


def check_agent05_reconciliation() -> dict:
    try:
        from agents.agent_05_reconciliation import ReconciliationAgent

        mock_inputs = {
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
        agent = ReconciliationAgent()
        result = asyncio.run(agent.execute("phase2-test", mock_inputs))
        data = result.data
        hypotheses = data.get("hypotheses", [])
        narrative = data.get("forensic_narrative")
        gap_cls = data.get("gap_classification")
        valid = {"NORMAL_CASH", "DATA_GAP", "SUSPICIOUS", "ACCEPTABLE"}
        check("Agent 05 hypotheses array has >= 2 entries", isinstance(hypotheses, list) and len(hypotheses) >= 2, f"hypotheses={len(hypotheses) if isinstance(hypotheses, list) else 'n/a'}")
        check("Agent 05 forensic_narrative is a non-empty string", isinstance(narrative, str) and len(narrative.strip()) > 0)
        check("Agent 05 gap_classification is one of 4 valid values", gap_cls in valid, f"gap_classification={gap_cls}")
        return data
    except Exception as exc:
        check("Agent 05 hypotheses array has >= 2 entries", False, str(exc))
        check("Agent 05 forensic_narrative is a non-empty string", False, str(exc))
        check("Agent 05 gap_classification is one of 4 valid values", False, str(exc))
        return {}


def check_supervisor_import_and_runtime() -> None:
    try:
        from agents.supervisor import SupervisorAgent

        check("Supervisor imports without error", True)
    except Exception as exc:
        check("Supervisor imports without error", False, str(exc))
        check("Supervisor publishes SUPERVISOR_REASONING event to EventBus", False, str(exc))
        check("Supervisor Claude Decision Point 1 returns valid JSON", False, str(exc))
        check("End-to-end: Supervisor.run_session completes with mock inputs", False, str(exc))
        return

    class MockEventBus:
        def __init__(self):
            self.events = []

        async def publish_agent_event(self, **kwargs):
            self.events.append(kwargs)

    class MockAudit:
        def __init__(self):
            self.logs = []

        async def log(self, *args, **kwargs):
            self.logs.append(kwargs)

    try:
        event_bus = MockEventBus()
        audit = MockAudit()
        sup = SupervisorAgent(audit_logger=audit, event_bus=event_bus, settings=None)
        # Force fallback JSON path to make Decision Point 1 deterministic for test.
        async def fake_claude(system_prompt: str, user_prompt: str, fallback: dict) -> dict:
            return fallback

        sup._claude_json = fake_claude  # type: ignore
        result = asyncio.run(sup.run_session("phase2-session", ["whatsapp", "sms"]))

        has_reasoning_event = any((evt.get("data") or {}).get("type") == "SUPERVISOR_REASONING" for evt in event_bus.events)
        d1 = result.get("supervisor_decision_1")
        d1_valid = isinstance(d1, dict) and isinstance(d1.get("phase_b_order"), list) and "reasoning" in d1
        completed = isinstance(result, dict) and "pipeline_complete" in result and "elapsed_ms" in result
        check("Supervisor publishes SUPERVISOR_REASONING event to EventBus", has_reasoning_event, f"events={len(event_bus.events)}")
        check("Supervisor Claude Decision Point 1 returns valid JSON", d1_valid, json.dumps(d1)[:120] if isinstance(d1, dict) else "no d1")
        check("End-to-end: Supervisor.run_session completes with mock inputs", completed)
    except Exception as exc:
        check("Supervisor publishes SUPERVISOR_REASONING event to EventBus", False, str(exc))
        check("Supervisor Claude Decision Point 1 returns valid JSON", False, str(exc))
        check("End-to-end: Supervisor.run_session completes with mock inputs", False, str(exc))


def check_multisource_boost_audit() -> None:
    try:
        from agents.agent_04_warmth import CreditWarmthScoreAgent

        class MockAudit:
            def __init__(self):
                self.logs = []

            async def log(self, *args, **kwargs):
                self.logs.append(kwargs)

        class MockEventBus:
            async def publish_agent_event(self, **kwargs):
                return None

        audit = MockAudit()
        bus = MockEventBus()
        agent = CreditWarmthScoreAgent(audit_logger=audit, event_bus=bus, settings=None)
        mock_inputs = {
            "whatsapp_output": {"weekly_summary": [{"week_start": "2026-01-05", "total_inflow": 10000}], "behavioral_signals": {"activity_ratio": 0.9}},
            "upi_output": {"total_inflow": 9000},
            "sms_output": {"monthly_summary": [{"month": "2026-01", "total_inflow": 8000}]},
            "maps_output": {"continuity_from_maps": 0.75},
            "bill_output": {"connection_type": "COMMERCIAL"},
        }
        _ = asyncio.run(agent.execute("phase2-audit", mock_inputs))
        found = False
        for row in audit.logs:
            if row.get("event_type") == "MULTI_SOURCE_CONFIRMATION":
                found = True
                break
        check("Multi-source confidence boost logged to audit_log", found)
    except Exception as exc:
        check("Multi-source confidence boost logged to audit_log", False, str(exc))


def print_summary() -> int:
    print()
    print("═══════════════════════════════════════════════════")
    print("PHASE 2 VERIFICATION RESULTS")
    print("═══════════════════════════════════════════════════")
    passed = sum(1 for _, p, _ in CHECKS if p)
    for name, p, msg in CHECKS:
        icon = "✅" if p else "❌"
        print(f"{icon} {name}" + (f" ({msg})" if msg else ""))
    print("───────────────────────────────────────────────────")
    print(f"{passed}/{len(CHECKS)} checks passed.")
    if passed == len(CHECKS):
        print("10/10 passed — Phase 2 complete. Say Phase 3.")
        print("═══════════════════════════════════════════════════")
        return 0
    print("Fix the ❌ items before starting Phase 3.")
    print("═══════════════════════════════════════════════════")
    return 1


def main() -> int:
    check_agent04_warmth()
    check_agent05_reconciliation()
    check_supervisor_import_and_runtime()
    check_multisource_boost_audit()
    return print_summary()


if __name__ == "__main__":
    raise SystemExit(main())

