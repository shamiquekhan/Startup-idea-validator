"""Scoring is now handled by the evaluator. This module provides the compatibility wrapper."""
from app.schemas import (
    ViabilityScore, DemandSignal, MarketSizing, OverallEvaluation,
)

_STRENGTH_SCORES = {"weak": 20, "moderate": 50, "strong": 85}
_CONFIDENCE_SCORES = {"low": 20, "medium": 60}


def compute_viability(
    demand: DemandSignal,
    competitor_count: int,
    market_sizing: MarketSizing,
    risk_count: int,
) -> ViabilityScore:
    demand_score = _STRENGTH_SCORES.get(demand.strength, 30)
    competition_score = _competition_score(competitor_count)
    market_score = _CONFIDENCE_SCORES.get(market_sizing.confidence, 15)
    risk_penalty = min(risk_count * 8, 40)
    risk_score = max(60, 100 - risk_penalty)

    total = round(
        demand_score * 0.30
        + competition_score * 0.25
        + market_score * 0.25
        + risk_score * 0.20
    )
    total = max(0, min(100, total))

    return ViabilityScore(
        score=total,
        breakdown={
            "demand": demand_score,
            "competition": competition_score,
            "market_size": market_score,
            "risk": risk_score,
        },
        weighting_explanation=(
            f"Weighted formula: demand (30%) + competition (25%) + "
            f"market size (25%) + risk (20%)"
        ),
    )


def _competition_score(count: int) -> int:
    if count == 0: return 50
    if count == 1: return 75
    if count <= 3: return 65
    if count <= 5: return 55
    if count <= 8: return 45
    if count <= 12: return 35
    return 25


def evaluation_to_viability(eval: OverallEvaluation) -> ViabilityScore:
    breakdown = {}
    for d in eval.dimensions:
        breakdown[d.name] = d.score
    return ViabilityScore(
        score=eval.overall_score,
        breakdown=breakdown,
        weighting_explanation=" | ".join(
            f"{d.name}: {d.weight*100:.0f}%" for d in eval.dimensions
        ),
    )
