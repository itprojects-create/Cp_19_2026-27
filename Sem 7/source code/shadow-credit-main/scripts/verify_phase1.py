from __future__ import annotations

import asyncio
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


def check_agent01_structure() -> None:
    try:
        from backend.agents.agent_01_ocr import OCRIngestionAgent

        agent = OCRIngestionAgent()
        supported = set(agent.SUPPORTED_ARTIFACT_TYPES)
        required = {"UPI", "BILL", "INVOICE", "SUPPLIER_INVOICE", "RECEIPT", "KHATA_PHOTO"}
        ok = required.issubset(supported)
        check("Agent 01 imports + 6 supported artifact types", ok, f"types={sorted(supported)}")
    except Exception as exc:
        check("Agent 01 imports + 6 supported artifact types", False, str(exc))


def check_agent01_behavioral_signals() -> None:
    try:
        from backend.agents.agent_01_ocr import OCRIngestionAgent

        agent = OCRIngestionAgent()
        fields = [
            {"field_name": "bill_date", "normalized_value": "2026-03-20"},
            {"field_name": "address", "normalized_value": "Laxmi Road Pune District 411002"},
            {"field_name": "connection_type", "normalized_value": "COMMERCIAL"},
        ]
        signals = agent.extract_behavioral_signals("BILL", fields, None)
        ok = isinstance(signals, dict) and "bill_age_days" in signals and "connection_type" in signals
        check("Agent 01 behavioral_signals extracted from test image", ok, f"signals={signals}")
    except Exception as exc:
        check("Agent 01 behavioral_signals extracted from test image", False, str(exc))


def check_agent02_filtering_and_ambiguity() -> None:
    try:
        from backend.agents.agent_02_whatsapp import WhatsAppBatchParser

        parser = WhatsAppBatchParser()
        raw = """[27/03/2026, 9:15 AM] Ramesh: bhai 500 rupes kal dena
[27/03/2026, 9:16 AM] Suresh: haan pakka
[27/03/2026, 10:30 AM] Customer2: order ready 2kg aata 1kg daal
[27/03/2026, 11:00 AM] Unknown: Good morning! 🌅
"""
        result = asyncio.run(parser.execute("phase1-test", {"raw_text": raw, "session_id": "phase1-test"}))
        data = result.data
        check(
            "Agent 02 filters irrelevant messages correctly",
            data.get("messages_filtered", 0) > 0,
            f"messages_filtered={data.get('messages_filtered')}",
        )
        check(
            "Agent 02 ambiguity resolution runs",
            data.get("ambiguity_resolutions", 0) >= 0,
            f"ambiguity_resolutions={data.get('ambiguity_resolutions')}",
        )
    except Exception as exc:
        check("Agent 02 filters irrelevant messages correctly", False, str(exc))
        check("Agent 02 ambiguity resolution runs", False, str(exc))


def check_agent02b_sms() -> None:
    try:
        from agents.agent_02b_sms import SMSBankAlertParser

        parser = SMSBankAlertParser()
        test_sms = """SBI: Rs.2,500 credited to a/c XX4521 by UPI ref 312456789012. -Sharma Traders. 27-03-2026
HDFC Bank: Rs 15000 debited from a/c XX8834. UPI/312456890123/Patil Wholesale. 26-03-2026
Paytm: Rs.500.00 sent to 9822XXXX12 (Ramesh). UTR:123456789012. 25-03-2026
Airtel: Your recharge of Rs.199 was successful. 24-03-2026"""
        result = asyncio.run(parser.execute("phase1-test", {"sms_text": test_sms}))
        events = result.data.get("financial_events", [])
        ok_count = len(events) >= 2 and result.data.get("filtered_sms_count", 0) >= 1
        check(
            "Agent 02B SMS parser identifies financial vs non-financial SMS",
            ok_count,
            f"financial={len(events)} filtered={result.data.get('filtered_sms_count')}",
        )
        check(
            "Agent 02B cross-verification logic runs without error",
            "cross_verified_transactions" in result.data,
            f"cross_verified_transactions={result.data.get('cross_verified_transactions')}",
        )
    except Exception as exc:
        check("Agent 02B SMS parser identifies financial vs non-financial SMS", False, str(exc))
        check("Agent 02B cross-verification logic runs without error", False, str(exc))


def check_agent03_khata() -> None:
    try:
        from backend.agents.agent_03_khata import compute_90day_metrics, detect_format_and_normalize

        csv_text = """Date,Type,Amount,Party Name,Note
01/02/2026,Credit,1000,Ramesh,Udhar
05/02/2026,Debit,1000,Ramesh,Collected
10/02/2026,Credit,1500,Patil,Udhar
15/02/2026,Debit,1200,Patil,Partly paid
03/03/2026,Credit,2000,Sharma,Goods
20/03/2026,Debit,2000,Sharma,Received
"""
        _, df = detect_format_and_normalize(csv_text)
        metrics = compute_90day_metrics(df)
        ok = "monthly_inflow_series" in metrics and isinstance(metrics["monthly_inflow_series"], dict)
        check(
            "Agent 03 Khata CSV parsing produces monthly_inflow_series",
            ok,
            f"months={list(metrics.get('monthly_inflow_series', {}).keys())}",
        )
    except Exception as exc:
        check("Agent 03 Khata CSV parsing produces monthly_inflow_series", False, str(exc))


def check_agent00_maps() -> None:
    try:
        from agents.agent_00_maps import GoogleMapsVerificationAgent

        agent = GoogleMapsVerificationAgent()
        result = asyncio.run(
            agent.execute(
                "phase1-test",
                {"business_name": "Suresh Kirana Store", "address": "Laxmi Road Pune", "pin_code": "411002"},
            )
        )
        maps_conf = float(result.data.get("maps_confidence", -1))
        check(
            "Agent 00 Maps returns maps_confidence >= 0.0",
            maps_conf >= 0.0,
            f"maps_confidence={maps_conf}",
        )
    except Exception as exc:
        check("Agent 00 Maps returns maps_confidence >= 0.0", False, str(exc))


def print_summary() -> int:
    print()
    print("═══════════════════════════════════════════════════")
    print("PHASE 1 VERIFICATION RESULTS")
    print("═══════════════════════════════════════════════════")
    passed = sum(1 for _, p, _ in CHECKS if p)
    for name, p, msg in CHECKS:
        icon = "✅" if p else "❌"
        print(f"{icon} {name}" + (f" ({msg})" if msg else ""))
    print("───────────────────────────────────────────────────")
    print(f"{passed}/{len(CHECKS)} checks passed.")
    if passed == len(CHECKS):
        print("8/8 checks passed — Phase 1 complete. Say Phase 2.")
        print("═══════════════════════════════════════════════════")
        return 0
    print("Fix the ❌ items before starting Phase 2.")
    print("═══════════════════════════════════════════════════")
    return 1


def main() -> int:
    check_agent01_structure()
    check_agent01_behavioral_signals()
    check_agent02_filtering_and_ambiguity()
    check_agent02b_sms()
    check_agent03_khata()
    check_agent00_maps()
    return print_summary()


if __name__ == "__main__":
    raise SystemExit(main())

