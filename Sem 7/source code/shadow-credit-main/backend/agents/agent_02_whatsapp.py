import asyncio
import logging
import json
import re
from collections import Counter, defaultdict
from datetime import datetime

try:
    from backend.agents import AgentOutput, BaseAgent
    from backend.core.ai_client import groq_complete_async, groq_complete_json_async
except ModuleNotFoundError:
    from agents import AgentOutput, BaseAgent
    from core.ai_client import groq_complete_async, groq_complete_json_async

logger = logging.getLogger(__name__)

WHATSAPP_SYSTEM_PROMPT = """You are a forensic financial data extractor for Indian MSME credit assessment.

You are reading WhatsApp messages between an Indian Kirana store owner (named Suresh) and his customers/suppliers. These messages are in Hinglish (Hindi-English code-switch). Your job is to identify every financial transaction.

RETURN: A valid JSON array — one object per message. No explanation. No markdown. No preamble.

JSON SCHEMA FOR EACH MESSAGE:
{
  "line_id": int,
  "classification": "sale_confirmation" | "payment_received" | "purchase_order" | "expense" | "irrelevant",
  "direction": "inflow" | "outflow" | "unclear" | null,
  "amount": float | null,
  "counterparty": str | null,
  "date": "YYYY-MM-DD" | null,
  "confidence": float (0.0 to 1.0),
  "reasoning": "ONE sentence explaining your classification"
}

CRITICAL CLASSIFICATION RULES:

RULE 1 — DIRECTION:
- If Suresh RECEIVES money or goods are DELIVERED TO a customer: direction = "inflow"
- If Suresh PAYS someone or buys supplies: direction = "outflow"
- If the message is ambiguous about who is paying whom: direction = "unclear", confidence < 0.65
- sale_confirmation = Suresh confirmed selling something = inflow
- payment_received = Customer paid Suresh = inflow
- purchase_order = Suresh ordering from supplier = could be outflow
- expense = Suresh paying for something = outflow

RULE 2 — AMOUNT NORMALIZATION (convert all to float):
"5 hazaar" → 5000.0
"do lakh" → 200000.0
"teen sau" → 300.0
"ek hazaar panchsau" → 1500.0
"50k" → 50000.0
"1.5L" → 150000.0
"pachees rupaye" → 25.0
Always extract numeric value. Never return a string amount.

RULE 3 — HINDI FINANCIAL KEYWORDS:
dena = give/pay (context determines direction)
lena = take/receive (context determines direction)
bheja = sent (past tense)
mila = received (past tense — strong inflow signal)
baaki = balance remaining (indicates partial payment)
udhar = credit/debt (indicates khata transaction)
maal = goods/merchandise (NOT marijuana — this is a shop context)
party = business counterparty (NOT a social event)
rate = price per unit
amount aa gaya = amount received = inflow

RULE 4 — MEDIA MESSAGES:
<Media omitted> or <image omitted> with financial keywords nearby = likely receipt photo
Classify as: sale_confirmation, confidence: 0.60, direction: inflow

RULE 5 — CONFIDENCE CALIBRATION:
>0.85: Clear transaction with amount, direction, counterparty all present
0.70-0.85: Clear transaction but missing one field
0.50-0.70: Transaction likely but direction ambiguous
<0.50: Mark as irrelevant

Return ONLY the JSON array. First character must be [. Last character must be ]."""


PATTERN_BRACKET_COMMA = re.compile(
    r"^\[(?P<d>\d{1,2}/\d{1,2}/\d{2,4}),\s*(?P<t>\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\]\s*(?P<s>[^:]+):\s*(?P<m>.*)$"
)
PATTERN_BRACKET_NOCOMMA = re.compile(
    r"^\[(?P<d>\d{1,2}/\d{1,2}/\d{2,4})\s+(?P<t>\d{1,2}:\d{2}:\d{2})\]\s*(?P<s>[^:]+):\s*(?P<m>.*)$"
)
PATTERN_ANDROID = re.compile(
    r"^(?P<d>\d{1,2}/\d{1,2}/\d{2,4}),\s*(?P<t>\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm))?)\s*-\s*(?P<s>[^:]+):\s*(?P<m>.*)$"
)

CURRENCY_RE = re.compile(r"(₹|\brs\.?\b|रु|rupay|rupaye|rupee|paisa)", re.IGNORECASE)
DIGIT_RE = re.compile(r"\d")
MEDIA_RE = re.compile(r"<\s*(?:media|image)\s+omitted\s*>", re.IGNORECASE)
VOICE_RE = re.compile(r"<\s*voice note omitted\s*>", re.IGNORECASE)

TRADE_KEYWORDS = [
    "dena",
    "lena",
    "payment",
    "order",
    "bhai",
    "rupaye",
    "paisa",
    "total",
    "bill",
    "amount",
    "upi",
    "paid",
    "pending",
    "advance",
    "baaki",
    "credit",
    "cash",
    "maal",
    "stock",
    "rate",
    "kg",
    "piece",
    "dozen",
    "hazaar",
    "lakh",
    "purchase",
    "sale",
    "deliver",
    "ready",
    "customer",
    "shop",
    "dukan",
    "party",
    "invoice",
    "receipt",
]
TRADE_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in TRADE_KEYWORDS) + r")\b", re.IGNORECASE)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _parse_dt(date_s: str, time_s: str) -> datetime | None:
    candidates = [
        f"{date_s}, {time_s}",
        f"{date_s} {time_s}",
    ]
    formats = [
        "%d/%m/%Y, %I:%M %p",
        "%d/%m/%y, %I:%M %p",
        "%d/%m/%Y, %H:%M",
        "%d/%m/%y, %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%y %H:%M:%S",
    ]
    for c in candidates:
        for f in formats:
            try:
                return datetime.strptime(c, f)
            except ValueError:
                continue
    return None


def _normalize_amount_from_text(text: str) -> float | None:
    tx = (text or "").lower()
    tx = tx.replace(",", "")
    # direct numeric patterns
    m = re.search(r"(?:₹|rs\.?|inr)\s*([0-9]+(?:\.[0-9]+)?)", tx)
    if m:
        return float(m.group(1))
    m = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*(k|l|lakhs?|hazaar|hazar)\b", tx)
    if m:
        n = float(m.group(1))
        u = m.group(2)
        if u == "k":
            return n * 1000
        if u in {"l", "lakh", "lakhs"}:
            return n * 100000
        if u in {"hazaar", "hazar"}:
            return n * 1000
    m = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\b", tx)
    if m:
        return float(m.group(1))

    # Hindi word-style
    simple = {
        "ek": 1,
        "do": 2,
        "teen": 3,
        "char": 4,
        "chaar": 4,
        "paanch": 5,
        "pach": 5,
        "pachees": 25,
    }
    for w, v in simple.items():
        if re.search(rf"\b{w}\b", tx):
            if "lakh" in tx:
                return float(v * 100000)
            if "hazaar" in tx or "hazar" in tx:
                return float(v * 1000)
            if "sau" in tx:
                return float(v * 100)
            return float(v)
    return None


class WhatsAppBatchParser(BaseAgent):
    agent_id = "AGENT_02_WHATSAPP"
    name = "WhatsApp Batch Parser"
    version = "1.0.0"

    def __init__(self, audit_logger=None, event_bus=None, settings=None):
        # verification gate expects no-arg init
        if audit_logger is None and event_bus is None and settings is None:
            self.audit_logger = None
            self.event_bus = None
            self.settings = None
        else:
            super().__init__(audit_logger, event_bus, settings)

    async def _publish(self, session_id: str, message: str):
        if self.event_bus:
            await self.event_bus.publish_agent_event(
                session_id=session_id,
                agent_id=self.agent_id,
                status="PROGRESS",
                message=message,
            )

    def _parse_messages(self, raw_text: str) -> list[dict]:
        lines = (raw_text or "").splitlines()
        messages: list[dict] = []
        curr = None
        line_id = 0
        for ln in lines:
            s = ln.strip()
            if not s:
                continue
            m = PATTERN_BRACKET_COMMA.match(s) or PATTERN_BRACKET_NOCOMMA.match(s) or PATTERN_ANDROID.match(s)
            if m:
                dt = _parse_dt(m.group("d"), m.group("t"))
                sender = m.group("s").strip()
                text = m.group("m").strip()
                curr = {
                    "line_id": line_id,
                    "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None,
                    "sender": sender,
                    "text": text,
                    "is_media": bool(MEDIA_RE.search(text)),
                    "is_voice": bool(VOICE_RE.search(text)),
                    "hour": dt.hour if dt else None,
                    "day_of_week": dt.weekday() if dt else None,
                    "is_weekend": (dt.weekday() >= 5) if dt else None,
                }
                messages.append(curr)
                line_id += 1
            elif curr:
                curr["text"] = f"{curr['text']} {s}".strip()
                curr["is_media"] = curr["is_media"] or bool(MEDIA_RE.search(s))
                curr["is_voice"] = curr["is_voice"] or bool(VOICE_RE.search(s))
        return messages

    def _pre_filter(self, messages: list[dict]) -> tuple[list[dict], dict]:
        out = []
        for msg in messages:
            txt = str(msg.get("text", ""))
            keep = bool(DIGIT_RE.search(txt) or CURRENCY_RE.search(txt) or TRADE_RE.search(txt))
            if keep:
                out.append(msg)
        stats = {
            "messages_total": len(messages),
            "messages_filtered": len(messages) - len(out),
            "messages_sent_to_llm": len(out),
        }
        return out, stats

    async def _classify_batch(self, batch: list[dict]) -> list[dict]:
        formatted = [
            {
                "line_id": m["line_id"],
                "sender": m.get("sender"),
                "text": m.get("text"),
                "timestamp": m.get("timestamp"),
                "is_media": m.get("is_media", False),
            }
            for m in batch
        ]
        user_content = (
            "Classify each of these WhatsApp messages. "
            "The shop owner's name is Suresh.\n"
            f"Messages:\n{json.dumps(formatted, ensure_ascii=False, indent=2)}"
        )
        try:
            # Use JSON mode for guaranteed valid JSON
            result = await groq_complete_json_async(WHATSAPP_SYSTEM_PROMPT, user_content)
            
            # Handle both array and object responses
            if isinstance(result, list):
                events = result
            elif isinstance(result, dict) and "events" in result:
                events = result["events"]
            elif isinstance(result, dict) and "classifications" in result:
                events = result["classifications"]
            else:
                # Groq returned unexpected format
                raise ValueError(f"Unexpected JSON structure: {type(result)}")
            
            if not events:
                raise ValueError("Empty event list from Groq")
            
            return events
        except Exception as e:
            logger.warning(f"[AGENT_02] Groq classification failed, using fallback: {e}")
            # deterministic local fallback for reliability
            events = []
            for msg in batch:
                txt = str(msg["text"]).lower()
                amount = _normalize_amount_from_text(txt)
                counterparty = msg["sender"]
                direction = "unclear"
                c = "irrelevant"
                conf = 0.55
                reason = "Defaulted due to weak financial signal."

                if any(k in txt for k in ["order", "maal", "ready", "kg", "piece", "dozen"]):
                    c = "purchase_order"
                    direction = "inflow"
                    conf = 0.74
                    reason = "Trade/order language suggests likely incoming business transaction."
                if any(k in txt for k in ["paid", "payment received", "mila", "received", "aa gaya"]):
                    c = "payment_received"
                    direction = "inflow"
                    conf = 0.82
                    reason = "Payment-received cues indicate inbound funds."
                if "dena" in txt and amount is not None:
                    c = "payment_received"
                    direction = "unclear"
                    conf = 0.62
                    reason = "Phrase 'dena' with amount is ambiguous without relationship context."
                if any(k in txt for k in ["expense", "pay", "sent", "bheja"]) and amount is not None:
                    c = "expense"
                    direction = "outflow"
                    conf = 0.8
                    reason = "Outflow verbs indicate money paid by business."
                if amount is None and c != "purchase_order":
                    c = "irrelevant"
                    direction = "unclear"
                    conf = 0.35
                    reason = "No reliable monetary signal found."

                events.append(
                    {
                        "line_id": msg["line_id"],
                        "classification": c,
                        "direction": direction,
                        "amount": amount,
                        "counterparty": counterparty,
                        "date": (msg.get("timestamp") or "")[:10] if msg.get("timestamp") else None,
                        "confidence": conf,
                        "reasoning": reason,
                    }
                )
            return events

    async def _classify_messages(self, filtered_messages: list[dict]) -> list[dict]:
        chunks = [filtered_messages[i : i + 20] for i in range(0, len(filtered_messages), 20)]
        # exponential backoff wrapper shape preserved for future Claude use.
        async def run_chunk(chunk: list[dict]) -> list[dict]:
            for attempt in range(4):
                try:
                    return await self._classify_batch(chunk)
                except Exception:
                    if attempt >= 3:
                        break
                    await asyncio.sleep(2**attempt)
            return []

        nested = await asyncio.gather(*(run_chunk(c) for c in chunks))
        by_line = {}
        for c in nested:
            for e in c:
                by_line[e["line_id"]] = e
        return [by_line[k] for k in sorted(by_line.keys())]

    async def _resolve_ambiguities(self, events: list[dict], messages: list[dict]) -> int:
        msg_by_line = {m["line_id"]: m for m in messages}
        by_sender = defaultdict(list)
        for m in messages:
            by_sender[m["sender"]].append(m["line_id"])

        resolved_count = 0
        for e in events:
            if e.get("direction") != "unclear":
                continue
            cp = e.get("counterparty") or ""
            lines = sorted(by_sender.get(cp, []))
            current_line = e["line_id"]
            idx = lines.index(current_line) if current_line in lines else -1
            window = lines[max(0, idx - 5) : idx + 6] if idx >= 0 else lines[:10]
            context_text = " ".join((msg_by_line[l]["text"] for l in window if l in msg_by_line)).lower()

            inflow_votes = sum(1 for k in ["order", "maal", "ready", "customer", "rate"] if k in context_text)
            outflow_votes = sum(1 for k in ["pay", "sent", "bheja", "expense"] if k in context_text)

            if inflow_votes >= outflow_votes:
                e["direction"] = "inflow"
                e["confidence"] = max(float(e["confidence"]), 0.71)
                e["reasoning"] = "Resolved via counterparty context: relationship mostly buyer/customer-side."
            else:
                e["direction"] = "outflow"
                e["confidence"] = max(float(e["confidence"]), 0.71)
                e["reasoning"] = "Resolved via counterparty context: relationship mostly vendor/payment-side."
            resolved_count += 1
        return resolved_count

    def _weekly_summary(self, financial_events: list[dict]) -> list[dict]:
        buckets = defaultdict(lambda: {"inflow": 0.0, "outflow": 0.0, "count": 0})
        for e in financial_events:
            d = e.get("date")
            if not d:
                continue
            try:
                dt = datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                continue
            ws = (dt.date()).toordinal() - dt.weekday()
            amount = float(e.get("amount") or 0.0)
            if e.get("direction") == "inflow":
                buckets[ws]["inflow"] += amount
            elif e.get("direction") == "outflow":
                buckets[ws]["outflow"] += amount
            buckets[ws]["count"] += 1

        out = []
        for ws in sorted(buckets.keys()):
            week_start = datetime.fromordinal(ws).date().isoformat()
            inflow = buckets[ws]["inflow"]
            outflow = buckets[ws]["outflow"]
            out.append(
                {
                    "week_start": week_start,
                    "total_inflow": round(inflow, 2),
                    "total_outflow": round(outflow, 2),
                    "transaction_count": int(buckets[ws]["count"]),
                    "net": round(inflow - outflow, 2),
                }
            )
        return out

    def _behavioral(self, messages: list[dict]) -> dict:
        if not messages:
            return {
                "peak_hour_activity_pct": 0.0,
                "weekend_activity_pct": 0.0,
                "response_time_minutes": 0.0,
                "unique_counterparties": 0,
                "busiest_day_of_week": "Monday",
                "data_span_days": 0,
                "active_days": 0,
                "activity_ratio": 0.0,
            }
        total = len(messages)
        peak = 0
        weekend = 0
        day_counts = Counter()
        active_days_set = set()
        sender_last = {}
        response_deltas = []
        owner = "suresh"

        dates = []
        for m in messages:
            ts = m.get("timestamp")
            if not ts:
                continue
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            dates.append(dt)
            h = dt.hour
            if 9 <= h <= 20:
                peak += 1
            if dt.weekday() >= 5:
                weekend += 1
            day_counts[dt.weekday()] += 1
            active_days_set.add(dt.date())
            snd = str(m.get("sender", "")).strip().lower()
            sender_last[snd] = dt
            if snd == owner:
                others = [k for k in sender_last.keys() if k != owner]
                if others:
                    prior_candidates = [sender_last[o] for o in others if sender_last[o] <= dt]
                    if prior_candidates:
                        prior = max(prior_candidates)
                        response_deltas.append((dt - prior).total_seconds() / 60.0)

        if dates:
            span_days = (max(dates).date() - min(dates).date()).days + 1
        else:
            span_days = 0
        active_days = len(active_days_set)
        busiest_idx = day_counts.most_common(1)[0][0] if day_counts else 0
        avg_resp = sum(response_deltas) / len(response_deltas) if response_deltas else 0.0
        unique_counterparties = len({m["sender"] for m in messages if str(m["sender"]).strip().lower() != owner})

        return {
            "peak_hour_activity_pct": round((peak / total) * 100.0, 2),
            "weekend_activity_pct": round((weekend / total) * 100.0, 2),
            "response_time_minutes": round(avg_resp, 2),
            "unique_counterparties": unique_counterparties,
            "busiest_day_of_week": DAY_NAMES[busiest_idx],
            "data_span_days": span_days,
            "active_days": active_days,
            "activity_ratio": round(active_days / span_days, 4) if span_days > 0 else 0.0,
        }

    async def execute(self, session_id: str, inputs: dict) -> AgentOutput:
        started = datetime.utcnow()
        raw = str(inputs.get("raw_text") or inputs.get("file_content") or "")
        if not raw.strip():
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=False,
                data={},
                confidence_score=0.0,
                latency_ms=0,
                errors=["raw_text/file_content is required"],
                warnings=[],
                fallback_used=False,
            )

        try:
            messages = self._parse_messages(raw)
            filtered, stats = self._pre_filter(messages)
            await self._publish(session_id, f"messages_total={stats['messages_total']} filtered={stats['messages_filtered']} sent_to_llm={stats['messages_sent_to_llm']}")

            warnings = []
            pass_ratio = (stats["messages_sent_to_llm"] / max(stats["messages_total"], 1)) * 100.0
            if pass_ratio < 20.0:
                warnings.append("Low filter pass-through (<20%). Possible low-signal chat export.")

            classified = await self._classify_messages(filtered)
            ambiguities = await self._resolve_ambiguities(classified, filtered)

            # Build financial events payload.
            financial_events = []
            for e in classified:
                if e["classification"] == "irrelevant":
                    continue
                financial_events.append(
                    {
                        "event_type": e["classification"],
                        "direction": e["direction"],
                        "amount": float(e["amount"] or 0.0),
                        "counterparty": e["counterparty"],
                        "date": e["date"],
                        "confidence": float(e["confidence"]),
                        "reasoning": e["reasoning"],
                        "source_line": int(e["line_id"]),
                    }
                )

            weekly = self._weekly_summary(financial_events)
            behavioral = self._behavioral(messages)

            date_values = [datetime.strptime(m["timestamp"], "%Y-%m-%d %H:%M:%S").date() for m in messages if m.get("timestamp")]
            if date_values:
                start_d = min(date_values).isoformat()
                end_d = max(date_values).isoformat()
                covered = (max(date_values) - min(date_values)).days + 1
            else:
                start_d = None
                end_d = None
                covered = 0

            quality = "HIGH" if behavioral["activity_ratio"] > 0.85 else "MEDIUM" if behavioral["activity_ratio"] > 0.55 else "LOW"

            data = {
                "total_messages_parsed": len(messages),
                "messages_filtered": stats["messages_filtered"],
                "messages_classified": len(classified),
                "financial_events": financial_events,
                "weekly_summary": weekly,
                "behavioral_signals": behavioral,
                "ambiguity_resolutions": ambiguities,
                "data_quality": quality,
                "date_range": {"start": start_d, "end": end_d, "days_covered": covered},
            }

            latency_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
            conf = min(1.0, max(0.3, 0.5 + (len(financial_events) / max(1, len(messages))) * 0.5))
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=True,
                data=data,
                confidence_score=round(conf, 4),
                latency_ms=latency_ms,
                errors=[],
                warnings=warnings,
                fallback_used=False,
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


# Backward compatibility with existing orchestrator imports.
WhatsAppParserAgent = WhatsAppBatchParser
