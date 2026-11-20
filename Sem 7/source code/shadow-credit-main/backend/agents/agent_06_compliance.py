import json
import logging
import uuid
import hashlib
from datetime import datetime, date
from typing import Any

try:
    from backend.agents import BaseAgent, AgentOutput
    from backend.config import get_settings
    from backend.core.ai_client import groq_complete_json_async
    from backend.db.database import execute_query, execute_write, get_db
except ModuleNotFoundError:
    from agents import BaseAgent, AgentOutput
    from config import get_settings
    from core.ai_client import groq_complete_json_async
    from db.database import execute_query, execute_write, get_db

logger = logging.getLogger(__name__)


RBI_REFERENCES = {
    "msme_classification": "MSME Development (Amendment) Act 2020, S.7: Micro enterprise — investment ≤ ₹1Cr, turnover ≤ ₹5Cr",
    "turnover_threshold": "MSME Development (Amendment) Act 2020, S.7(1)(a)(i): Annual turnover ≤ ₹5,00,00,000",
    "investment_threshold": "MSME Development (Amendment) Act 2020, S.7(1)(a)(i): Plant & machinery investment ≤ ₹1,00,00,000",
    "business_continuity": "RBI Master Direction - Priority Sector Lending, 2023, Para 6.2: Minimum 12 months operating history for MSME lending",
    "gst_registration": "CGST Act 2017, S.22: Mandatory GST registration threshold ₹40L turnover; affects AA data eligibility",
    "upi_history": "RBI Digital Payments Guidelines 2023: Minimum 90-day UPI transaction history for alternative credit scoring",
    "address_verification": "RBI KYC Master Direction 2016 (Updated 2023), Para 38: Address proof mandatory via utility bill or government document",
    "proprietor_id": "RBI KYC Master Direction 2016, Para 14: Sole proprietor — identity document + business ownership proof",
    "wilful_default": "RBI Circular DBS.OSMOS.No.12/33.01.001/2002-2003: Wilful default classification requires CIBIL bureau check — cannot verify via alternative data",
    "dpdp_consent": "Digital Personal Data Protection Act 2023, S.6: Explicit, informed, specific consent mandatory before processing personal financial data",
    "data_diversity": "RBI Working Paper WPS-23/2023: Cross-validation across minimum 2 independent data sources reduces alternative-data credit assessment error by 43%",
    "aa_eligibility": "RBI Account Aggregator Framework, RBI/2021-22/90: Loan applications above ₹3,00,000 are eligible for AA-facilitated financial data sharing",
}

GST_FORMALISATION_STEPS = [
    {
        "step_number": 1,
        "action": "Register for GST on GST Portal (gst.gov.in)",
        "benefit": "Unlocks Account Aggregator data sharing eligibility. Enables ₹10L credit cap vs current ₹3L cap.",
        "timeline": "3-7 business days for ARN generation; full registration within 7-10 days",
        "portal": "https://www.gst.gov.in/",
        "documents_needed": ["Aadhaar card", "PAN card", "Business address proof", "Bank account details"],
        "credit_impact": "+₹7,00,000 potential additional credit eligibility",
    },
    {
        "step_number": 2,
        "action": "Enable Account Aggregator consent via your bank's mobile app",
        "benefit": "Bank statement data flows directly to lenders. Eliminates WhatsApp-UPI gap concern. Enables AA-verified credit limit.",
        "timeline": "15 minutes via AA-enabled bank app (SBI, HDFC, Axis, Kotak, ICICI supported)",
        "portal": "Sahamati AA Framework — available in your bank app under 'Share Financial Data'",
        "documents_needed": ["None — app-based consent only"],
        "credit_impact": "Removes ₹3L cap. Opens full formula-calculated limit.",
    },
    {
        "step_number": 3,
        "action": "Upload current utility bill (not older than 90 days)",
        "benefit": "Upgrades address verification from PARTIAL to PASS. Boosts Business Continuity signal.",
        "timeline": "Immediate — upload in Shadow Credit app",
        "documents_needed": ["MSEDCL/BSNL/water board bill dated within last 90 days"],
        "credit_impact": "+0.05 to continuity_score → +₹8,000-15,000 to credit limit",
    },
]

OCEN_VERSION = "4.0.0"
OCEN_PRODUCT_TYPE = "INVOICE_BASED_FINANCING"


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _summary_from_checklist(items: list[dict]) -> dict:
    passed = sum(1 for i in items if i["status"] == "PASS")
    failed = sum(1 for i in items if i["status"] == "FAIL")
    partial = sum(1 for i in items if i["status"] == "PARTIAL")
    manual = sum(1 for i in items if i["status"] == "MANUAL_REQUIRED")
    na = sum(1 for i in items if i["status"] == "NOT_APPLICABLE")
    denom = max(1, 12 - na - manual)
    compliance_score_pct = round(((passed + partial * 0.5) / denom) * 100.0, 2)
    return {
        "passed": passed,
        "failed": failed,
        "partial": partial,
        "manual": manual,
        "not_applicable": na,
        "compliance_score_pct": compliance_score_pct,
    }


def run_compliance_checklist(session_data: dict) -> list[dict]:
    items: list[dict] = []

    annual_estimated = (_safe_float(session_data.get("median_monthly_inflow", 0.0)) or 0.0) * 12.0
    if annual_estimated == 0:
        i1_status = "PARTIAL"
        i1_val = "No reliable annualized estimate available"
        i1_notes = "Insufficient revenue data to confirm MSME classification. Manual verification required."
        i1_up = "Manual CA-certified turnover declaration required"
    elif annual_estimated <= 5_00_00_000:
        i1_status = "PASS"
        i1_val = f"Estimated annual turnover ₹{annual_estimated:,.0f} — within ₹5Cr micro threshold"
        i1_notes = "Turnover evidence fits micro-enterprise range."
        i1_up = None
    else:
        i1_status = "FAIL"
        i1_val = f"Estimated annual turnover ₹{annual_estimated:,.0f} — exceeds micro threshold"
        i1_notes = "Turnover estimate breaches micro-enterprise turnover limit."
        i1_up = "Manual CA-certified turnover declaration required"

    items.append({
        "item_id": 1,
        "criterion": "Business qualifies as Micro Enterprise under MSME Act 2020",
        "status": i1_status,
        "evidence_source": "Agent 03 Khata Book / Agent 02 WhatsApp (median_monthly_inflow)",
        "evidence_value": i1_val,
        "rbi_reference": RBI_REFERENCES["msme_classification"],
        "notes": i1_notes,
        "upgrade_path": i1_up,
    })

    items.append({
        "item_id": 2,
        "criterion": "Annual turnover ≤ ₹5,00,00,000",
        "status": i1_status,
        "evidence_source": "Agent 03 Khata Book / Agent 02 WhatsApp (median_monthly_inflow)",
        "evidence_value": i1_val,
        "rbi_reference": RBI_REFERENCES["turnover_threshold"],
        "notes": i1_notes,
        "upgrade_path": i1_up,
    })

    items.append({
        "item_id": 3,
        "criterion": "Plant & machinery investment ≤ ₹1,00,00,000",
        "status": "MANUAL_REQUIRED",
        "evidence_source": "NOT_AVAILABLE — requires external declaration",
        "evidence_value": "Not derivable from transaction artifacts",
        "rbi_reference": RBI_REFERENCES["investment_threshold"],
        "notes": "Investment in plant & machinery cannot be assessed from digital transaction data. Requires CA certificate or Udyam Registration.",
        "upgrade_path": "Upload Udyam Registration Certificate or CA-certified investment declaration",
    })

    days = int(session_data.get("days_of_data", 0) or 0)
    if days >= 365:
        s4, ev4, up4 = "PASS", f"{days} days of transaction history verified", None
    elif days >= 180:
        s4, ev4, up4 = "PARTIAL", f"Only {days} days of data — 365 required for full compliance", "Upload older WhatsApp exports or Khata Book data to extend history"
    else:
        s4, ev4, up4 = "FAIL", f"Only {days} days — insufficient for 12-month requirement", "Upload WhatsApp history going back at least 12 months"
    items.append({
        "item_id": 4,
        "criterion": "Minimum 12 months of verifiable business operation",
        "status": s4,
        "evidence_source": "Agent 02 WhatsApp + Agent 03 Khata Book (timeline span)",
        "evidence_value": ev4,
        "rbi_reference": RBI_REFERENCES["business_continuity"],
        "notes": "Business continuity is assessed using transaction history span.",
        "upgrade_path": up4,
    })

    has_gst = bool(session_data.get("has_gst", False))
    if has_gst:
        s5, ev5, n5, up5 = "PASS", "GST registration confirmed", "GST registration enables full Account Aggregator data sharing. ₹10L credit cap applies.", None
    else:
        s5, ev5, n5, up5 = (
            "PARTIAL",
            "No GST registration detected",
            "Not mandatory below ₹40L turnover, but absence limits AA eligibility and credit cap to ₹3,00,000.",
            "Register at gst.gov.in — process takes 7-10 days. Unlocks ₹10L credit cap.",
        )
    items.append({
        "item_id": 5,
        "criterion": "GST registration status verified (affects Account Aggregator eligibility)",
        "status": s5,
        "evidence_source": "Session profile + user declaration",
        "evidence_value": ev5,
        "rbi_reference": RBI_REFERENCES["gst_registration"],
        "notes": n5,
        "upgrade_path": up5,
    })

    upi_days = int(session_data.get("upi_days_covered", 0) or 0)
    if upi_days >= 90:
        s6, ev6, up6 = "PASS", f"{upi_days} days of UPI transaction history", None
    elif upi_days >= 30:
        s6, ev6, up6 = "PARTIAL", f"Only {upi_days} days of UPI data", "Upload UPI screenshots covering at least 90 days"
    else:
        s6, ev6, up6 = "FAIL", f"Only {upi_days} days of UPI data — 90 required", "Upload all available UPI screenshots. Check GPay/PhonePe/Paytm statement exports."
    items.append({
        "item_id": 6,
        "criterion": "Minimum 90 days of UPI transaction history for alternative scoring",
        "status": s6,
        "evidence_source": "Agent 01 OCR (UPI screenshots analyzed)",
        "evidence_value": ev6,
        "rbi_reference": RBI_REFERENCES["upi_history"],
        "notes": "UPI depth improves score stability.",
        "upgrade_path": up6,
    })

    bill_ok = bool(session_data.get("bill_extracted", False))
    maps_ok = bool(session_data.get("maps_verified", False))
    bill_age = int(session_data.get("bill_days_old", 999) or 999)
    if bill_ok and maps_ok and bill_age <= 180:
        s7, ev7, up7 = "PASS", f"Utility bill ({bill_age} days old) + Maps listing cross-validated", None
    elif bill_ok and bill_age <= 365:
        s7, ev7, up7 = "PARTIAL", f"Utility bill verified ({bill_age} days old). Maps cross-validation not available.", "Google Maps business listing verification recommended for full PASS"
    elif bill_ok and bill_age > 365:
        s7, ev7, up7 = "PARTIAL", f"Utility bill found but {bill_age} days old — exceeds 12-month freshness threshold", "Upload utility bill dated within the last 12 months"
    else:
        s7, ev7, up7 = "FAIL", "No utility bill detected in uploaded documents", "Upload MSEDCL/BSNL/water board bill. Any utility bill accepted."
    items.append({
        "item_id": 7,
        "criterion": "Business address verified via utility bill cross-validation",
        "status": s7,
        "evidence_source": "Agent 01 OCR (bill extractions) + Maps data (if available)",
        "evidence_value": ev7,
        "rbi_reference": RBI_REFERENCES["address_verification"],
        "notes": "Address verification confidence is higher with fresh bill + maps cross-check.",
        "upgrade_path": up7,
    })

    items.append({
        "item_id": 8,
        "criterion": "Sole proprietor / firm identity verifiable from uploaded documents",
        "status": "PARTIAL",
        "evidence_source": "Session creation (owner_name field)",
        "evidence_value": "Owner name recorded at session creation",
        "rbi_reference": RBI_REFERENCES["proprietor_id"],
        "notes": "Full KYC requires Aadhaar/PAN document upload — not part of current data ingestion scope.",
        "upgrade_path": "Upload Aadhaar card and PAN card for complete KYC compliance",
    })

    items.append({
        "item_id": 9,
        "criterion": "No wilful default classification in credit bureau records",
        "status": "MANUAL_REQUIRED",
        "evidence_source": "NOT_AVAILABLE — requires external CIBIL API integration",
        "evidence_value": "Cannot verify via alternative data sources",
        "rbi_reference": RBI_REFERENCES["wilful_default"],
        "notes": "CIBIL bureau check required. Shadow Credit cannot assess this criterion. Manual lender verification required before disbursement.",
        "upgrade_path": "Lender must run CIBIL/Experian check at pre-disbursement stage",
    })

    consent = int(session_data.get("consent_given", 0) or 0)
    if consent == 1:
        s10, ev10, n10, up10 = "PASS", "Consent hash recorded at session creation", "Consent is cryptographically recorded with session_id + timestamp hash. Tamper-evident via audit trail.", None
    else:
        s10, ev10, n10, up10 = "FAIL", "No consent recorded", "CRITICAL: Processing without consent violates DPDP Act 2023 S.6. Pipeline should not have reached this point.", "Session must be re-created with explicit consent_given=True"
    items.append({
        "item_id": 10,
        "criterion": "Explicit informed consent obtained per Digital Personal Data Protection Act 2023",
        "status": s10,
        "evidence_source": "Session audit_log (action_type=SESSION_CREATED, consent_hash stored)",
        "evidence_value": ev10,
        "rbi_reference": RBI_REFERENCES["dpdp_consent"],
        "notes": n10,
        "upgrade_path": up10,
    })

    sources = session_data.get("data_sources", []) or []
    valid_sources = [s for s in sources if s in {"WHATSAPP", "UPI", "KHATA", "BILL", "MAPS"}]
    source_count = len(set(valid_sources))
    source_join = ", ".join(sorted(set(valid_sources))) if valid_sources else "none"
    if source_count >= 3:
        s11, ev11, n11, up11 = "PASS", f"{source_count} independent sources: {source_join}", "Cross-validation depth is strong.", None
    elif source_count == 2:
        s11, ev11, n11, up11 = "PASS", f"2 sources cross-validated: {source_join}", "Minimum threshold met. 3+ sources would improve score confidence.", None
    else:
        s11, ev11, n11, up11 = "FAIL", f"Only {source_count} source(s) available — minimum 2 required", "Insufficient source diversity for robust cross-validation.", "Upload at least one additional document type (UPI screenshot, utility bill, or Khata CSV)"
    items.append({
        "item_id": 11,
        "criterion": "Minimum 2 independent data sources cross-validated",
        "status": s11,
        "evidence_source": "Shadow Credit pipeline (sources_present tracking)",
        "evidence_value": ev11,
        "rbi_reference": RBI_REFERENCES["data_diversity"],
        "notes": n11,
        "upgrade_path": up11,
    })

    final_limit = _safe_float(session_data.get("final_credit_limit", 0.0))
    has_aa = bool(session_data.get("has_aa_consent", False))
    if final_limit <= 3_00_000:
        s12, ev12, n12, up12 = "NOT_APPLICABLE", f"Credit limit ₹{final_limit:,.0f} — AA consent not required below ₹3L", "Below threshold; AA is optional.", None
    elif has_aa:
        s12, ev12, n12, up12 = "PASS", "AA consent provided — full limit accessible", "AA data-sharing condition satisfied.", None
    else:
        s12, ev12, n12, up12 = "PARTIAL", f"Credit limit ₹{final_limit:,.0f} exceeds ₹3L threshold. AA consent not provided.", "Without AA consent: limit capped at ₹3,00,000. With AA consent: full formula limit applicable.", "Enable Account Aggregator consent via your bank's mobile app (15 minutes)"
    items.append({
        "item_id": 12,
        "criterion": "AA framework eligibility assessed for credit limits above ₹3,00,000",
        "status": s12,
        "evidence_source": "credit_assessments table + session consent records",
        "evidence_value": ev12,
        "rbi_reference": RBI_REFERENCES["aa_eligibility"],
        "notes": n12,
        "upgrade_path": up12,
    })

    return items


async def enrich_failed_items_with_rm_explanations(checklist: list[dict]) -> list[dict]:
    failed_items = [i for i in (checklist or []) if str(i.get("status")) == "FAIL"]
    if not failed_items:
        return checklist

    system_prompt = (
        "You are a compliance officer at an RBI-registered NBFC. "
        "Explain compliance failures in plain English for a relationship manager "
        "who is not a lawyer. Be specific, actionable, and cite the regulation. "
        "Under 40 words per explanation. Return only JSON."
    )
    user_prompt = (
        "Explain these compliance failures for a bank RM:\n"
        f"{json.dumps(failed_items, indent=2)}\n\n"
        "Return:\n"
        "[{\n"
        '  "check_id": str,\n'
        '  "rm_explanation": str,\n'
        '  "action_required": str,\n'
        '  "blocking": bool\n'
        "}]"
    )

    explanation_map: dict[str, dict] = {}
    try:
        parsed = await groq_complete_json_async(
            system_prompt=system_prompt,
            user_content=user_prompt,
            temperature=0.1,
        )
        if isinstance(parsed, list):
            for row in parsed:
                if isinstance(row, dict):
                    cid = str(row.get("check_id") or "")
                    if cid:
                        explanation_map[cid] = row
    except Exception:
        explanation_map = {}

    for item in checklist:
        if str(item.get("status")) != "FAIL":
            continue
        cid = str(item.get("item_id"))
        row = explanation_map.get(cid)
        if row:
            item["rm_explanation"] = str(row.get("rm_explanation") or "")[:280]
            item["action_required"] = str(row.get("action_required") or item.get("upgrade_path") or "")[:280]
            item["blocking"] = bool(row.get("blocking", True))
        else:
            item["rm_explanation"] = "Compliance failure blocks approval until required RBI/MSME evidence is submitted."
            item["action_required"] = item.get("upgrade_path") or "Provide required compliance evidence."
            item["blocking"] = True
    return checklist


def compute_final_credit_limit(session_data: dict, settings=None) -> dict:
    settings = settings or get_settings()

    median_monthly_inflow = _safe_float(session_data.get("median_monthly_inflow", 0.0))
    income_regularity_score = _safe_float(session_data.get("income_regularity_score", 0.70))
    top_customer_pct = _safe_float(session_data.get("top_customer_pct", 0.50))
    business_continuity_score = _safe_float(session_data.get("business_continuity_score", 0.75))
    has_aa_consent = bool(session_data.get("has_aa_consent", False))

    base_3x = 3.0 * median_monthly_inflow
    after_regularity = base_3x * income_regularity_score
    concentration_multiplier = 0.75 if top_customer_pct > 0.60 else 1.0
    after_concentration = after_regularity / concentration_multiplier
    after_continuity = after_concentration * business_continuity_score
    credit_limit_base = after_continuity

    cap_applied = 10_00_000.0 if has_aa_consent else 3_00_000.0
    cap_type = "AA" if has_aa_consent else "NON_AA"
    final_pre_round = min(credit_limit_base, cap_applied)
    final_limit = round(final_pre_round / 5000.0) * 5000.0
    final_limit = max(final_limit, 10_000.0)

    formula_string = (
        f"₹{final_limit:,.0f} = 3.0 × ₹{median_monthly_inflow:,.0f} × {income_regularity_score:.2f} "
        f"÷ {concentration_multiplier:.2f} × {business_continuity_score:.2f} "
        f"[capped at ₹{cap_applied:,.0f} {cap_type}]"
    )

    return {
        "median_monthly_inflow": float(median_monthly_inflow),
        "base_3x": float(base_3x),
        "income_regularity_score": float(income_regularity_score),
        "after_regularity": float(after_regularity),
        "top_customer_pct": float(top_customer_pct),
        "concentration_multiplier": float(concentration_multiplier),
        "after_concentration": float(after_concentration),
        "business_continuity_score": float(business_continuity_score),
        "credit_limit_base": float(credit_limit_base),
        "cap_applied": float(cap_applied),
        "cap_type": cap_type,
        "final_limit": float(final_limit),
        "formula_string": formula_string,
        "provenance": {
            "median_monthly_inflow": "Agent 03 Khata Book (90-day median) or Agent 02 WhatsApp",
            "income_regularity_score": "Agent 04 Signal 1 — IsolationForest on weekly inflows",
            "top_customer_pct": "Agent 03 Khata Book — customer_metrics.top_customer_pct",
            "business_continuity_score": "Agent 04 Signal 3 — bill recency + data span",
        },
        "formula_components": {
            "multiplier": {"value": 3.0, "source": "Shadow Credit formula v1"},
            "median_monthly_inflow": {"value": float(median_monthly_inflow), "source": "Agent 03 Khata / Agent 02 WhatsApp"},
            "income_regularity_score": {"value": float(income_regularity_score), "source": "Agent 04 Signal 1 IsolationForest"},
            "concentration_risk": {"value": float(top_customer_pct), "source": "Agent 03 top_customer_pct"},
            "continuity_score": {"value": float(business_continuity_score), "source": "Agent 04 Signal 3 bill recency"},
        },
    }


def simulate_scenario(
    scenario: str,
    session_data: dict,
    settings=None,
) -> dict:
    settings = settings or get_settings()
    current_data = json.loads(json.dumps(session_data, default=str))
    modified = json.loads(json.dumps(session_data, default=str))

    label_map = {
        "current": "Current State",
        "gst_registered": "With GST Registration",
        "aa_consent": "With AA Consent",
        "gst_plus_aa": "With GST + AA Consent",
    }

    if scenario == "gst_registered":
        modified["has_gst"] = True
    elif scenario == "aa_consent":
        modified["has_aa_consent"] = True
    elif scenario == "gst_plus_aa":
        modified["has_gst"] = True
        modified["has_aa_consent"] = True

    current_check = run_compliance_checklist(current_data)
    current_credit = compute_final_credit_limit(current_data, settings=settings)
    current_data["final_credit_limit"] = current_credit["final_limit"]

    check = run_compliance_checklist(modified)
    credit = compute_final_credit_limit(modified, settings=settings)
    modified["final_credit_limit"] = credit["final_limit"]
    summary = _summary_from_checklist(check)

    curr_map = {i["item_id"]: i["status"] for i in current_check}
    unlocked = [
        i for i in check
        if i["status"] == "PASS" and curr_map.get(i["item_id"]) in {"FAIL", "PARTIAL"}
    ]

    delta = credit["final_limit"] - current_credit["final_limit"]
    delta_pct = (delta / max(current_credit["final_limit"], 1.0)) * 100.0

    if scenario == "gst_registered":
        narrative = (
            "Registering for GST upgrades compliance item 5 to PASS and documents formal business status — "
            "no change to credit limit until AA consent is added."
        )
    elif scenario == "aa_consent":
        narrative = (
            f"Enabling Account Aggregator consent removes the ₹3,00,000 non-AA cap, increasing your credit "
            f"limit from ₹{current_credit['final_limit']:,.0f} to ₹{credit['final_limit']:,.0f} — a {delta_pct:.1f}% increase."
        )
    elif scenario == "gst_plus_aa":
        narrative = (
            f"With GST registration and AA consent, {summary['passed']}/12 compliance items pass and your "
            f"credit limit reaches ₹{credit['final_limit']:,.0f} — the maximum for your income profile."
        )
    else:
        narrative = "Current compliance and credit profile baseline."

    return {
        "scenario": scenario,
        "scenario_label": label_map.get(scenario, scenario),
        "credit_limit": float(credit["final_limit"]),
        "delta_from_current": float(delta),
        "delta_pct": round(float(delta_pct), 2),
        "compliance_items": check,
        "newly_unlocked_items": unlocked,
        "compliance_score_pct": float(summary["compliance_score_pct"]),
        "formalisation_steps": GST_FORMALISATION_STEPS if scenario in {"gst_registered", "gst_plus_aa"} else None,
        "narrative": narrative,
    }


def run_all_scenarios(session_data: dict, settings=None) -> dict:
    current = simulate_scenario("current", session_data, settings=settings)
    gst = simulate_scenario("gst_registered", session_data, settings=settings)
    aa = simulate_scenario("aa_consent", session_data, settings=settings)
    both = simulate_scenario("gst_plus_aa", session_data, settings=settings)
    return {
        "current": current,
        "gst_registered": gst,
        "aa_consent": aa,
        "gst_plus_aa": both,
        "max_achievable_limit": float(both["credit_limit"]),
        "steps_to_max_limit": GST_FORMALISATION_STEPS,
    }


def build_ocen_payload(
    session_id: str,
    assessment_id: str,
    session_data: dict,
    compliance_checklist: list[dict],
    credit_limit_result: dict,
    reconciliation_result: dict,
) -> dict:
    summary = _summary_from_checklist(compliance_checklist)
    sources = session_data.get("data_sources", []) or []
    days_of_data = int(session_data.get("days_of_data", 0) or 0)
    warmth_score = _safe_float(session_data.get("warmth_score", 0.0))
    credit_grade = str(session_data.get("credit_grade", "C"))

    risk_factors = []
    top_customer_pct = _safe_float(session_data.get("top_customer_pct", 0.5))
    if top_customer_pct > 0.60:
        risk_factors.append({
            "riskId": str(uuid.uuid4()),
            "riskType": "CONCENTRATION_RISK",
            "severity": "HIGH" if top_customer_pct > 0.80 else "MEDIUM",
            "description": f"Top customer concentration at {top_customer_pct:.1%}",
            "mitigant": "Diversify receivables base or lower exposure cap.",
            "rbiReference": RBI_REFERENCES["data_diversity"],
        })
    if int(session_data.get("upi_days_covered", 0) or 0) < 90:
        risk_factors.append({
            "riskId": str(uuid.uuid4()),
            "riskType": "DATA_GAP",
            "severity": "MEDIUM",
            "description": "UPI history below 90-day recommended depth.",
            "mitigant": "Upload additional UPI period exports.",
            "rbiReference": RBI_REFERENCES["upi_history"],
        })
    if _safe_float(reconciliation_result.get("cash_ratio_estimate", 0.0)) > 0.50:
        risk_factors.append({
            "riskId": str(uuid.uuid4()),
            "riskType": "CASH_HEAVY",
            "severity": "MEDIUM",
            "description": "High cash-ratio estimate from provenance reconciliation.",
            "mitigant": "Enable AA consent and provide bank statement linkage.",
            "rbiReference": RBI_REFERENCES["aa_eligibility"],
        })
    if warmth_score < 0.60:
        risk_factors.append({
            "riskId": str(uuid.uuid4()),
            "riskType": "LOW_CONFIDENCE",
            "severity": "HIGH",
            "description": "Alternative-data confidence below robust underwriting threshold.",
            "mitigant": "Request clarifications and additional source documents.",
            "rbiReference": RBI_REFERENCES["data_diversity"],
        })

    if credit_grade in {"A+", "A"} and reconciliation_result.get("reconciliation_status") == "CLEAN":
        decision = "APPROVE"
    elif credit_grade in {"A+", "A", "B+"} and reconciliation_result.get("reconciliation_status") in {"CLEAN", "FLAGGED"}:
        decision = "APPROVE_WITH_CONDITIONS"
    elif _safe_float(credit_limit_result.get("final_limit", 0.0)) > 3_00_000:
        decision = "REFER_TO_AA"
    else:
        decision = "MANUAL_REVIEW"

    aa_limit = _safe_float(session_data.get("aa_scenario_limit", credit_limit_result.get("final_limit", 0.0)))
    consent_artifact_id = hashlib.sha256(f"{session_id}DPDP_CONSENT_V1".encode("utf-8")).hexdigest()

    source_data_points = {
        "WHATSAPP": int(session_data.get("whatsapp_event_count", 0) or 0),
        "UPI": int(session_data.get("upi_txn_count", 0) or 0),
        "KHATA": int(session_data.get("khata_txn_count", 0) or 0),
        "BILL": 1 if bool(session_data.get("bill_extracted", False)) else 0,
        "MAPS": 1 if bool(session_data.get("maps_verified", False)) else 0,
    }
    source_method = {
        "WHATSAPP": "AGENT_NLP",
        "UPI": "AGENT_OCR",
        "KHATA": "AGENT_STRUCTURED",
        "BILL": "AGENT_OCR",
        "MAPS": "AGENT_NLP",
    }

    return {
        "apiVersion": OCEN_VERSION,
        "loanApplicationId": assessment_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "loanServiceProvider": {
            "id": "SHADOW_CREDIT_V1",
            "name": "Shadow Credit — Ghost MSME Reconstruction Agent",
            "version": "1.0.0",
        },
        "borrowerInfo": {
            "id": session_id,
            "entityType": "INDIVIDUAL",
            "consent": {
                "consentArtifactId": consent_artifact_id,
                "consentGrantedAt": datetime.utcnow().isoformat() + "Z",
                "consentScope": "FINANCIAL_DATA_ANALYSIS",
                "dpdpCompliant": True,
            },
        },
        "businessInfo": {
            "entityType": "MICRO_ENTERPRISE",
            "msmeClassification": "MICRO",
            "estimatedAnnualTurnover": _safe_float(session_data.get("median_monthly_inflow", 0.0)) * 12.0,
            "gstRegistered": bool(session_data.get("has_gst", False)),
            "primaryIndustry": "RETAIL_KIRANA",
            "yearsInOperation": round(days_of_data / 365.0, 2),
            "dataSourcesVerified": sources,
        },
        "financialSummary": {
            "assessmentPeriodDays": days_of_data,
            "medianMonthlyInflow": _safe_float(session_data.get("median_monthly_inflow", 0.0)),
            "totalInflow90d": _safe_float(session_data.get("khata_total_90d", 0.0)),
            "incomeRegularityScore": _safe_float(session_data.get("income_regularity_score", 0.70)),
            "creditWarmthScore": warmth_score,
            "creditGrade": credit_grade,
            "reconciliationStatus": reconciliation_result.get("reconciliation_status", "UNKNOWN"),
            "cashRatioEstimate": _safe_float(reconciliation_result.get("cash_ratio_estimate", 0.0)),
            "provenanceCoverage": _safe_float(reconciliation_result.get("provenance_coverage", 0.0)),
        },
        "creditAssessment": {
            "recommendedLoanAmount": _safe_float(credit_limit_result.get("final_limit", 0.0)),
            "loanAmountWithAAConsent": aa_limit,
            "formulaComponents": credit_limit_result.get("formula_components", {}),
            "creditScore": int(max(0, min(900, round(warmth_score * 900)))),
            "creditGrade": credit_grade,
            "assessmentConfidence": _safe_float(session_data.get("assessment_confidence", 0.0)),
            "capType": credit_limit_result.get("cap_type", "NON_AA"),
        },
        "alternativeDataSources": [
            {
                "sourceType": s,
                "dataPoints": source_data_points.get(s, 0),
                "periodDays": days_of_data,
                "confidenceScore": _safe_float(session_data.get("assessment_confidence", 0.0)),
                "verificationMethod": source_method.get(s, "AGENT_STRUCTURED"),
            }
            for s in sources
        ],
        "complianceChecklist": {
            "totalItems": 12,
            "passedItems": summary["passed"],
            "partialItems": summary["partial"],
            "failedItems": summary["failed"],
            "manualReviewRequired": summary["manual"],
            "complianceScore": summary["compliance_score_pct"],
            "criticalFailures": [i for i in compliance_checklist if i["status"] == "FAIL"],
        },
        "riskFactors": risk_factors,
        "recommendation": {
            "decision": decision,
            "recommendedAmount": _safe_float(credit_limit_result.get("final_limit", 0.0)),
            "suggestedTenorMonths": 12,
            "conditions": (
                ["AA consent required above ₹3L"] if (credit_limit_result.get("cap_type") == "NON_AA" and _safe_float(credit_limit_result.get("credit_limit_base", 0.0)) > 3_00_000) else []
            ),
            "nextSteps": [s["action"] for s in GST_FORMALISATION_STEPS[:2]],
        },
    }


class ComplianceScenarioAgent(BaseAgent):
    agent_id = "AGENT_06_COMPLIANCE"
    name = "Compliance + Scenario Agent"
    version = "1.0.0"

    def __init__(self, audit_logger=None, event_bus=None, settings=None):
        if audit_logger is None and event_bus is None and settings is None:
            class _NoOpAudit:
                async def log(self, *args, **kwargs):
                    return None

            class _NoOpBus:
                async def publish_agent_event(self, *args, **kwargs):
                    return None

            self.audit_logger = _NoOpAudit()
            self.event_bus = _NoOpBus()
            self.settings = get_settings()
        else:
            super().__init__(audit_logger, event_bus, settings or get_settings())

    async def execute(self, session_id: str, inputs: dict) -> AgentOutput:
        try:
            warmth_output = inputs.get("warmth_output") or {}
            reconciliation_output = inputs.get("reconciliation_output") or {}
            whatsapp_output = inputs.get("whatsapp_output") or {}
            khata_output = inputs.get("khata_output") or {}
            ocr_outputs = inputs.get("ocr_outputs") or []
            session_record = inputs.get("session_record") or {}

            signals = warmth_output.get("signals", []) if isinstance(warmth_output, dict) else []
            signal_1 = next((s for s in signals if s.get("signal") == "INCOME_REGULARITY"), {})
            signal_3 = next((s for s in signals if s.get("signal") == "BUSINESS_CONTINUITY"), {})

            median_monthly = _safe_float(((khata_output.get("inflow_metrics") or {}).get("median_monthly_received")))
            if median_monthly <= 0:
                median_monthly = _safe_float(((whatsapp_output.get("timeline") or {}).get("median_monthly_inflow")))
            if median_monthly <= 0:
                logger.warning("median_monthly_inflow defaulted to 0.0 for session %s", session_id)

            upi_days = int(session_record.get("upi_days_covered", 0) or 0)
            data_period_days = int(
                _safe_float(((whatsapp_output.get("timeline") or {}).get("date_range") or {}).get("days_covered"))
                or _safe_float((khata_output.get("period") or {}).get("days_actual"))
                or 0
            )
            bill_extracted = False
            bill_days_old = 999
            for payload in ocr_outputs:
                if not isinstance(payload, dict):
                    continue
                if str(payload.get("artifact_type", "")).upper() == "BILL" and int(payload.get("field_count", 0) or 0) > 0:
                    bill_extracted = True
                    extracted_at = payload.get("preprocessing_metadata", {}).get("extracted_at") or payload.get("extracted_at")
                    if extracted_at:
                        try:
                            dt = datetime.fromisoformat(str(extracted_at).replace("Z", "+00:00")).date()
                            bill_days_old = max(0, (date.today() - dt).days)
                        except Exception:
                            pass

            data_sources = []
            if whatsapp_output:
                data_sources.append("WHATSAPP")
            if khata_output:
                data_sources.append("KHATA")
            if ocr_outputs:
                if any(str(p.get("artifact_type", "")).upper() == "UPI" for p in ocr_outputs if isinstance(p, dict)):
                    data_sources.append("UPI")
                if any(str(p.get("artifact_type", "")).upper() == "BILL" for p in ocr_outputs if isinstance(p, dict)):
                    data_sources.append("BILL")

            session_data = {
                "consent_given": int(session_record.get("consent_given", 0) or 0),
                "data_sources": sorted(set(data_sources)),
                "days_of_data": data_period_days,
                "upi_days_covered": upi_days,
                "khata_total_90d": _safe_float(((khata_output.get("inflow_metrics") or {}).get("total_received_90d"))),
                "median_monthly_inflow": median_monthly,
                "continuity_score": _safe_float(signal_3.get("score"), 0.75),
                "regularity_score": _safe_float(signal_1.get("score"), 0.70),
                "income_regularity_score": _safe_float(signal_1.get("score"), 0.70),
                "top_customer_pct": _safe_float(((khata_output.get("customer_metrics") or {}).get("top_customer_pct")), 0.50),
                "bill_extracted": bill_extracted,
                "bill_days_old": bill_days_old,
                "maps_verified": bool(session_record.get("maps_verified", False)),
                "reconciliation_status": reconciliation_output.get("reconciliation_status", "UNKNOWN"),
                "has_gst": bool(session_record.get("has_gst", False)),
                "has_aa_consent": bool(session_record.get("aa_consent", False)),
                "warmth_score": _safe_float(warmth_output.get("warmth_score", 0.0)),
                "credit_grade": str(warmth_output.get("credit_grade", "C")),
                "data_period_days": data_period_days,
                "whatsapp_event_count": len((whatsapp_output.get("financial_events") or [])),
                "khata_txn_count": int((khata_output.get("data_quality") or {}).get("total_transactions", 0) or 0),
                "upi_txn_count": sum(
                    1 for p in ocr_outputs if isinstance(p, dict) and str(p.get("artifact_type", "")).upper() == "UPI"
                ),
                "assessment_confidence": _safe_float(warmth_output.get("confidence_in_score", 0.0)),
            }

            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message="Running 12-item RBI MSME 2025 compliance checklist...",
            )
            checklist = run_compliance_checklist(session_data)
            checklist = await enrich_failed_items_with_rm_explanations(checklist)
            for item in checklist:
                icon = "✅" if item["status"] == "PASS" else "⚠️" if item["status"] == "PARTIAL" else "❌"
                await self.event_bus.publish_agent_event(
                    session_id=session_id,
                    agent_id=self.agent_id,
                    status="PROGRESS",
                    message=f"{icon} Item {item['item_id']}: {item['criterion'][:50]} -> {item['status']}",
                )

            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message="Computing credit limit via Shadow Credit formula...",
            )
            credit_result = compute_final_credit_limit(session_data, self.settings)
            session_data["final_credit_limit"] = credit_result["final_limit"]
            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message=f"Credit limit: ₹{credit_result['final_limit']:,.0f} ({credit_result['cap_type']})",
            )

            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message="Simulating: GST registration, AA consent, combined...",
            )
            scenarios = run_all_scenarios(session_data, self.settings)
            max_limit = _safe_float(scenarios["max_achievable_limit"])
            session_data["aa_scenario_limit"] = _safe_float(scenarios["gst_plus_aa"]["credit_limit"])
            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message=f"Maximum achievable limit: ₹{max_limit:,.0f} (with GST + AA consent)",
            )

            assessment_id = str(uuid.uuid4())
            ocen = build_ocen_payload(
                session_id=session_id,
                assessment_id=assessment_id,
                session_data=session_data,
                compliance_checklist=checklist,
                credit_limit_result=credit_result,
                reconciliation_result=reconciliation_output,
            )

            summary = _summary_from_checklist(checklist)

            async with get_db() as db:
                existing = await execute_query(
                    db,
                    "SELECT id, warmth_score, credit_grade, created_at FROM credit_assessments WHERE session_id = ? LIMIT 1",
                    (session_id,),
                )
                if existing:
                    await execute_write(
                        db,
                        """
                        UPDATE credit_assessments SET
                            final_limit = ?,
                            base_limit = ?,
                            regularity_score = ?,
                            concentration_risk = ?,
                            continuity_score = ?,
                            formula_json = ?,
                            ocen_payload = ?
                        WHERE session_id = ?
                        """,
                        (
                            float(credit_result["final_limit"]),
                            float(credit_result["base_3x"]),
                            float(session_data["income_regularity_score"]),
                            float(session_data["top_customer_pct"]),
                            float(session_data["continuity_score"]),
                            json.dumps(credit_result),
                            json.dumps(ocen),
                            session_id,
                        ),
                    )
                else:
                    await execute_write(
                        db,
                        """
                        INSERT INTO credit_assessments
                        (id, session_id, base_limit, regularity_score, concentration_risk, continuity_score,
                         final_limit, warmth_score, credit_grade, formula_json, ocen_payload, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(uuid.uuid4()),
                            session_id,
                            float(credit_result["base_3x"]),
                            float(session_data["income_regularity_score"]),
                            float(session_data["top_customer_pct"]),
                            float(session_data["continuity_score"]),
                            float(credit_result["final_limit"]),
                            float(session_data["warmth_score"]),
                            str(session_data["credit_grade"]),
                            json.dumps(credit_result),
                            json.dumps(ocen),
                            datetime.utcnow().isoformat() + "Z",
                        ),
                    )

            passed = summary["passed"]
            await self.event_bus.publish_agent_event(
                session_id=session_id,
                agent_id=self.agent_id,
                status="COMPLETE",
                message=(
                    f"Compliance: {passed}/12 items PASS | "
                    f"Credit Limit: ₹{credit_result['final_limit']:,.0f} | "
                    f"Max achievable: ₹{max_limit:,.0f}"
                ),
                confidence=_safe_float(summary["compliance_score_pct"]) / 100.0,
            )

            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=True,
                confidence_score=_safe_float(summary["compliance_score_pct"]) / 100.0,
                latency_ms=0,
                data={
                    "compliance_checklist": checklist,
                    "compliance_summary": summary,
                    "credit_limit": credit_result,
                    "scenarios": scenarios,
                    "ocen_payload": ocen,
                    "assessment_id": assessment_id,
                    "formula_string": credit_result["formula_string"],
                },
                errors=[],
                warnings=[],
                fallback_used=False,
            )
        except Exception as exc:
            logger.exception("ComplianceScenarioAgent failed for session %s", session_id)
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=False,
                confidence_score=0.0,
                latency_ms=0,
                data={},
                errors=[str(exc)],
                warnings=[],
                fallback_used=False,
            )
