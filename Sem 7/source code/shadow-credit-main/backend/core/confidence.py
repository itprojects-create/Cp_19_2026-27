from __future__ import annotations

from enum import Enum

try:
    from backend.config import get_settings
except ModuleNotFoundError:
    from config import get_settings


class ConfidenceBand(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SupervisorAction(str, Enum):
    AUTO_ACCEPT = "AUTO_ACCEPT"
    CLARIFY = "CLARIFY"
    FALLBACK = "FALLBACK"


def classify_confidence(score: float) -> tuple[ConfidenceBand, SupervisorAction]:
    if score < 0 or score > 1:
        raise ValueError("score must be between 0 and 1")

    settings = get_settings()
    high = settings.CONFIDENCE_HIGH_THRESHOLD
    medium = settings.CONFIDENCE_MEDIUM_THRESHOLD

    if score >= high:
        return ConfidenceBand.HIGH, SupervisorAction.AUTO_ACCEPT
    if score >= medium:
        return ConfidenceBand.MEDIUM, SupervisorAction.CLARIFY
    return ConfidenceBand.LOW, SupervisorAction.FALLBACK


def aggregate_confidence(
    scores: list[float],
    weights: list[float] = None,
) -> float:
    if not scores:
        raise ValueError("scores cannot be empty")
    if any(score < 0 or score > 1 for score in scores):
        raise ValueError("all scores must be between 0 and 1 inclusive")

    if weights is not None:
        if len(scores) != len(weights):
            raise ValueError("scores and weights must have same length")
        if any(weight < 0 for weight in weights):
            raise ValueError("weights cannot be negative")
        total_weight = sum(weights)
        if total_weight == 0:
            raise ValueError("weights sum cannot be zero")
        value = sum(score * weight for score, weight in zip(scores, weights)) / total_weight
    else:
        value = sum(scores) / len(scores)

    return round(float(value), 4)


def confidence_trend(scores: list[float]) -> str:
    if len(scores) < 2:
        raise ValueError("at least 2 scores are required")
    if any(score < 0 or score > 1 for score in scores):
        raise ValueError("all scores must be between 0 and 1 inclusive")

    midpoint = len(scores) // 2
    first_half = scores[:midpoint]
    second_half = scores[midpoint:]

    first_avg = sum(first_half) / len(first_half)
    second_avg = sum(second_half) / len(second_half)
    diff = second_avg - first_avg

    if diff > 0.05:
        return "IMPROVING"
    if diff < -0.05:
        return "DECLINING"
    return "STABLE"
