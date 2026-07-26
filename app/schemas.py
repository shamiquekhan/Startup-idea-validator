from typing import Literal
from pydantic import BaseModel


StartupType = Literal[
    "deep-tech", "enterprise-saas", "smb-saas", "marketplace",
    "ecommerce", "consumer-app", "hardware", "biotech",
    "fintech", "cleantech", "healthtech",
    "legaltech", "edtech", "insurtech", "proptech", "agtech",
    "developer-tools", "other",
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
    focus_area: str | None = None
    target_customer: str | None = None
    weakness: str | None = None
    your_edge: str | None = None


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


class SegmentRank(BaseModel):
    name: str
    rank: int
    reasoning: str


MoatStatus = Literal["confirmed", "likely", "unknown", "negative_evidence"]

class MoatFactor(BaseModel):
    name: str
    status: MoatStatus = "unknown"
    explanation: str


class BusinessModelOption(BaseModel):
    name: str
    viability: int
    reasoning: str


class VCFit(BaseModel):
    firm: str
    score: int
    reasoning: str


class CustomerRole(BaseModel):
    role: str
    description: str


class InvestorReadiness(BaseModel):
    question: str
    assessment: str


class UserBuyerPayer(BaseModel):
    user: str = ""
    buyer: str = ""
    economic_buyer: str = ""
    decision_maker: str = ""
    champion: str = ""
    influencer: str = ""


class Beachhead(BaseModel):
    segment: str = ""
    reasoning: str = ""


class PricingTier(BaseModel):
    name: str = ""
    price: str = ""
    target: str = ""
    reasoning: str = ""


class ProductPhase(BaseModel):
    phase: str = ""
    description: str = ""


class SuccessMetric(BaseModel):
    metric: str = ""
    target: str = ""
    timeframe: str = ""


class ScoreBreakdownItem(BaseModel):
    action: Literal["add", "subtract"]
    reason: str
    points: int


class DecisionSupport(BaseModel):
    moat_factors: list[MoatFactor] = []
    score_breakdown: list[ScoreBreakdownItem] = []
    customer_segments: list[SegmentRank] = []
    business_models: list[BusinessModelOption] = []
    differentiation_answer: str = ""
    funding_recommendation: str = ""
    vc_fit: list[VCFit] = []
    validation_roadmap: list[str] = []
    financial_projection: str = ""
    investor_questions: list[str] = []
    investor_readiness: list[InvestorReadiness] = []
    red_team_fail: list[str] = []
    red_team_succeed: list[str] = []
    founder_coach: list[str] = []
    why_now: str = ""
    user_buyer_payer: UserBuyerPayer = UserBuyerPayer()
    beachhead: list[Beachhead] = []
    pricing: list[PricingTier] = []
    product_roadmap: list[ProductPhase] = []
    success_metrics: list[SuccessMetric] = []
    build_decision: str = ""
    build_reasoning: str = ""


class CompletenessResult(BaseModel):
    completeness_score: float = 0
    fields: dict = {}
    follow_up_questions: list[str] = []
    summary: str = ""


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
    decision_support: DecisionSupport | None = None
    completeness: CompletenessResult | None = None
