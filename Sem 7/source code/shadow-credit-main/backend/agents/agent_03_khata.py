import re
import io
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

try:
    from backend.agents import BaseAgent, AgentOutput
    from backend.db.database import get_db, execute_write
    from backend.config import get_settings
except ModuleNotFoundError:
    from agents import BaseAgent, AgentOutput
    from db.database import get_db, execute_write
    from config import get_settings

logger = logging.getLogger(__name__)


OKCREDIT_REQUIRED_COLS = {"date", "type", "amount", "party name"}
OKCREDIT_OPTIONAL_COLS = {"note", "running balance", "balance"}

KHATABOOK_REQUIRED_COLS = {"date", "customer name"}
KHATABOOK_AMOUNT_COLS = {
    "credit (you gave)", "debit (you received)",
    "credit (you'll get)", "debit (you gave)",
    "credit", "debit"
}

AMOUNT_CLEAN_PATTERN = re.compile(r"[₹,\s]|Rs\.?\s*|INR\s*|/-$")

DATE_FORMATS = [
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d/%m/%y",
    "%d-%m-%y",
    "%d %b %Y",
    "%d %B %Y",
    "%Y-%m-%d",
    "%b %d, %Y",
    "%d/%b/%Y",
    "%d %b %y",
    "%B %d, %Y",
]

SEASONALITY_THRESHOLD = 2.5


def _clean_headers(df: pd.DataFrame) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key:
            cleaned[key] = col
    return cleaned


def _parse_amount(value) -> float:
    if pd.isna(value):
        return 0.0
    raw = str(value).strip()
    if not raw:
        return 0.0
    cleaned = AMOUNT_CLEAN_PATTERN.sub("", raw).strip()
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        logger.warning("Amount parse failed for value=%s; defaulting to 0.0", raw)
        return 0.0


def _parse_date_series(series: pd.Series) -> pd.Series:
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    source = series.astype(str).str.strip()
    for fmt in DATE_FORMATS:
        mask = parsed.isna()
        if not mask.any():
            break
        trial = pd.to_datetime(source[mask], format=fmt, errors="coerce")
        parsed.loc[mask] = trial
    return parsed


def detect_encoding_and_read(file_content_bytes: bytes) -> tuple[str, str]:
    """
    Detects encoding of raw CSV bytes and returns decoded string + encoding name.
    """
    encodings = [
        ("utf-8-sig", "utf-8-sig"),
        ("utf-8", "utf-8"),
        ("utf-16", "utf-16"),
        ("latin-1", "latin-1"),
    ]
    for codec, label in encodings:
        try:
            return file_content_bytes.decode(codec), label
        except UnicodeDecodeError:
            continue

    logger.warning("CSV encoding detection fell back to replace mode")
    return file_content_bytes.decode("utf-8", errors="replace"), "utf-8-replaced"


def detect_format_and_normalize(raw_csv: str) -> tuple[str, pd.DataFrame]:
    """
    Auto-detects whether this CSV is OkCredit, Khatabook, or Unknown.
    """
    try:
        df = pd.read_csv(io.StringIO(raw_csv), sep=",")
    except Exception as exc:
        raise KhataParseError(f"Cannot parse CSV: {exc}") from exc

    if len(df.columns) < 3:
        try:
            df = pd.read_csv(io.StringIO(raw_csv), sep="\t")
        except Exception as exc:
            raise KhataParseError(f"Cannot parse CSV: {exc}") from exc

    if len(df.columns) < 3:
        raise KhataParseError(
            "Cannot parse CSV: fewer than 3 columns detected. Verify file is a valid CSV export."
        )

    cleaned_headers = _clean_headers(df)
    cleaned_keys = set(cleaned_headers.keys())

    fmt = None
    if OKCREDIT_REQUIRED_COLS.issubset(cleaned_keys):
        fmt = "okcredit"
    elif KHATABOOK_REQUIRED_COLS.issubset(cleaned_keys) and any(c in cleaned_keys for c in KHATABOOK_AMOUNT_COLS):
        fmt = "khatabook"
    elif "type" in cleaned_keys:
        type_col = cleaned_headers["type"]
        type_vals = set(df[type_col].astype(str).str.strip().str.lower().dropna().tolist())
        if {"credit", "debit"} & type_vals:
            fmt = "okcredit_variant"
    elif "credit" in cleaned_keys and "debit" in cleaned_keys:
        fmt = "khatabook_minimal"

    if fmt is None:
        raise KhataParseError(
            f"Unrecognized CSV format. Headers found: {list(df.columns)}. "
            "Expected OkCredit (Date, Type, Amount, Party Name) or "
            "Khatabook (Date, Customer Name, Credit, Debit) format."
        )

    norm = pd.DataFrame(index=df.index)

    if fmt in {"okcredit", "okcredit_variant"}:
        date_col = cleaned_headers.get("date")
        type_col = cleaned_headers.get("type")
        amount_col = cleaned_headers.get("amount")
        party_col = cleaned_headers.get("party name") or cleaned_headers.get("customer name")
        note_col = cleaned_headers.get("note")
        rb_col = cleaned_headers.get("running balance") or cleaned_headers.get("balance")

        types = df[type_col].astype(str).str.strip().str.lower() if type_col else pd.Series("", index=df.index)
        amounts = df[amount_col].map(_parse_amount) if amount_col else pd.Series(0.0, index=df.index)

        norm["amount_given"] = np.where(types == "credit", amounts, 0.0).astype(float)
        norm["amount_received"] = np.where(types == "debit", amounts, 0.0).astype(float)
        norm["party_name"] = df[party_col].astype(str).str.strip() if party_col else "Unknown"
        norm["notes"] = df[note_col].astype(str).fillna("").str.strip() if note_col else ""
        norm["running_balance"] = df[rb_col].map(_parse_amount) if rb_col else 0.0
        norm["source_format"] = fmt
        date_series = df[date_col] if date_col else pd.Series("", index=df.index)
    else:
        date_col = cleaned_headers.get("date")
        party_col = cleaned_headers.get("customer name") or cleaned_headers.get("party name")

        credit_col = (
            cleaned_headers.get("credit (you gave)")
            or cleaned_headers.get("credit (you'll get)")
            or cleaned_headers.get("credit")
        )
        debit_col = (
            cleaned_headers.get("debit (you received)")
            or cleaned_headers.get("debit (you gave)")
            or cleaned_headers.get("debit")
        )
        rb_col = cleaned_headers.get("running balance") or cleaned_headers.get("balance")
        note_col = cleaned_headers.get("notes") or cleaned_headers.get("note")

        norm["amount_given"] = df[credit_col].map(_parse_amount) if credit_col else 0.0
        norm["amount_received"] = df[debit_col].map(_parse_amount) if debit_col else 0.0
        norm["party_name"] = df[party_col].astype(str).str.strip() if party_col else "Unknown"
        norm["notes"] = df[note_col].astype(str).fillna("").str.strip() if note_col else ""
        norm["running_balance"] = df[rb_col].map(_parse_amount) if rb_col else 0.0
        norm["source_format"] = fmt
        date_series = df[date_col] if date_col else pd.Series("", index=df.index)

    norm["date"] = _parse_date_series(date_series)
    bad_dates = int(norm["date"].isna().sum())
    if bad_dates > 0:
        logger.warning("Dropping %d rows with unparseable dates", bad_dates)
    norm = norm.dropna(subset=["date"]).copy()

    norm["amount_received"] = pd.to_numeric(norm["amount_received"], errors="coerce").fillna(0.0).astype(float)
    norm["amount_given"] = pd.to_numeric(norm["amount_given"], errors="coerce").fillna(0.0).astype(float)
    norm["running_balance"] = pd.to_numeric(norm["running_balance"], errors="coerce").fillna(0.0).astype(float)
    norm["net"] = (norm["amount_received"] - norm["amount_given"]).astype(float)
    norm["party_name"] = norm["party_name"].astype(str).replace("nan", "Unknown").fillna("Unknown")
    norm["notes"] = norm["notes"].astype(str).replace("nan", "").fillna("")

    norm = norm.sort_values("date").reset_index(drop=True)

    if len(norm) == 0:
        raise KhataParseError(
            "No valid transactions found after parsing. Verify the CSV contains transaction data."
        )
    if len(norm) < 3:
        logger.warning("Very low transaction count after parsing: %d rows", len(norm))

    cols = [
        "date", "amount_received", "amount_given", "net",
        "party_name", "notes", "running_balance", "source_format",
    ]
    return fmt, norm[cols]


def compute_90day_metrics(df: pd.DataFrame) -> dict:
    """
    Computes financial metrics needed for credit assessment.
    """
    if df.empty:
        raise KhataParseError("No transactions provided for metric computation.")

    df_work = df.copy()
    df_work["date"] = pd.to_datetime(df_work["date"], errors="coerce")
    df_work = df_work.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if df_work.empty:
        raise KhataParseError("No valid dated transactions available for metric computation.")

    ref_date = df_work["date"].max()
    window_start = ref_date - timedelta(days=90)
    df_90 = df_work[df_work["date"] >= window_start].copy()

    if len(df_90) < 3:
        df_90 = df_work.copy()
        full_90_days = False
        actual_days = max(0, int((df_work["date"].max() - df_work["date"].min()).days))
    else:
        full_90_days = True
        actual_days = 90

    period_start = df_90["date"].min()
    period_end = df_90["date"].max()

    total_received_90d = float(df_90["amount_received"].sum())
    total_given_90d = float(df_90["amount_given"].sum())

    df_90["month"] = df_90["date"].dt.to_period("M")
    monthly_group = df_90.groupby("month")["amount_received"].sum()
    monthly_series = {str(k): float(v) for k, v in monthly_group.to_dict().items()}
    monthly_values = list(monthly_series.values()) or [0.0]

    median_monthly_received = float(np.median(monthly_values))
    mean_monthly_received = float(np.mean(monthly_values))

    inflow_by_party = df_90.groupby("party_name")["amount_received"].sum().sort_values(ascending=False)
    customer_positive = inflow_by_party[inflow_by_party > 0]
    unique_customers = int(customer_positive.index.nunique())

    if not inflow_by_party.empty:
        top_customer_name = str(inflow_by_party.index[0])
        top_customer_amount = float(inflow_by_party.iloc[0])
    else:
        top_customer_name = ""
        top_customer_amount = 0.0

    top_customer_pct = float(top_customer_amount / total_received_90d) if total_received_90d > 0 else 0.0
    top_customer_pct = max(0.0, min(1.0, top_customer_pct))

    customer_breakdown = []
    for name, val in inflow_by_party.head(10).items():
        pct = float(val / total_received_90d) if total_received_90d > 0 else 0.0
        customer_breakdown.append(
            {"name": str(name), "total": float(val), "pct": max(0.0, min(1.0, pct))}
        )

    outstanding_estimate = float(max(0.0, total_given_90d - (total_received_90d * 0.7)))
    recovery_rate = float(min(1.0, total_received_90d / total_given_90d)) if total_given_90d > 0 else 1.0
    logger.info("Outstanding estimate computed with conservative approximation formula")

    df_90["year_week"] = df_90["date"].dt.strftime("%G-W%V")
    weekly_group = df_90.groupby("year_week")["amount_received"].sum()
    weekly_series = {str(k): float(v) for k, v in weekly_group.to_dict().items()}

    active_weeks = int(df_90["year_week"].nunique())
    total_weeks = max(1, int(actual_days // 7))
    activity_rate = float(min(1.0, active_weeks / total_weeks))

    sorted_dates = df_90["date"].sort_values().to_list()
    if len(sorted_dates) >= 2:
        diffs = [(sorted_dates[i] - sorted_dates[i - 1]).days for i in range(1, len(sorted_dates))]
        longest_gap_days = int(max(diffs)) if diffs else 0
    else:
        longest_gap_days = 0

    transactions_per_week_avg = float(len(df_90) / max(1, total_weeks))

    if len(monthly_values) >= 2:
        mean_val = float(np.mean(monthly_values))
        if mean_val == 0:
            income_regularity_score = 0.0
        else:
            cov = float(np.std(monthly_values) / mean_val)
            income_regularity_score = float(max(0.0, min(1.0, 1.0 - cov)))
    else:
        income_regularity_score = 0.5

    seasonal_detected = False
    peak_month: Optional[str] = None
    trough_month: Optional[str] = None
    peak_to_trough_ratio = 1.0

    if len(monthly_series) >= 3:
        max_month_val = max(monthly_series.values()) if monthly_series else 0.0
        min_month_val = min(monthly_series.values()) if monthly_series else 0.0
        if min_month_val > 0:
            peak_to_trough_ratio = float(max_month_val / min_month_val)
        else:
            peak_to_trough_ratio = float(max_month_val / 1.0)
        if peak_to_trough_ratio >= SEASONALITY_THRESHOLD:
            seasonal_detected = True
            peak_month = max(monthly_series, key=monthly_series.get)
            trough_month = min(monthly_series, key=monthly_series.get)

    monthly_vs_average = {}
    if mean_monthly_received > 0:
        for month, val in monthly_series.items():
            monthly_vs_average[month] = round(float(val / mean_monthly_received), 2)

    first_period = period_start.to_period("M")
    last_period = period_end.to_period("M")
    full_range = pd.period_range(start=first_period, end=last_period, freq="M")
    missing_months = [str(p) for p in full_range if str(p) not in monthly_series]

    source_format = str(df_90["source_format"].iloc[0]) if "source_format" in df_90.columns and len(df_90) else "unknown"

    # Behavioral signals for downstream warmth scoring.
    credit_rows = df_90[df_90["amount_given"] > 0].copy()
    debit_rows = df_90[df_90["amount_received"] > 0].copy()

    credit_parties = set(credit_rows["party_name"].astype(str).tolist())
    collected_parties = set(debit_rows["party_name"].astype(str).tolist())
    if credit_parties:
        payment_collection_rate = (len(credit_parties & collected_parties) / len(credit_parties)) * 100.0
    else:
        payment_collection_rate = 0.0

    collection_deltas: list[int] = []
    if not credit_rows.empty and not debit_rows.empty:
        debit_by_party = {
            party: sorted(group["date"].tolist())
            for party, group in debit_rows.groupby("party_name")
        }
        for _, row in credit_rows.iterrows():
            party = str(row["party_name"])
            credit_date = row["date"]
            candidates = [d for d in debit_by_party.get(party, []) if d >= credit_date]
            if candidates:
                collection_deltas.append(int((candidates[0] - credit_date).days))
    avg_days_to_collect = float(sum(collection_deltas) / len(collection_deltas)) if collection_deltas else 0.0

    return {
        "period": {
            "start": period_start.strftime("%Y-%m-%d"),
            "end": period_end.strftime("%Y-%m-%d"),
            "days_actual": int(max(0, (period_end - period_start).days)),
            "full_90_days": bool(full_90_days),
        },
        "inflow_metrics": {
            "total_received_90d": float(total_received_90d),
            "median_monthly_received": float(median_monthly_received),
            "mean_monthly_received": float(mean_monthly_received),
            "income_regularity_score": float(max(0.0, min(1.0, income_regularity_score))),
            "monthly_series": monthly_series,
            "weekly_series": weekly_series,
        },
        "monthly_inflow_series": monthly_series,
        "customer_metrics": {
            "unique_customers": int(unique_customers),
            "top_customer_name": top_customer_name,
            "top_customer_amount": float(top_customer_amount),
            "top_customer_pct": float(top_customer_pct),
            "customer_breakdown": customer_breakdown,
        },
        "receivables_metrics": {
            "total_given_90d": float(total_given_90d),
            "recovery_rate": float(max(0.0, min(1.0, recovery_rate))),
            "outstanding_estimate": float(outstanding_estimate),
            "is_estimate": True,
        },
        "regularity_metrics": {
            "active_weeks": int(active_weeks),
            "total_weeks": int(total_weeks),
            "activity_rate": float(max(0.0, min(1.0, activity_rate))),
            "longest_gap_days": int(longest_gap_days),
            "transactions_per_week_avg": float(max(0.0, transactions_per_week_avg)),
        },
        "seasonal_analysis": {
            "seasonal_detected": bool(seasonal_detected),
            "peak_month": peak_month,
            "trough_month": trough_month,
            "peak_to_trough_ratio": float(max(0.0, peak_to_trough_ratio)),
            "monthly_vs_average": monthly_vs_average,
        },
        "data_quality": {
            "confidence_score": 0.92,
            "source_type": "STRUCTURED",
            "source_format": source_format,
            "total_transactions": int(len(df_work)),
            "transactions_90d": int(len(df_90)),
            "date_range_days": int(max(0, (df_work["date"].max() - df_work["date"].min()).days)),
            "missing_months": missing_months,
        },
        "behavioral_signals": {
            "payment_collection_rate": round(float(max(0.0, min(100.0, payment_collection_rate))), 2),
            "avg_days_to_collect": round(float(max(0.0, avg_days_to_collect)), 2),
        },
    }


def build_key_extractions(metrics: dict, artifact_id: str) -> list[dict]:
    """
    Builds extraction records to insert into extractions table.
    """
    inflow = metrics["inflow_metrics"]
    customer = metrics["customer_metrics"]
    regularity = metrics["regularity_metrics"]
    seasonal = metrics["seasonal_analysis"]
    quality = metrics["data_quality"]
    period = metrics["period"]

    median_val = float(inflow.get("median_monthly_received", 0.0))
    total_inflow = float(inflow.get("total_received_90d", 0.0))
    days = int(period.get("days_actual", 0))
    unique_customers = int(customer.get("unique_customers", 0))
    top_pct = float(customer.get("top_customer_pct", 0.0))
    top_name = str(customer.get("top_customer_name", "")) or "N/A"
    reg_score = float(inflow.get("income_regularity_score", 0.0))
    active = int(regularity.get("active_weeks", 0))
    total = int(regularity.get("total_weeks", 1))
    seasonal_detected = bool(seasonal.get("seasonal_detected", False))
    seasonal_ratio = float(seasonal.get("peak_to_trough_ratio", 1.0))
    format_name = str(quality.get("source_format", "unknown"))

    rows = [
        ("median_monthly_inflow", f"₹{median_val:,.0f}/month (90-day median)", str(float(median_val))),
        ("total_inflow_90d", f"₹{total_inflow:,.0f} received in {days} days", str(float(total_inflow))),
        ("unique_customers", f"{unique_customers} unique customers", str(int(unique_customers))),
        ("top_customer_pct", f"{top_pct:.1%} revenue from {top_name}", str(float(max(0.0, min(1.0, top_pct))))),
        ("income_regularity_score", f"{reg_score:.2f}/1.0 regularity score (CoV method)", str(float(max(0.0, min(1.0, reg_score))))),
        ("activity_rate", f"{active}/{total} weeks active", str(float(max(0.0, min(1.0, regularity.get('activity_rate', 0.0)))))),
        ("seasonal_detected", f"Seasonal: {seasonal_detected} (peak/trough ratio: {seasonal_ratio:.1f}x)", "true" if seasonal_detected else "false"),
        ("source_format", f"CSV format: {format_name}", format_name),
    ]

    extractions = []
    for field_name, raw_value, normalized in rows:
        extractions.append(
            {
                "id": str(uuid.uuid4()),
                "artifact_id": artifact_id,
                "field_name": field_name,
                "raw_value": raw_value,
                "normalized_value": normalized,
                "confidence_score": 0.92,
                "extraction_method": "CSV_PARSE",
                "flagged": 0,
            }
        )
    return extractions


class KhataBookAgent(BaseAgent):
    agent_id = "AGENT_03_KHATA"
    name = "Khata Book Agent"
    version = "1.0.0"

    async def execute(self, session_id: str, inputs: dict) -> AgentOutput:
        """
        Parses structured ledger CSV and writes key metrics.
        """
        file_content = inputs.get("file_content")
        file_path = str(inputs.get("file_path", "") or "")
        artifact_id = str(inputs.get("artifact_id", "") or "")

        if not file_content:
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=False,
                data={},
                confidence_score=0.0,
                latency_ms=0,
                errors=["No file_content provided to KhataBookAgent"],
                warnings=[],
                fallback_used=False,
            )

        if isinstance(file_content, bytes):
            file_str, encoding = detect_encoding_and_read(file_content)
        else:
            file_str = str(file_content)
            encoding = "utf-8 (pre-decoded)"

        try:
            source_format, df = detect_format_and_normalize(file_str)
        except KhataParseError as exc:
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=False,
                data={"hint": "Provide OkCredit or Khatabook CSV export"},
                confidence_score=0.0,
                latency_ms=0,
                errors=[str(exc)],
                warnings=[],
                fallback_used=False,
            )

        await self.event_bus.publish_agent_event(
            session_id=session_id,
            agent_id=self.agent_id,
            status="PROGRESS",
            message=(
                f"Detected {source_format} format — {len(df)} transactions loaded "
                f"(encoding: {encoding})"
            ),
            data={"file_path": file_path},
        )

        metrics = compute_90day_metrics(df)
        metrics["data_quality"]["source_format"] = source_format

        await self.event_bus.publish_agent_event(
            session_id=session_id,
            agent_id=self.agent_id,
            status="PROGRESS",
            message=(
                f"90-day analysis complete — median monthly: "
                f"₹{metrics['inflow_metrics']['median_monthly_received']:,.0f}, "
                f"{metrics['customer_metrics']['unique_customers']} customers, "
                f"activity rate: {metrics['regularity_metrics']['activity_rate']:.0%}, "
                f"seasonal: {metrics['seasonal_analysis']['seasonal_detected']}"
            ),
        )

        extractions = build_key_extractions(metrics, artifact_id)

        async with get_db() as db:
            await execute_write(
                db,
                """UPDATE artifacts SET ocr_confidence = ?, extracted_at = ?,
                   processing_status = ? WHERE id = ?""",
                (0.92, datetime.utcnow().isoformat() + "Z", "COMPLETE", artifact_id),
            )

            for ext in extractions:
                await execute_write(
                    db,
                    """INSERT INTO extractions (id, artifact_id, field_name,
                       raw_value, normalized_value, confidence_score,
                       extraction_method, flagged)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        ext["id"],
                        ext["artifact_id"],
                        ext["field_name"],
                        ext["raw_value"],
                        ext["normalized_value"],
                        ext["confidence_score"],
                        ext["extraction_method"],
                        ext["flagged"],
                    ),
                )

        await self.event_bus.publish_agent_event(
            session_id=session_id,
            agent_id=self.agent_id,
            status="PROGRESS",
            message=(
                f"Khata data written — {len(extractions)} extractions stored "
                "in audit database"
            ),
        )

        return AgentOutput(
            agent_id=self.agent_id,
            agent_name=self.name,
            session_id=session_id,
            success=True,
            confidence_score=0.92,
            latency_ms=0,
            data=metrics,
            errors=[],
            warnings=[],
            fallback_used=False,
        )


class KhataParseError(Exception):
    """
    Raised when CSV cannot be parsed into a usable dataframe.
    """

    pass
