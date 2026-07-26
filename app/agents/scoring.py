"""Scoring is now handled by the evaluator. This module provides the compatibility wrapper."""
from app.schemas import (
    ViabilityScore, OverallEvaluation,
)


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
