import json
from datetime import datetime
from pathlib import Path
import importlib.util

try:
    from backend.core.ai_client import groq_complete_json_async
except Exception:
    from core.ai_client import groq_complete_json_async


def _load_backend_agents():
    try:
        from backend.agents import AgentOutput, BaseAgent  # type: ignore

        return AgentOutput, BaseAgent
    except Exception:
        backend_agents_path = Path(__file__).resolve().parents[1] / "backend" / "agents" / "__init__.py"
        spec = importlib.util.spec_from_file_location("shadow_backend_agents", str(backend_agents_path))
        if spec is None or spec.loader is None:
            raise ImportError("Unable to load backend.agents BaseAgent/AgentOutput")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.AgentOutput, module.BaseAgent


AgentOutput, BaseAgent = _load_backend_agents()


def _f(value, default=0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _sum_inflow(events: list[dict] | None) -> float:
    total = 0.0
    for event in events or []:
        if not isinstance(event, dict):
            continue
        if str(event.get("direction", "")).lower() != "inflow":
            continue
        total += max(0.0, _f(event.get("amount"), 0.0))
    return total


def _gap_classification(gap_pct: float) -> str:
    if gap_pct <= 0.35:
        return "NORMAL_CASH"
    if gap_pct <= 0.50:
        return "ACCEPTABLE"
    if gap_pct <= 0.65:
        return "DATA_GAP"
    return "SUSPICIOUS"


def _fallback_hypotheses(gap_pct: float, gap_amount: float, business_type: str) -> list[dict]:
    business_type = (business_type or "Kirana store").lower()
    if "kirana" in business_type:
        normal_band = "25-35%"
    elif "tailor" in business_type:
        normal_band = "15-25%"
    elif "auto" in business_type:
        normal_band = "40-60%"
    else:
        normal_band = "20-40%"

    cash_prob = 0.62 if gap_pct <= 0.50 else 0.35
    data_gap_prob = 0.25 if gap_pct <= 0.50 else 0.35
    suspicious_prob = max(0.05, 1.0 - cash_prob - data_gap_prob)

    return [
        {
            "label": "Cash transactions not digitized",
            "probability": round(cash_prob, 2),
            "supporting_evidence": [
                f"Observed revenue gap is ₹{gap_amount:,.0f} ({gap_pct:.1%}).",
                f"{business_type.title()} cash pattern benchmark is {normal_band}.",
            ],
            "contradicting_evidence": ["SMS and UPI evidence does not fully cover WhatsApp-stated revenue."],
            "risk_implication": "ACCEPTABLE" if gap_pct <= 0.50 else "MONITOR",
        },
        {
            "label": "Data capture lag / partial records",
            "probability": round(data_gap_prob, 2),
            "supporting_evidence": [
                "WhatsApp, SMS, and UPI channels are asynchronous and may be incomplete.",
                "Bank SMS streams often omit some channels or delayed postings.",
            ],
            "contradicting_evidence": ["Persistent high gap can indicate unverified turnover claims."],
            "risk_implication": "MONITOR",
        },
        {
            "label": "Potential overstatement of turnover",
            "probability": round(suspicious_prob, 2),
            "supporting_evidence": ["Gap remains elevated after cross-source comparison."],
            "contradicting_evidence": ["Cash-heavy MSME behavior can explain part of the mismatch."],
            "risk_implication": "FLAG" if gap_pct > 0.65 else "MONITOR",
        },
    ]


class ReconciliationAgent(BaseAgent):
    agent_id = "AGENT_05_RECONCILIATION"
    name = "Forensic Reconciliation Agent"
    version = "1.0.0"

    def __init__(self, audit_logger=None, event_bus=None, settings=None):
        if audit_logger is None and event_bus is None and settings is None:
            self.audit_logger = None
            self.event_bus = None
            self.settings = None
        else:
            super().__init__(audit_logger, event_bus, settings)

    async def _log_audit(self, session_id: str, action_type: str, payload: dict):
        if not self.audit_logger:
            return
        try:
            await self.audit_logger.log(
                db=None,
                session_id=session_id,
                event_type=action_type,
                agent_id=self.agent_id,
                details=payload,
            )
        except Exception:
            return

    def _build_prompt(self, matrix: dict, inputs: dict) -> str:
        business_type = inputs.get("business_type") or "Kirana store"
        location = inputs.get("location_masked") or "Unknown"
        date_range = inputs.get("date_range") or "Unknown"
        weekly_summary = inputs.get("weekly_summary") or []
        unique_counterparties = inputs.get("unique_counterparties") or 0
        peak_hour_activity_pct = _f(inputs.get("peak_hour_activity_pct"), 0.0)
        return f"""
Analyze this financial reconciliation for an Indian MSME credit case.

Business type: {business_type}
Location: {location}
Data period: {date_range}

SOURCE COMPARISON:
WhatsApp-stated revenue: ₹{matrix['whatsapp_total']:,.0f}
UPI digital receipts: ₹{matrix['upi_screenshot_total']:,.0f}
SMS bank alerts: ₹{matrix['sms_total']:,.0f}
Khata ledger: ₹{matrix['khata_total']:,.0f} {'(available)' if matrix['khata_total'] > 0 else '(not provided)'}
Gap amount: ₹{matrix['gap_wa_vs_upi']:,.0f} ({matrix['gap_pct']:.1%} of stated revenue)
Cross-verified transactions: {matrix['cross_verified_amount']}

TRANSACTION PATTERNS:
Weekly inflows: {json.dumps(weekly_summary)}
Unique counterparties: {unique_counterparties}
Peak activity: {peak_hour_activity_pct:.0%} during business hours

Generate a forensic analysis as JSON:
{{
  "hypotheses": [
    {{
      "label": str,
      "probability": float,
      "supporting_evidence": [str],
      "contradicting_evidence": [str],
      "risk_implication": "ACCEPTABLE"|"MONITOR"|"FLAG"
    }}
  ],
  "primary_explanation": str,
  "gap_classification": "NORMAL_CASH"|"DATA_GAP"|"SUSPICIOUS"|"ACCEPTABLE",
  "rbi_context": str,
  "recommended_action": "PROCEED"|"REQUEST_CLARIFICATION"|"ESCALATE",
  "credit_impact": str,
  "forensic_narrative": str
}}
"""

    async def _groq_reasoning(self, prompt: str) -> dict | None:
        system = (
            "You are a senior credit forensic analyst at an Indian NBFC. "
            "Your analysis must be specific, RBI-grounded, and uncertainty-aware. "
            "Return ONLY valid JSON."
        )

        try:
            result = await groq_complete_json_async(system_prompt=system, user_content=prompt, temperature=0.1)
            return result if isinstance(result, dict) else None
        except Exception:
            strict_prompt = prompt + "\nIMPORTANT: Output must be strictly valid JSON object. No markdown."
            try:
                result = await groq_complete_json_async(system_prompt=system, user_content=strict_prompt, temperature=0.1)
                return result if isinstance(result, dict) else None
            except Exception:
                return None

    async def execute(self, session_id: str, inputs: dict) -> AgentOutput:
        started = datetime.utcnow()
        try:
            whatsapp_total = _f(inputs.get("whatsapp_total"), _sum_inflow(inputs.get("whatsapp_events")))
            sms_total = _f(inputs.get("sms_total"), _sum_inflow(inputs.get("sms_events")))
            upi_total = _f(inputs.get("upi_total"), _sum_inflow(inputs.get("upi_events")))
            khata_total = _f(inputs.get("khata_total"), 0.0)
            cross_verified_amount = _f(inputs.get("cross_verified_amount"), 0.0)

            gap_wa_vs_sms = whatsapp_total - sms_total
            gap_wa_vs_upi = whatsapp_total - upi_total
            baseline = min(v for v in [sms_total, upi_total] if v > 0) if (sms_total > 0 or upi_total > 0) else 0.0
            gap_pct = ((whatsapp_total - baseline) / whatsapp_total) if whatsapp_total > 0 else 0.0
            gap_pct = max(0.0, gap_pct)

            matrix = {
                "whatsapp_total": round(whatsapp_total, 2),
                "sms_total": round(sms_total, 2),
                "upi_screenshot_total": round(upi_total, 2),
                "khata_total": round(khata_total, 2),
                "gap_wa_vs_sms": round(gap_wa_vs_sms, 2),
                "gap_wa_vs_upi": round(gap_wa_vs_upi, 2),
                "gap_pct": round(gap_pct, 4),
                "cross_verified_amount": round(cross_verified_amount, 2),
            }

            prompt = self._build_prompt(matrix, inputs)
            groq_payload = await self._groq_reasoning(prompt)
            await self._log_audit(session_id, "RECONCILIATION_GROQ_RESPONSE", {"groq_response": groq_payload})

            if groq_payload and isinstance(groq_payload, dict) and "hypotheses" in groq_payload:
                out = groq_payload
            else:
                hypotheses = _fallback_hypotheses(gap_pct, gap_wa_vs_upi, str(inputs.get("business_type") or "Kirana store"))
                gap_class = _gap_classification(gap_pct)
                if gap_class in {"NORMAL_CASH", "ACCEPTABLE"}:
                    action = "PROCEED"
                elif gap_class == "DATA_GAP":
                    action = "REQUEST_CLARIFICATION"
                else:
                    action = "ESCALATE"
                out = {
                    "hypotheses": hypotheses,
                    "primary_explanation": (
                        f"Most likely explanation is non-digitized cash flow mixed with partial channel capture. "
                        f"Observed gap is ₹{gap_wa_vs_upi:,.0f} ({gap_pct:.1%})."
                    ),
                    "gap_classification": gap_class,
                    "rbi_context": (
                        "RBI MSME observations indicate meaningful cash usage in informal businesses; "
                        "moderate gaps are not automatically suspicious."
                    ),
                    "recommended_action": action,
                    "credit_impact": (
                        "Proceed with caution and monitor reconciliation trend."
                        if action != "ESCALATE"
                        else "Escalate for enhanced due diligence before sanction."
                    ),
                    "forensic_narrative": (
                        f"WhatsApp-reported inflow is ₹{whatsapp_total:,.0f}, while UPI and SMS confirm lower digital realization. "
                        f"The reconciliation gap of ₹{gap_wa_vs_upi:,.0f} indicates a mixed cash-digital operating model with possible data capture lag. "
                        "Given Indian MSME transaction behavior, this pattern can be economically plausible in kirana-like businesses. "
                        "Recommendation is based on gap severity and cross-source convergence rather than a single-channel reading."
                    ),
                }

            data = {
                "comparison_matrix": matrix,
                "gap_amount": round(gap_wa_vs_upi, 2),
                "hypotheses": out.get("hypotheses", []),
                "primary_explanation": out.get("primary_explanation"),
                "gap_classification": out.get("gap_classification"),
                "rbi_context": out.get("rbi_context"),
                "recommended_action": out.get("recommended_action"),
                "credit_impact": out.get("credit_impact"),
                "forensic_narrative": out.get("forensic_narrative"),
            }

            gap_class = str(data.get("gap_classification") or "")
            if gap_class in {"NORMAL_CASH", "ACCEPTABLE"}:
                conf = 0.84
            elif gap_class == "DATA_GAP":
                conf = 0.68
            else:
                conf = 0.52

            latency_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=True,
                data=data,
                confidence_score=conf,
                latency_ms=latency_ms,
                errors=[],
                warnings=[],
                fallback_used=groq_payload is None,
            )
        except Exception as exc:
            latency_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=False,
                data={},
                confidence_score=0.0,
                latency_ms=latency_ms,
                errors=[str(exc)],
                warnings=[],
                fallback_used=False,
            )
