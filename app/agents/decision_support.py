"""Decision-support engine — generates strategic insights in dual LLM passes."""

import json
import logging
import re

from app.model_config import get_llm_with_fallback as get_llm
from app.schemas import (
    IntakeResult, DemandSignal, MarketSizing, CompetitorEntry,
    OverallEvaluation, DecisionSupport, SegmentRank, MoatFactor,
    BusinessModelOption, VCFit, InvestorReadiness, UserBuyerPayer,
    Beachhead, PricingTier, ProductPhase, SuccessMetric, ScoreBreakdownItem,
)

logger = logging.getLogger(__name__)

_STRATEGIC_PROMPT = """You are a startup analyst. Based on the evidence, answer in JSON.

Rules:
- For moat factors: set status to "confirmed", "likely", "unknown", or "negative_evidence". NEVER set status to "confirmed" or "negative_evidence" unless the evidence explicitly states it. Use "unknown" when the idea simply does not mention it.
- For score_breakdown: start at BASE 100, then add or subtract points for each dimension. Each item is: {{"action": "add" or "subtract", "points": N, "reason": "short reason"}}
- If you do not have evidence for a claim, omit it. Never invent numbers.

Evidence:
{evidence_json}

Return JSON:
{{"score_breakdown": [{{"action": "add", "points": 18, "reason": "Strong demand signal"}}, {{"action": "subtract", "points": 15, "reason": "Crowded market"}}],
  "moat_factors": [{{"name": "data_moat", "status": "unknown", "explanation": "Idea does not mention data moat."}}, {{"name": "algorithm_moat", "status": "confirmed", "explanation": "Custom ML models described."}}, {{"name": "patent_moat", "status": "unknown", "explanation": "No patent strategy described."}}, {{"name": "network_effects", "status": "negative_evidence", "explanation": "Single-sided platform; no network effects possible."}}, {{"name": "switching_cost", "status": "likely", "explanation": "Tight integration with workflows creates stickiness."}}],
  "customer_segments": [{{"name": "segment", "rank": 1, "reasoning": "why best first target"}}, {{"name": "segment", "rank": 2, "reasoning": "why"}}],
  "business_models": [{{"name": "model", "viability": 80, "reasoning": "why"}}, {{"name": "model", "viability": 60, "reasoning": "why"}}],
  "differentiation_answer": "Why customer buys from YOU vs competitors?",
  "why_now": "Why should this startup exist NOW?",
  "user_buyer_payer": {{"user": "who uses it daily", "buyer": "who evaluates purchase", "economic_buyer": "who controls budget", "decision_maker": "who approves", "champion": "who advocates internally", "influencer": "who advises"}},
  "funding_recommendation": "Bootstrappable? VC? Grants?",
  "beachhead": [{{"segment": "first niche", "reasoning": "why this first"}}, {{"segment": "second niche", "reasoning": "why next"}}],
  "pricing": [{{"name": "Starter", "price": "₹8000/mo", "target": "small teams", "reasoning": "low friction entry"}}, {{"name": "Growth", "price": "₹25000/mo", "target": "mid-size", "reasoning": "value-based"}}, {{"name": "Enterprise", "price": "Custom", "target": "large orgs", "reasoning": "negotiated"}}],
  "build_decision": "One of: BUILD, BUILD_AFTER_VALIDATION, PIVOT, DONT_BUILD",
  "build_reasoning": "Detailed explanation of why this decision."}}

Include 5 moat factors, 5 segments, 4 business models, 3 pricing tiers, 2 beachhead steps. JSON:"""

_TACTICAL_PROMPT = """You generate tactical startup advice. Based on the evidence below, answer in JSON.

Evidence:
{evidence_json}

Return JSON:
{{"vc_fit": [{{"firm": "YC", "score": 3, "reasoning": "why"}}, {{"firm": "a16z", "score": 4, "reasoning": "why"}}, {{"firm": "Sequoia", "score": 3, "reasoning": "why"}}, {{"firm": "SOSV", "score": 5, "reasoning": "why"}}],
  "investor_readiness": [{{"question": "Is this VC-backable?", "assessment": "answer"}}, {{"question": "Bootstrap-friendly?", "assessment": "answer"}}, {{"question": "Expected funding need", "assessment": "answer"}}, {{"question": "Typical sales cycle", "assessment": "answer"}}, {{"question": "Time to first revenue", "assessment": "answer"}}],
  "validation_roadmap": ["Week 1: 15 customer interviews in specific niche", "Week 2: landing page + signups", "Week 3: clickable MVP", "Week 4: deploy to 1 pilot customer", "Week 5: collect feedback + iterate", "Week 6: charge first customer"],
  "financial_projection": "Assumptions: Price X, Target Y customers, ARR = X*Y. Then Year 1-3 projection with explicit assumptions listed first.",
  "investor_questions": ["Key question 1?", "Key question 2?", "Key question 3?", "Key question 4?", "Key question 5?"],
  "red_team_fail": ["5 specific reasons this fails"],
  "red_team_succeed": ["5 specific reasons this succeeds"],
  "founder_coach": ["5 concrete actions to take tomorrow"],
  "product_roadmap": [{{"phase": "MVP", "description": "core feature set"}}, {{"phase": "Beta", "description": "limited pilot"}}, {{"phase": "Pilot", "description": "paid pilot users"}}, {{"phase": "Paid Pilot", "description": "first revenue"}}, {{"phase": "Enterprise", "description": "full product"}}, {{"phase": "Scale", "description": "growth infrastructure"}}],
  "success_metrics": [{{"metric": "Customer interviews", "target": "20", "timeframe": "30 days"}}, {{"metric": "LOIs signed", "target": "3", "timeframe": "60 days"}}, {{"metric": "Pilot revenue", "target": "₹50k MRR", "timeframe": "90 days"}}]}}

Include exactly 5 red_team_fail, 5 red_team_succeed, 5 founder_coach, 6 roadmap phases, 5 success metrics, 4 vc_fit entries. JSON:"""


async def generate_decision_support(
    intake: IntakeResult,
    demand: DemandSignal,
    competitors: list[CompetitorEntry],
    market_sizing: MarketSizing,
    evaluation: OverallEvaluation | None,
) -> DecisionSupport:
    evidence = _build_evidence(intake, demand, competitors, market_sizing, evaluation)

    try:
        result = DecisionSupport()
        llm = get_llm(model="qwen3:1.7b", temperature=0.5, num_predict=2048)
        evidence_json = json.dumps(evidence, indent=2)

        response = llm.invoke(_STRATEGIC_PROMPT.format(evidence_json=evidence_json))
        strategic = _try_parse(response.content)
        if strategic:
            result = _merge_strategic(result, strategic)

        response = llm.invoke(_TACTICAL_PROMPT.format(evidence_json=evidence_json))
        tactical = _try_parse(response.content)
        if tactical:
            result = _merge_tactical(result, tactical)

        return result
    except Exception:
        logger.warning("decision support LLM call failed", exc_info=True)
        return DecisionSupport()


def _build_evidence(intake, demand, competitors, market_sizing, evaluation):
    comp_lines = []
    for c in competitors[:8]:
        edge = f" Your edge: {c.your_edge[:80]}" if c.your_edge else ""
        comp_lines.append(f"- {c.name}: {c.description[:100]}{edge}")
    comp_list = "\n".join(comp_lines) or "None found"
    dims_list = "\n".join(
        f"- {d.name}: {d.score}/100 ({d.explanation[:80]})"
        for d in (evaluation.dimensions[:8] if evaluation else [])
    ) or "None"
    return f"""Problem: {intake.problem_statement}
Target user: {intake.target_user}
Solution: {intake.proposed_solution}
Category: {intake.category or 'N/A'}
Startup type: {intake.startup_type}
Demand: {demand.strength} ({len(demand.evidence)} sources)
Market: {market_sizing.estimate_summary[:200]}
Score: {evaluation.overall_score if evaluation else 'N/A'}/100
Verdict: {evaluation.recommendation.verdict if evaluation else 'N/A'}
Reasoning: {evaluation.reasoning if evaluation else ''}
Competitors:
{comp_list}
Dimensions:
{dims_list}"""


def _try_parse(text: str) -> dict | None:
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        return None


def _merge_strategic(result: DecisionSupport, data: dict) -> DecisionSupport:
    raw = data.get("score_breakdown", [])
    if isinstance(raw, list):
        items = []
        for item in raw:
            if isinstance(item, dict):
                action = item.get("action", "subtract")
                points = item.get("points", 0)
                reason = item.get("reason", "")
                items.append(ScoreBreakdownItem(action=action, points=points, reason=reason))
            elif isinstance(item, str):
                parts = item.strip().split(maxsplit=1)
                if len(parts) == 2:
                    prefix, reason = parts
                    if prefix.startswith("+"):
                        items.append(ScoreBreakdownItem(action="add", points=0, reason=reason))
                    elif prefix.startswith("-"):
                        items.append(ScoreBreakdownItem(action="subtract", points=0, reason=reason))
                    else:
                        items.append(ScoreBreakdownItem(action="add", points=0, reason=item))
                else:
                    items.append(ScoreBreakdownItem(action="add", points=0, reason=item))
        result.score_breakdown = items

    moats = data.get("moat_factors", [])
    if isinstance(moats, list):
        parsed = []
        for m in moats:
            if isinstance(m, dict):
                parsed.append(MoatFactor(name=m.get("name", ""), status=m.get("status", "unknown"), explanation=m.get("explanation", "")))
        result.moat_factors = parsed

    segments = data.get("customer_segments", [])
    if isinstance(segments, list):
        result.customer_segments = [SegmentRank(**s) for s in segments if isinstance(s, dict)]
    models = data.get("business_models", [])
    if isinstance(models, list):
        result.business_models = [BusinessModelOption(**b) for b in models if isinstance(b, dict)]

    result.differentiation_answer = data.get("differentiation_answer", "")
    result.why_now = data.get("why_now", "")
    ubp = data.get("user_buyer_payer", {})
    if isinstance(ubp, dict):
        result.user_buyer_payer = UserBuyerPayer(**ubp)
    result.funding_recommendation = data.get("funding_recommendation", "")

    beachhead = data.get("beachhead", [])
    if isinstance(beachhead, list):
        result.beachhead = [Beachhead(**b) for b in beachhead if isinstance(b, dict)]

    pricing = data.get("pricing", [])
    if isinstance(pricing, list):
        result.pricing = [PricingTier(**p) for p in pricing if isinstance(p, dict)]

    result.build_decision = data.get("build_decision", "")
    result.build_reasoning = data.get("build_reasoning", "")

    return result


def _merge_tactical(result: DecisionSupport, data: dict) -> DecisionSupport:
    vc = data.get("vc_fit", [])
    if isinstance(vc, list):
        result.vc_fit = [VCFit(**v) for v in vc if isinstance(v, dict) and "firm" in v]
    readiness = data.get("investor_readiness", [])
    if isinstance(readiness, list):
        result.investor_readiness = [InvestorReadiness(**r) for r in readiness if isinstance(r, dict) and "question" in r]
    result.validation_roadmap = data.get("validation_roadmap", [])
    result.financial_projection = data.get("financial_projection", "")
    result.investor_questions = data.get("investor_questions", [])
    result.red_team_fail = data.get("red_team_fail", [])
    result.red_team_succeed = data.get("red_team_succeed", [])
    result.founder_coach = data.get("founder_coach", [])

    roadmap = data.get("product_roadmap", [])
    if isinstance(roadmap, list):
        result.product_roadmap = [ProductPhase(**p) for p in roadmap if isinstance(p, dict)]

    metrics = data.get("success_metrics", [])
    if isinstance(metrics, list):
        result.success_metrics = [SuccessMetric(**m) for m in metrics if isinstance(m, dict)]

    return result
