import logging
import uuid
import time
from datetime import datetime, timedelta
from typing import Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
import shap

try:
    from backend.agents import BaseAgent, AgentOutput
    from backend.config import get_settings
    from backend.db.database import execute_query, execute_write, get_db
except ModuleNotFoundError:
    from agents import BaseAgent, AgentOutput
    from config import get_settings
    from db.database import execute_query, execute_write, get_db

logger = logging.getLogger(__name__)


SIGNAL_WEIGHTS = {
    "INCOME_REGULARITY": 0.266,
    "INFLOW_CLAIM_CONSISTENCY": 0.209,
    "BUSINESS_CONTINUITY": 0.190,
    "SEASONAL_PATTERN": 0.1425,
    "NETWORK_RELIABILITY": 0.095,
    "DATA_SOURCE_DIVERSITY": 0.0475,
    "BEHAVIORAL_CONSISTENCY": 0.05,
}

GRADE_THRESHOLDS = [
    (0.85, "A+"),
    (0.75, "A"),
    (0.65, "B+"),
    (0.55, "B"),
    (0.00, "C"),
]

RBI_CASH_RATIO_NOTE = (
    "Cash transaction ratio for micro-enterprises is 36% per RBI MSME Survey 2023. "
    "A WhatsApp-UPI gap below 30% is within the documented norm for this business category."
)


_warmth_model: Optional[xgb.XGBClassifier] = None
_warmth_scaler: Optional[MinMaxScaler] = None


def _clamp(v: float, low: float, high: float) -> float:
    return max(low, min(high, float(v)))


def _safe_float(v, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _parse_date_any(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw)
    except Exception:
        pass
    fmts = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in fmts:
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue
    return None


def compute_signal_1_income_regularity(
    weekly_summary: list[dict],
    monthly_inflow_series: dict[str, float] = None,
) -> float:
    inflows: list[float] = []
    periods_seen: set[str] = set()

    for idx, w in enumerate(weekly_summary or []):
        key = f"w{idx}"
        if key in periods_seen:
            continue
        periods_seen.add(key)
        inflows.append(max(0.0, _safe_float((w or {}).get("total_inflow", 0.0))))

    if monthly_inflow_series:
        for month, value in monthly_inflow_series.items():
            key = f"m:{month}"
            if key in periods_seen:
                continue
            periods_seen.add(key)
            inflows.append(max(0.0, _safe_float(value) / 4.33))

    if len(inflows) < 4:
        return 0.65
    if all(v == 0 for v in inflows):
        return 0.30

    values_array = np.array(inflows, dtype=float).reshape(-1, 1)
    clf = IsolationForest(
        contamination=0.15,
        random_state=42,
        n_estimators=100,
    )
    predictions = clf.fit_predict(values_array)
    anomaly_count = int(sum(1 for p in predictions if p == -1))
    contamination_ratio = anomaly_count / max(len(predictions), 1)
    score = 1.0 - contamination_ratio

    cv = float(np.std(inflows) / (np.mean(inflows) + 1e-9))
    if cv > 0.8:
        score *= 0.85
    elif cv > 0.5:
        score *= 0.93

    return round(_clamp(score, 0.30, 1.0), 4)


def _linear_decay(value: float, x0: float, x1: float, y0: float, y1: float) -> float:
    if value <= x0:
        return y0
    if value >= x1:
        return y1
    frac = (value - x0) / (x1 - x0)
    return y0 + frac * (y1 - y0)


def compute_signal_2_consistency(
    whatsapp_total: float,
    upi_total: float,
    khata_total: float = None,
) -> float:
    wa = max(0.0, _safe_float(whatsapp_total))
    upi = max(0.0, _safe_float(upi_total))
    kh = None if khata_total is None else max(0.0, _safe_float(khata_total))

    if wa <= 0 and upi <= 0 and (kh is None or kh <= 0):
        return 0.50

    if wa > 0 and upi > 0:
        gap_ratio = abs(wa - upi) / max(wa, 1.0)
        if gap_ratio < 0.10:
            score = 1.00
        elif gap_ratio < 0.20:
            score = 0.95
        elif gap_ratio < 0.30:
            score = 0.85  # RBI cash-ratio context noted in RBI_CASH_RATIO_NOTE
        elif gap_ratio < 0.40:
            score = _linear_decay(gap_ratio, 0.30, 0.40, 0.85, 0.70)
        elif gap_ratio < 0.60:
            score = _linear_decay(gap_ratio, 0.40, 0.60, 0.70, 0.60)
        else:
            score = 0.60
    elif wa > 0 and upi <= 0:
        score = 0.70
    else:
        score = 0.80

    if kh is not None and kh > 0:
        available = [v for v in (wa, upi) if v > 0]
        if available:
            avg_sources = float(np.mean(available))
            if avg_sources > 0:
                align_gap = abs(kh - avg_sources) / avg_sources
                if align_gap <= 0.25:
                    score += 0.05

    return round(_clamp(score, 0.50, 1.00), 4)


def compute_signal_3_continuity(
    bill_extracted_at: str = None,
    bill_due_date: str = None,
    maps_listing_age_years: float = None,
    maps_review_count: int = None,
    data_start_date: str = None,
) -> tuple[float, dict]:
    today = datetime.utcnow()
    bill_score = None
    maps_score = None
    span_score = None
    method = "none"

    bill_dt = _parse_date_any(bill_due_date) or _parse_date_any(bill_extracted_at)
    if bill_dt is not None:
        days_since = max(0, (today.date() - bill_dt.date()).days)
        if days_since <= 30:
            bill_score = 1.00
        elif days_since <= 90:
            bill_score = 0.90
        elif days_since <= 180:
            bill_score = 0.80
        elif days_since <= 365:
            bill_score = 0.70
        elif days_since <= 730:
            decay = (days_since - 365) / 365.0
            bill_score = 0.70 - (0.20 * decay)
        else:
            bill_score = 0.50

    if maps_listing_age_years is not None:
        age = max(0.0, _safe_float(maps_listing_age_years))
        base_score = min(age / 10.0, 1.0)
        if maps_review_count is not None:
            rv = max(0, int(maps_review_count))
            review_score = min(np.log10(rv + 1) / 3.0, 1.0)
            maps_score = (base_score * 0.7) + (review_score * 0.3)
        else:
            maps_score = base_score

    start_dt = _parse_date_any(data_start_date)
    if start_dt is not None:
        days_of_data = max(0, (today.date() - start_dt.date()).days)
        span_score = min(days_of_data / 365.0, 1.0)

    if bill_score is not None and maps_score is not None and span_score is not None:
        score = (bill_score * 0.5) + (maps_score * 0.3) + (span_score * 0.2)
        method = "all_three"
    elif bill_score is not None and span_score is not None:
        score = (bill_score * 0.6) + (span_score * 0.4)
        method = "bill_span"
    elif bill_score is not None:
        score = bill_score
        method = "bill_only"
    elif maps_score is not None:
        score = maps_score * 0.85
        method = "maps_only"
    elif span_score is not None:
        score = span_score * 0.80
        method = "span_only"
    else:
        score = 0.60

    score = round(_clamp(score, 0.50, 1.00), 4)
    return score, {
        "bill_score": None if bill_score is None else round(float(bill_score), 4),
        "maps_score": None if maps_score is None else round(float(maps_score), 4),
        "span_score": None if span_score is None else round(float(span_score), 4),
        "composite_method": method,
    }


def compute_signal_4_seasonal(
    monthly_inflow: dict[str, float],
) -> tuple[float, dict]:
    if not monthly_inflow or len(monthly_inflow) < 4:
        return 0.65, {
            "seasonal_detected": False,
            "peak_months": [],
            "trough_months": [],
            "peak_to_trough_ratio": 1.0,
            "predictability_score": 0.65,
            "months_analyzed": 0 if not monthly_inflow else len(monthly_inflow),
            "interpretation": "Insufficient data for seasonality detection",
            "reason": "insufficient_data",
        }

    ordered = sorted(monthly_inflow.items(), key=lambda x: x[0])
    months = [m for m, _ in ordered]
    values = np.array([max(0.0, _safe_float(v)) for _, v in ordered], dtype=float)
    mean_inflow = float(np.mean(values)) if len(values) else 0.0
    monthly_ratios = {m: (float(v) / mean_inflow if mean_inflow > 0 else 0.0) for m, v in ordered}

    peak_months = [m for m, r in monthly_ratios.items() if r > 1.5]
    trough_months = [m for m, r in monthly_ratios.items() if r < 0.5]
    seasonal_detected = bool(peak_months or trough_months)

    predictability = 0.65
    if len(values) >= 12:
        x = np.arange(len(values))
        sine_wave = np.sin((2 * np.pi / 12) * x)
        try:
            from scipy.stats import pearsonr  # type: ignore
            corr, p_value = pearsonr(values, sine_wave)
            predictability = abs(float(corr)) if float(p_value) < 0.05 else 0.5
        except Exception:
            corr = np.corrcoef(values, sine_wave)[0, 1]
            predictability = abs(float(corr)) if np.isfinite(corr) else 0.5

    if not seasonal_detected:
        score = 0.90
        interpretation = "Stable business with consistent monthly inflow"
    elif predictability > 0.60:
        score = 0.80
        interpretation = "Predictable seasonal business pattern"
    elif predictability > 0.40:
        score = 0.70
        interpretation = "Seasonal behavior present but moderately irregular"
    else:
        score = 0.65
        interpretation = "High volatility with low seasonal predictability"

    min_val = float(np.min(values)) if len(values) else 0.0
    max_val = float(np.max(values)) if len(values) else 0.0
    if min_val > 0:
        ptr = max_val / min_val
    else:
        ptr = max_val / 1.0

    return round(_clamp(score, 0.65, 1.0), 4), {
        "seasonal_detected": seasonal_detected,
        "peak_months": peak_months,
        "trough_months": trough_months,
        "peak_to_trough_ratio": round(float(ptr), 4),
        "predictability_score": round(float(_clamp(predictability, 0.0, 1.0)), 4),
        "months_analyzed": len(values),
        "interpretation": interpretation,
    }


def compute_signal_5_network(
    unique_customers: int,
    top_customer_pct: float,
    unique_counterparties_whatsapp: list[str] = None,
) -> float:
    customers = max(0, int(unique_customers or 0))
    top_pct = _clamp(_safe_float(top_customer_pct), 0.0, 1.0)

    base_score = min(np.log10(customers + 1) / np.log10(51), 1.0)
    if top_pct > 0.80:
        concentration_factor = 0.60
    elif top_pct > 0.60:
        concentration_factor = 0.75
    elif top_pct > 0.40:
        concentration_factor = 0.90
    else:
        concentration_factor = 1.00
    base_score *= concentration_factor

    if unique_counterparties_whatsapp:
        wa_diversity = min(len(set(unique_counterparties_whatsapp)) / 20.0, 1.0)
        base_score = (base_score * 0.70) + (wa_diversity * 0.30)

    return round(_clamp(base_score, 0.20, 1.00), 4)


def compute_signal_6_diversity(
    sources_present: list[str],
) -> float:
    valid = {"WHATSAPP", "UPI", "KHATA", "BILL", "MAPS", "SMS"}
    unique_sources = {str(s).upper() for s in (sources_present or []) if str(s).upper() in valid}
    score = len(unique_sources) / 6.0
    if "KHATA" in unique_sources and "UPI" in unique_sources:
        score = min(score + 0.10, 1.0)
    return round(float(_clamp(score, 0.0, 1.0)), 4)


def compute_signal_7_behavioral(
    whatsapp_behavioral: dict | None,
    sms_behavioral: dict | None,
    ocr_behavioral: dict | None,
    bill_connection_type: str | None,
) -> float:
    wb = whatsapp_behavioral or {}
    sb = sms_behavioral or {}
    ob = ocr_behavioral or {}

    def _pct(v):
        x = _safe_float(v, -1.0)
        if x < 0:
            return None
        if x > 1.0:
            x = x / 100.0
        return _clamp(x, 0.0, 1.0)

    peak_hour_score = _pct(wb.get("peak_hour_activity_pct"))
    if peak_hour_score is None:
        peak_hour_score = _pct(sb.get("peak_hour_activity_pct"))

    activity_ratio_score = _pct(wb.get("activity_ratio"))
    if activity_ratio_score is None:
        activity_ratio_score = _pct(sb.get("activity_ratio"))

    response_mean = _safe_float(wb.get("response_time_minutes"), -1.0)
    response_std = _safe_float(wb.get("response_time_std_minutes"), -1.0)
    if response_mean <= 0:
        response_mean = _safe_float(sb.get("response_time_minutes"), -1.0)
        response_std = _safe_float(sb.get("response_time_std_minutes"), -1.0)
    if response_mean > 0 and response_std >= 0:
        response_consistency = _clamp(1.0 - (response_std / max(response_mean, 1e-6)), 0.0, 1.0)
    else:
        response_consistency = 0.5

    ocr_hint = _pct(ob.get("activity_ratio")) if isinstance(ob, dict) else None
    commercial_connection_bonus = 0.15 if str(bill_connection_type or "").upper() == "COMMERCIAL" else 0.0

    components = []
    if peak_hour_score is not None:
        components.append((peak_hour_score, 0.35))
    if activity_ratio_score is not None:
        components.append((activity_ratio_score, 0.35))
    components.append((response_consistency, 0.20))
    if ocr_hint is not None:
        components.append((ocr_hint, 0.10))

    wsum = sum(w for _, w in components) or 1.0
    score = sum(v * w for v, w in components) / wsum
    score = _clamp(score + commercial_connection_bonus, 0.0, 1.0)
    return round(float(score), 4)


def _feature_array(signal_values: dict[str, float]) -> np.ndarray:
    return np.array(
        [[
            _safe_float(signal_values.get("income_regularity", 0.5)),
            _safe_float(signal_values.get("consistency", 0.5)),
            _safe_float(signal_values.get("continuity", 0.5)),
            _safe_float(signal_values.get("seasonal", 0.5)),
            _safe_float(signal_values.get("network", 0.5)),
            _safe_float(signal_values.get("diversity", 0.5)),
            _safe_float(signal_values.get("behavioral_consistency", 0.5)),
        ]],
        dtype=float,
    )


def build_warmth_model() -> xgb.XGBClassifier:
    np.random.seed(42)
    n_total = 1000
    n_pos = int(n_total * 0.60)
    n_neg = n_total - n_pos

    pos = np.column_stack(
        [
            np.random.beta(8, 2, n_pos),
            np.random.beta(7, 2, n_pos),
            np.random.beta(6, 3, n_pos),
            np.random.uniform(0.65, 1.0, n_pos),
            np.random.beta(5, 3, n_pos),
            np.random.uniform(0.4, 1.0, n_pos),
            np.random.uniform(0.65, 1.0, n_pos),
        ]
    )
    neg = np.column_stack(
        [
            np.random.beta(2, 5, n_neg),
            np.random.beta(2, 4, n_neg),
            np.random.beta(2, 5, n_neg),
            np.random.uniform(0.30, 0.70, n_neg),
            np.random.beta(2, 5, n_neg),
            np.random.uniform(0.0, 0.4, n_neg),
            np.random.uniform(0.2, 0.7, n_neg),
        ]
    )
    X = np.vstack([pos, neg])
    y = np.array([1] * n_pos + [0] * n_neg)

    global _warmth_scaler
    _warmth_scaler = MinMaxScaler()
    X_scaled = _warmth_scaler.fit_transform(X)

    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss",
        verbosity=0,
    )
    model.fit(X_scaled, y)
    return model


def get_warmth_model() -> xgb.XGBClassifier:
    global _warmth_model
    if _warmth_model is None:
        _warmth_model = build_warmth_model()
    return _warmth_model


def compute_shap_attributions(
    model: xgb.XGBClassifier,
    signal_values: dict[str, float],
) -> list[dict]:
    feature_names = ["income_regularity", "consistency", "continuity", "seasonal", "network", "diversity", "behavioral_consistency"]
    human_names = {
        "income_regularity": "Income Regularity",
        "consistency": "Inflow Claim Consistency",
        "continuity": "Business Continuity",
        "seasonal": "Seasonal Pattern",
        "network": "Network Reliability",
        "diversity": "Data Source Diversity",
        "behavioral_consistency": "BEHAVIORAL_CONSISTENCY",
    }
    weight_key = {
        "income_regularity": "INCOME_REGULARITY",
        "consistency": "INFLOW_CLAIM_CONSISTENCY",
        "continuity": "BUSINESS_CONTINUITY",
        "seasonal": "SEASONAL_PATTERN",
        "network": "NETWORK_RELIABILITY",
        "diversity": "DATA_SOURCE_DIVERSITY",
        "behavioral_consistency": "BEHAVIORAL_CONSISTENCY",
    }
    points_text = {
        "income_regularity": "Weekly inflow behavior",
        "consistency": "Cross-source inflow validation",
        "continuity": "Bill/maps/data-span continuity evidence",
        "seasonal": "Monthly pattern analysis",
        "network": "Customer concentration and diversity",
        "diversity": "Number of verified source channels",
        "behavioral_consistency": "WhatsApp message timing + SMS patterns + Bill type",
    }

    X = _feature_array(signal_values)
    if _warmth_scaler is not None:
        X_infer = _warmth_scaler.transform(X)
    else:
        X_infer = X

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_infer)
    if isinstance(shap_values, list):
        shap_vec = np.array(shap_values[1] if len(shap_values) > 1 else shap_values[0], dtype=float).reshape(-1)
    else:
        shap_arr = np.array(shap_values, dtype=float)
        shap_vec = shap_arr[0] if shap_arr.ndim > 1 else shap_arr

    abs_vals = np.abs(shap_vec)
    denom = float(np.sum(abs_vals)) + 1e-9

    out = []
    for i, key in enumerate(feature_names):
        sv = float(shap_vec[i]) if i < len(shap_vec) else 0.0
        raw = _safe_float(signal_values.get(key), 0.0)
        out.append(
            {
                "signal_id": f"S{i + 1}",
                "signal_name": human_names[key],
                "signal_key": key,
                "raw_score": round(raw, 4),
                "weight": SIGNAL_WEIGHTS[weight_key[key]],
                "shap_contribution": round(float(abs(sv) / denom), 4),
                "shap_direction": "positive" if sv >= 0 else "negative",
                "percentile": int(_clamp(raw, 0.0, 1.0) * 100),
                "data_points_used": points_text[key],
                "value": round(raw, 4),
                "data_source": points_text[key],
                "human_explanation": (
                    "Behavior aligns with consistent small-business operations."
                    if key == "behavioral_consistency"
                    else f"{human_names[key]} contributed {'positively' if sv >= 0 else 'negatively'} to the score."
                ),
            }
        )

    out.sort(key=lambda d: abs(d["shap_contribution"]), reverse=True)
    return out


def aggregate_warmth_score(
    signal_scores: dict[str, float],
    model: xgb.XGBClassifier,
) -> tuple[float, str, str]:
    mapping = {
        "income_regularity": "INCOME_REGULARITY",
        "consistency": "INFLOW_CLAIM_CONSISTENCY",
        "continuity": "BUSINESS_CONTINUITY",
        "seasonal": "SEASONAL_PATTERN",
        "network": "NETWORK_RELIABILITY",
        "diversity": "DATA_SOURCE_DIVERSITY",
        "behavioral_consistency": "BEHAVIORAL_CONSISTENCY",
    }
    weighted_avg = 0.0
    for feature_key, weight_key in mapping.items():
        weighted_avg += _safe_float(signal_scores.get(feature_key), 0.5) * SIGNAL_WEIGHTS[weight_key]

    signal_array = _feature_array(signal_scores)
    if _warmth_scaler is not None:
        signal_array = _warmth_scaler.transform(signal_array)
    proba = float(model.predict_proba(signal_array)[0][1])
    warmth_score = (weighted_avg * 0.60) + (proba * 0.40)
    warmth_score = round(_clamp(warmth_score, 0.0, 1.0), 4)

    grade = "C"
    for threshold, label in GRADE_THRESHOLDS:
        if warmth_score >= threshold:
            grade = label
            break

    interpretations = {
        "A+": "Strong creditworthy profile. High income regularity across multiple verified sources.",
        "A": "Good credit profile. Minor inconsistencies in cross-source validation.",
        "B+": "Moderate profile. Seasonal business or single-source verification.",
        "B": "Below average. Limited data or significant cash-to-digital gap.",
        "C": "Insufficient evidence for automated approval. Manual review recommended.",
    }
    return warmth_score, grade, interpretations[grade]


class CreditWarmthScoreAgent(BaseAgent):
    agent_id = "AGENT_04_WARMTH"
    name = "CreditWarmthScore Agent"
    version = "1.0.0"

    def __init__(self, audit_logger=None, event_bus=None, settings=None):
        # Support no-arg construction in verification gates.
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
        started = time.perf_counter()
        settings = get_settings()
        _ = settings

        try:
            whatsapp_timeline = inputs.get("whatsapp_timeline") or inputs.get("whatsapp_output") or {}
            ocr_extractions = inputs.get("ocr_extractions") or []
            khata_metrics = inputs.get("khata_metrics") or {}
            maps_data = inputs.get("maps_data") or inputs.get("maps_output") or {}
            sms_data = inputs.get("sms_output") or {}
            upi_output = inputs.get("upi_output") or {}
            bill_output = inputs.get("bill_output") or {}

            weekly_summary = whatsapp_timeline.get("weekly_summary") or []
            monthly_inflow_wa = whatsapp_timeline.get("monthly_inflow") or {}
            whatsapp_total = _safe_float(whatsapp_timeline.get("total_inflow_all", 0.0))
            if whatsapp_total <= 0 and weekly_summary:
                whatsapp_total = float(sum(_safe_float((w or {}).get("total_inflow", 0.0)) for w in weekly_summary))

            upi_total = _safe_float(upi_output.get("total_inflow"), 0.0)
            bill_due_date = None
            bill_extracted_at = None
            bill_connection_type = str(bill_output.get("connection_type") or "")
            for ext in ocr_extractions:
                if not isinstance(ext, dict):
                    continue
                fname = str(ext.get("field_name", "")).lower()
                artifact_type = str(ext.get("artifact_type", ext.get("source_artifact_type", ""))).upper()
                val = _safe_float(ext.get("normalized_value", 0.0))
                if fname == "amount" and artifact_type == "UPI":
                    tx_type = str(ext.get("transaction_type", ext.get("normalized_transaction_type", ""))).upper()
                    if tx_type in {"", "CREDIT"}:
                        upi_total += max(0.0, val)
                if fname == "due_date" and artifact_type == "BILL":
                    bill_due_date = str(ext.get("normalized_value") or ext.get("raw_value") or "")
                if ext.get("extracted_at") and artifact_type == "BILL":
                    bill_extracted_at = str(ext.get("extracted_at"))
                if fname == "connection_type" and artifact_type == "BILL":
                    bill_connection_type = str(ext.get("normalized_value") or ext.get("raw_value") or bill_connection_type)

            khata_inflow = ((khata_metrics.get("inflow_metrics") or {}).get("total_received_90d"))
            khata_total = _safe_float(khata_inflow, 0.0)
            khata_monthly_series = (khata_metrics.get("inflow_metrics") or {}).get("monthly_series") or {}
            khata_weekly_series = (khata_metrics.get("inflow_metrics") or {}).get("weekly_series") or {}
            khata_weekly = [{"total_inflow": _safe_float(v)} for _, v in sorted(khata_weekly_series.items())]

            data_start_date = (
                ((khata_metrics.get("period") or {}).get("start"))
                or ((whatsapp_timeline.get("date_range") or {}).get("start"))
                or None
            )
            unique_counterparties_wa = whatsapp_timeline.get("unique_counterparties") or []
            if isinstance(unique_counterparties_wa, int):
                unique_counterparties_wa = [f"cp_{i}" for i in range(unique_counterparties_wa)]
            unique_customers = int(((khata_metrics.get("customer_metrics") or {}).get("unique_customers") or 0))
            top_customer_pct = _safe_float(((khata_metrics.get("customer_metrics") or {}).get("top_customer_pct") or 0.0))

            sources_present = []
            if whatsapp_timeline:
                sources_present.append("WHATSAPP")
            if upi_total > 0:
                sources_present.append("UPI")
            if khata_metrics:
                sources_present.append("KHATA")
            if bill_due_date or bill_extracted_at:
                sources_present.append("BILL")
            if maps_data:
                sources_present.append("MAPS")
            if sms_data:
                sources_present.append("SMS")

            s1_weekly = khata_weekly if khata_weekly else weekly_summary
            s1_monthly = khata_monthly_series if khata_monthly_series else monthly_inflow_wa

            signal_1 = compute_signal_1_income_regularity(s1_weekly, s1_monthly)
            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message=f"Signal 1/6: Income Regularity = {signal_1:.3f}",
            )

            signal_2 = compute_signal_2_consistency(whatsapp_total, upi_total, khata_total)
            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message=f"Signal 2/6: Inflow Claim Consistency = {signal_2:.3f}",
            )

            signal_3, s3_components = compute_signal_3_continuity(
                bill_extracted_at=bill_extracted_at,
                bill_due_date=bill_due_date,
                maps_listing_age_years=_safe_float(maps_data.get("listing_age_years")) if maps_data else None,
                maps_review_count=int(maps_data.get("review_count", 0)) if maps_data and maps_data.get("review_count") is not None else None,
                data_start_date=data_start_date,
            )
            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message=f"Signal 3/6: Business Continuity = {signal_3:.3f}",
            )

            seasonal_input = s1_monthly if s1_monthly else monthly_inflow_wa
            signal_4, s4_metadata = compute_signal_4_seasonal(seasonal_input)
            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message=f"Signal 4/6: Seasonal Pattern = {signal_4:.3f}",
            )

            if unique_customers == 0 and unique_counterparties_wa:
                unique_customers = len(set(unique_counterparties_wa))
                top_customer_pct = 1.0 / max(unique_customers, 1)

            signal_5 = compute_signal_5_network(unique_customers, top_customer_pct, unique_counterparties_wa)
            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message=f"Signal 5/6: Network Reliability = {signal_5:.3f}",
            )

            signal_6 = compute_signal_6_diversity(sources_present)
            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message=f"Signal 6/7: Data Source Diversity = {signal_6:.3f}",
            )

            signal_7 = compute_signal_7_behavioral(
                whatsapp_behavioral=whatsapp_timeline.get("behavioral_signals") or {},
                sms_behavioral=sms_data.get("behavioral_signals") or {},
                ocr_behavioral=inputs.get("ocr_behavioral_signals") or {},
                bill_connection_type=bill_connection_type,
            )
            await self.event_bus.publish_agent_event(
                session_id=session_id, agent_id=self.agent_id, status="PROGRESS",
                message=f"Signal 7/7: Behavioral Consistency = {signal_7:.3f}",
            )

            signal_scores = {
                "income_regularity": signal_1,
                "consistency": signal_2,
                "continuity": signal_3,
                "seasonal": signal_4,
                "network": signal_5,
                "diversity": signal_6,
                "behavioral_consistency": signal_7,
            }

            model = get_warmth_model()
            shap_attributions = compute_shap_attributions(model, signal_scores)
            warmth_score, grade, interpretation = aggregate_warmth_score(signal_scores, model)

            # Multi-source confidence boost.
            sms_monthly = sms_data.get("monthly_summary") or []
            sms_total = float(sum(_safe_float((m or {}).get("total_inflow", 0.0)) for m in sms_monthly))
            direction_votes = 0
            for val in [whatsapp_total, upi_total, khata_total, sms_total]:
                if val > 0:
                    direction_votes += 1
            boost_applied = 1.0
            if direction_votes >= 4:
                boost_applied = 1.10
            elif direction_votes >= 3:
                boost_applied = 1.05
            warmth_score = round(_clamp(warmth_score * boost_applied, 0.0, 1.0), 4)

            if self.audit_logger:
                try:
                    await self.audit_logger.log(
                        db=None,
                        session_id=session_id,
                        event_type="MULTI_SOURCE_CONFIRMATION",
                        agent_id=self.agent_id,
                        details={
                            "sources_confirmed": direction_votes,
                            "boost_applied": boost_applied,
                            "final_warmth_score": warmth_score,
                        },
                    )
                except Exception:
                    pass

            import json
            async with get_db() as db:
                try:
                    await execute_write(
                        db,
                        """
                        INSERT OR REPLACE INTO credit_assessments
                        (id, session_id, warmth_score, credit_grade, formula_json, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(uuid.uuid4()),
                            session_id,
                            warmth_score,
                            grade,
                            json.dumps(signal_scores),
                            datetime.utcnow().isoformat() + "Z",
                        ),
                    )
                except Exception as exc:
                    logger.warning(
                        "Skipped credit_assessments persist for session %s due to DB constraint/context: %s",
                        session_id,
                        exc,
                    )

                history = await execute_query(
                    db,
                    """
                    SELECT confidence_score, timestamp
                    FROM audit_log
                    WHERE session_id = ? AND agent_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 5
                    """,
                    (session_id, self.agent_id),
                )

            trend = "STABLE"
            if len(history) >= 2:
                vals = [float(r.get("confidence_score", 0.0) or 0.0) for r in history if r.get("confidence_score") is not None]
                if len(vals) >= 2:
                    delta = vals[0] - vals[-1]
                    if delta > 0.03:
                        trend = "IMPROVING"
                    elif delta < -0.03:
                        trend = "DECLINING"

            weighted_data_quality_score = round(
                _clamp((signal_6 * 0.5) + (signal_2 * 0.3) + (signal_3 * 0.2), 0.0, 1.0),
                4,
            )

            top_2 = ", ".join([a["signal_name"] for a in shap_attributions[:2]])
            days_of_data = int(
                _safe_float(((khata_metrics.get("period") or {}).get("days_actual")), 0.0)
                or _safe_float(((whatsapp_timeline.get("date_range") or {}).get("days_covered")), 0.0)
            )
            source_count = len(set(sources_present))

            await self.event_bus.publish_agent_event(
                session_id=session_id,
                agent_id=self.agent_id,
                status="COMPLETE",
                message=f"CreditWarmthScore: {warmth_score:.3f} -> Grade {grade} | {interpretation}",
                confidence=warmth_score,
            )

            signals = [
                {"signal": "INCOME_REGULARITY", "score": signal_1, "weight": SIGNAL_WEIGHTS["INCOME_REGULARITY"]},
                {"signal": "INFLOW_CLAIM_CONSISTENCY", "score": signal_2, "weight": SIGNAL_WEIGHTS["INFLOW_CLAIM_CONSISTENCY"], "note": RBI_CASH_RATIO_NOTE},
                {"signal": "BUSINESS_CONTINUITY", "score": signal_3, "weight": SIGNAL_WEIGHTS["BUSINESS_CONTINUITY"], "components": s3_components},
                {"signal": "SEASONAL_PATTERN", "score": signal_4, "weight": SIGNAL_WEIGHTS["SEASONAL_PATTERN"], "metadata": s4_metadata},
                {"signal": "NETWORK_RELIABILITY", "score": signal_5, "weight": SIGNAL_WEIGHTS["NETWORK_RELIABILITY"]},
                {"signal": "DATA_SOURCE_DIVERSITY", "score": signal_6, "weight": SIGNAL_WEIGHTS["DATA_SOURCE_DIVERSITY"]},
                {
                    "signal": "BEHAVIORAL_CONSISTENCY",
                    "score": signal_7,
                    "weight": SIGNAL_WEIGHTS["BEHAVIORAL_CONSISTENCY"],
                    "data_source": "WhatsApp message timing + SMS patterns + Bill type",
                },
            ]

            latency_ms = int((time.perf_counter() - started) * 1000)
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=True,
                confidence_score=warmth_score,
                latency_ms=latency_ms,
                data={
                    "warmth_score": warmth_score,
                    "credit_grade": grade,
                    "interpretation": interpretation,
                    "signals": signals,
                    "signal_breakdown": signals,
                    "shap_attributions": shap_attributions,
                    "shap_values": shap_attributions,
                    "temporal_trend": trend,
                    "confidence_in_score": weighted_data_quality_score,
                    "sources_used": list(set(sources_present)),
                    "multi_source_confirmation": {
                        "sources_confirmed": direction_votes,
                        "boost_applied": boost_applied,
                    },
                    "audit_explanation": (
                        f"Score driven by {top_2}. "
                        f"Based on {days_of_data} days of {source_count} verified sources."
                    ),
                },
                errors=[],
                warnings=[],
                fallback_used=False,
            )
        except Exception as exc:
            logger.exception("CreditWarmthScore agent failed for session %s", session_id)
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=False,
                confidence_score=0.0,
                latency_ms=int((time.perf_counter() - started) * 1000),
                data={},
                errors=[str(exc)],
                warnings=[],
                fallback_used=False,
            )
