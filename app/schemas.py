from typing import Literal
from pydantic import BaseModel


StartupType = Literal[
    "deep-tech", "enterprise-saas", "smb-saas", "marketplace",
    "ecommerce", "consumer-app", "hardware", "biotech",
    "fintech", "cleantech", "developer-tools", "other",
]


class SourcedClaim(BaseModel):
    text: str
    source_url: str
    source_name: str


class CompetitorEntry(BaseModel):
    name: str
    description: str
    funding_signal: str | None = None
    source_url: str
    is_verified_competitor: bool = False


class DemandSignal(BaseModel):
    evidence: list[SourcedClaim]
    strength: Literal["weak", "moderate", "strong"]


class MarketSizing(BaseModel):
    estimate_summary: str
    basis: list[SourcedClaim]
    confidence: Literal["low", "medium"]


class EvaluationDimension(BaseModel):
    name: str
    score: int
    weight: float
    explanation: str
    confidence: Literal["low", "medium", "high"]


class Recommendation(BaseModel):
    verdict: Literal["build", "narrow", "pivot", "abandon", "insufficient-info"]
    summary: str
    kill_criteria: list[str]
    next_steps: list[str]


class ViabilityScore(BaseModel):
    score: int
    breakdown: dict[str, int]
    weighting_explanation: str


class OverallEvaluation(BaseModel):
    dimensions: list[EvaluationDimension]
    overall_score: float
    reasoning: str
    recommendation: Recommendation


class IntakeResult(BaseModel):
    problem_statement: str
    target_user: str
    proposed_solution: str
    category: str | None = None
    startup_type: StartupType = "other"
    raw_idea: str
    input_quality: Literal["poor", "fair", "good"] = "fair"
    missing_fields: list[str] = []


class ValidationReport(BaseModel):
    intake: IntakeResult
    demand: DemandSignal
    competitors: list[CompetitorEntry]
    market_sizing: MarketSizing
    risks: list[str]
    evaluation: OverallEvaluation | None = None
    viability: ViabilityScore | None = None
    business_plan_draft: str = ""
    unresolved_claims_stripped: int = 0
