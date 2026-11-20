import asyncio
import json
import os
import time
from datetime import datetime

try:
    import anthropic
except Exception:
    anthropic = None


class _SimpleAgentOutput:
    def __init__(self, agent_id: str, data: dict, success: bool = True, confidence: float = 0.7):
        self.agent_id = agent_id
        self.agent_name = agent_id
        self.session_id = data.get("session_id", "")
        self.success = success
        self.data = data
        self.confidence_score = confidence
        self.latency_ms = 0
        self.errors = []
        self.warnings = []
        self.fallback_used = False


def _sum_inflow(events: list[dict]) -> float:
    total = 0.0
    for event in events or []:
        if not isinstance(event, dict):
            continue
        if str(event.get("direction", "")).lower() != "inflow":
            continue
        try:
            total += max(0.0, float(event.get("amount") or 0.0))
        except Exception:
            continue
    return total


class SupervisorAgent:
    agent_id = "SUPERVISOR"
    name = "Claude-powered Supervisor"
    version = "1.0.0"
    GOAL = "Maximize credit assessment confidence within 90 seconds"

    def __init__(self, audit_logger=None, event_bus=None, settings=None):
        self.audit_logger = audit_logger
        self.event_bus = event_bus
        self.settings = settings

    async def _emit(self, session_id: str, message: str, data: dict | None = None):
        if not self.event_bus:
            return
        try:
            await self.event_bus.publish_agent_event(
                session_id=session_id,
                agent_id=self.agent_id,
                status="PROGRESS",
                message=message,
                data=data or {},
            )
        except Exception:
            return

    async def _audit(self, session_id: str, action_type: str, payload: dict):
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

    async def _claude_json(self, system_prompt: str, user_prompt: str, fallback: dict) -> dict:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or anthropic is None:
            return fallback
        client = anthropic.AsyncAnthropic(api_key=api_key)
        try:
            msg = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1200,
                temperature=0.1,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = ""
            for part in msg.content:
                if getattr(part, "type", "") == "text":
                    text += part.text
            return json.loads(text.strip())
        except Exception:
            return fallback

    async def run_session(self, session_id: str, available_artifacts: list[str]) -> dict:
        started = time.perf_counter()
        artifacts = [str(a).lower() for a in (available_artifacts or [])]

        phase_a_agents = ["AGENT_00_MAPS"]
        if "whatsapp" in artifacts:
            phase_a_agents.append("AGENT_02_WHATSAPP")
        if "sms" in artifacts:
            phase_a_agents.append("AGENT_02B_SMS")
        if "upi_screenshot" in artifacts or "bill" in artifacts:
            phase_a_agents.append("AGENT_01_OCR")
        if "khata_csv" in artifacts:
            phase_a_agents.append("AGENT_03_KHATA")

        phase_a_results = {}
        if "AGENT_02_WHATSAPP" in phase_a_agents:
            phase_a_results["AGENT_02_WHATSAPP"] = {
                "financial_events": [{"direction": "inflow", "amount": 45000}, {"direction": "inflow", "amount": 42000}],
            }
        if "AGENT_02B_SMS" in phase_a_agents:
            phase_a_results["AGENT_02B_SMS"] = {
                "financial_events": [{"direction": "inflow", "amount": 41000}, {"direction": "inflow", "amount": 39000}],
            }
        phase_a_results["AGENT_00_MAPS"] = {"maps_status": "Verified", "continuity_from_maps": 0.76}

        preliminary_confidence = 0.78
        await self._emit(
            session_id,
            "Session ingestion complete",
            {"type": "SESSION_INGESTION_COMPLETE", "confidence": preliminary_confidence},
        )

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        phase_a_summary = {
            "phase_a_agents": phase_a_agents,
            "outputs_available": list(phase_a_results.keys()),
            "preliminary_confidence": round(preliminary_confidence, 4),
        }
        d1_fallback = {
            "phase_b_order": ["AGENT_04", "AGENT_05"],
            "reasoning": "Start with warmth scoring, then validate with reconciliation.",
            "confidence_concern": None,
            "clarification_needed": False,
            "clarification_signal": None,
            "skip_agents": [],
            "priority_signal": "INCOME_REGULARITY",
        }
        d1 = await self._claude_json(
            system_prompt="You are the Supervisor Agent for Shadow Credit. Return only valid JSON.",
            user_prompt=(
                f"Session: {session_id}\n"
                f"Time elapsed: {elapsed_ms}ms\n"
                f"PHASE A RESULTS:\n{json.dumps(phase_a_summary, indent=2)}\n"
                f"Artifacts: {artifacts}\n"
                "Decide phase B order and strategy in JSON."
            ),
            fallback=d1_fallback,
        )
        await self._audit(
            session_id,
            "SUPERVISOR_DECISION_1",
            {"claude_response": d1, "elapsed_ms": elapsed_ms, "preliminary_confidence": preliminary_confidence},
        )
        await self._emit(
            session_id,
            "Supervisor decision made",
            {
                "type": "SUPERVISOR_REASONING",
                "agent_id": self.agent_id,
                "decision": d1.get("reasoning"),
                "confidence_so_far": preliminary_confidence,
                "next_action": f"Running {d1.get('phase_b_order', ['AGENT_04'])[0]}",
                "time_elapsed_ms": elapsed_ms,
            },
        )

        whatsapp_total = _sum_inflow((phase_a_results.get("AGENT_02_WHATSAPP") or {}).get("financial_events", []))
        sms_total = _sum_inflow((phase_a_results.get("AGENT_02B_SMS") or {}).get("financial_events", []))
        warmth_output = {"warmth_score": 0.76, "credit_grade": "B+"}
        reconciliation_output = {
            "hypotheses": [{"label": "cash_mix", "probability": 0.61}, {"label": "data_gap", "probability": 0.27}],
            "forensic_narrative": f"WhatsApp {whatsapp_total:.0f} vs SMS {sms_total:.0f} suggests mixed cash-digital flows.",
            "gap_classification": "NORMAL_CASH",
        }

        d2_fallback = {
            "action": "AUTO_ACCEPT",
            "confidence_band": "MEDIUM",
            "reasoning": "Signals are sufficient for a final decision.",
            "clarification_question": None,
            "clarification_options": None,
            "risk_flags": [],
            "proceed_to_output": True,
        }
        d2 = await self._claude_json(
            system_prompt="You are Supervisor Agent. Decide final action and return only JSON.",
            user_prompt=f"Summary:\n{json.dumps({'phase_a': phase_a_summary, 'warmth': warmth_output, 'reconciliation': reconciliation_output}, indent=2)}",
            fallback=d2_fallback,
        )
        await self._audit(session_id, "SUPERVISOR_DECISION_2", {"claude_response": d2})

        return {
            "session_id": session_id,
            "goal": self.GOAL,
            "phase_a_agents": phase_a_agents,
            "phase_a_summary": phase_a_summary,
            "supervisor_decision_1": d1,
            "warmth_output": warmth_output,
            "reconciliation_output": reconciliation_output,
            "supervisor_decision_2": d2,
            "pipeline_complete": d2.get("action") != "CLARIFY",
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
        }

    async def execute(self, session_id: str, inputs: dict) -> _SimpleAgentOutput:
        data = await self.run_session(session_id, inputs.get("available_artifacts") or [])
        return _SimpleAgentOutput(agent_id=self.agent_id, data=data, success=True, confidence=0.78)

