"""Structured startup evaluation across real investment/founder dimensions."""

import json
import re
from langchain_ollama import ChatOllama

from app.schemas import (
    IntakeResult, DemandSignal, CompetitorEntry, MarketSizing,
    EvaluationDimension, Recommendation, OverallEvaluation,
    StartupType,
)

_EVALUATOR_PROMPT = """You are a veteran startup evaluator and angel investor. Evaluate this startup idea rigorously across the dimensions below.

Return ONLY valid JSON. Be critical — it's better to flag risks than to be optimistic.

Context:
- Problem: {problem}
- Target user: {target_user}
- Solution: {solution}
- Category: {category}
- Startup type: {startup_type}
- Demand signal: {demand_strength} ({demand_count} sources)
- Competitors found: {competitor_count} ({competitor_names})
- Market sources: {market_count}
- Missing from input: {missing_fields}
- Input quality: {input_quality}

CRITICAL RULES:
1. Vary scores across dimensions based on available evidence — do NOT default to 50 for all.
2. If customer, problem, or solution are missing from input, set customer_clarity, problem_pain, or solution_fit to 20-40 with low confidence. State "not specified" — do NOT invent or guess a customer segment.
3. Never fabricate customer details. If the target user is "not specified" or "unknown", customer_clarity must be ≤30 and the explanation must say "Customer not specified — cannot evaluate".
4. The overall_score must reflect the weighted sum. If many dimensions are low-confidence and below 50, the overall score should be below 60.
5. Do NOT recommend "build" if fundamental info (customer, problem) is missing.
6. For deep-tech/cleantech categories, be especially critical of: experimental validation costs, long sales cycles, regulatory hurdles, and capital requirements.

You MUST return JSON in this EXACT format (use the exact key names shown):
{{
  "dimensions": [
    {{"name": "problem_pain", "score": 0-100, "weight": 0.0-1.0, "explanation": "2-3 sentences", "confidence": "low/medium/high"}},
    {{"name": "customer_clarity", "score": 0-100, "weight": 0.0-1.0, "explanation": "2-3 sentences", "confidence": "low/medium/high"}},
    {{"name": "solution_fit", "score": 0-100, "weight": 0.0-1.0, "explanation": "2-3 sentences", "confidence": "low/medium/high"}},
    {{"name": "competitive_position", "score": 0-100, "weight": 0.0-1.0, "explanation": "2-3 sentences", "confidence": "low/medium/high"}},
    {{"name": "technical_feasibility", "score": 0-100, "weight": 0.0-1.0, "explanation": "2-3 sentences", "confidence": "low/medium/high"}},
    {{"name": "business_model", "score": 0-100, "weight": 0.0-1.0, "explanation": "2-3 sentences", "confidence": "low/medium/high"}},
    {{"name": "adoption_barriers", "score": 0-100, "weight": 0.0-1.0, "explanation": "2-3 sentences", "confidence": "low/medium/high"}},
    {{"name": "team_requirements", "score": 0-100, "weight": 0.0-1.0, "explanation": "2-3 sentences", "confidence": "low/medium/high"}}
  ],
  "overall_score": 0-100,
  "reasoning": "3-4 sentence summary assessment",
  "recommendation": {{
    "verdict": "build|narrow|pivot|abandon|insufficient-info",
    "summary": "one-line verdict",
    "kill_criteria": ["condition 1", "condition 2"],
    "next_steps": ["step 1", "step 2", "step 3"]
  }}
}}

All weights must sum to 1.0.

Verdict options:
- "build" = clear opportunity, manageable risk, AND customer/problem/solution are all known
- "narrow" = promising but needs focus on a specific vertical/segment
- "pivot" = problem may exist but solution/customer needs rethinking
- "abandon" = too many red flags
- "insufficient-info" = need more details about customer/problem/solution (use when 2+ fields missing)

JSON:"""


async def evaluate(
    intake: IntakeResult,
    demand: DemandSignal,
    competitors: list[CompetitorEntry],
    market_sizing: MarketSizing,
    model: str = "qwen3:1.7b",
) -> OverallEvaluation:
    competitor_names = ", ".join(c.name for c in competitors[:8]) or "none found"
    missing = ", ".join(intake.missing_fields) if intake.missing_fields else "none"

    prompt = _EVALUATOR_PROMPT.format(
        problem=intake.problem_statement,
        target_user=intake.target_user,
        solution=intake.proposed_solution,
        category=intake.category or "not specified",
        startup_type=intake.startup_type or "not specified",
        demand_strength=demand.strength,
        demand_count=len(demand.evidence),
        competitor_count=len(competitors),
        competitor_names=competitor_names,
        market_count=len(market_sizing.basis),
        missing_fields=missing,
        input_quality=intake.input_quality,
    )

    try:
        llm = ChatOllama(model=model, temperature=0.2, num_predict=2048)
        response = llm.invoke(prompt)
        text = response.content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        return _parse_evaluation(data, intake.startup_type, intake.input_quality)
    except Exception:
        return _fallback_evaluation(demand, competitors, intake.input_quality)


def _parse_evaluation(data: dict, startup_type: StartupType, input_quality: str = "poor") -> OverallEvaluation:
    dims_raw = data.get("dimensions", data.get("evaluation", []))
    if isinstance(dims_raw, dict):
        dims_raw = list(dims_raw.values())

    dimensions = []
    for d in dims_raw:
        dimensions.append(EvaluationDimension(
            name=d.get("name", d.get("dimension", "unknown")),
            score=d.get("score", 50),
            weight=d.get("weight", 0.125),
            explanation=d.get("explanation", ""),
            confidence=d.get("confidence", "low"),
        ))

    if not dimensions:
        dimensions = _default_dimensions(input_quality)

    rec_data = data.get("recommendation", {})
    if isinstance(rec_data, str):
        rec_data = {"verdict": rec_data, "summary": rec_data}

    rec = Recommendation(
        verdict=rec_data.get("verdict", "insufficient-info"),
        summary=rec_data.get("summary", "Assessment complete."),
        kill_criteria=rec_data.get("kill_criteria", []),
        next_steps=rec_data.get("next_steps", []),
    )

    overall = data.get("overall_score", 0)
    if not overall:
        overall = round(sum(d.score * d.weight for d in dimensions))

    return OverallEvaluation(
        dimensions=dimensions,
        overall_score=min(100, max(0, overall)),
        reasoning=data.get("reasoning", ""),
        recommendation=rec,
    )


def _default_dimensions(input_quality: str = "poor") -> list[EvaluationDimension]:
    if input_quality == "good":
        return [
            EvaluationDimension(name="problem_pain", score=60, weight=0.15, explanation="Problem stated but needs validation", confidence="medium"),
            EvaluationDimension(name="customer_clarity", score=55, weight=0.15, explanation="Customer partially described", confidence="medium"),
            EvaluationDimension(name="solution_fit", score=55, weight=0.10, explanation="Solution described but fit unclear", confidence="medium"),
            EvaluationDimension(name="competitive_position", score=45, weight=0.15, explanation="Insufficient market data", confidence="low"),
            EvaluationDimension(name="technical_feasibility", score=50, weight=0.15, explanation="Technical approach not detailed", confidence="low"),
            EvaluationDimension(name="business_model", score=40, weight=0.10, explanation="Business model not described", confidence="low"),
            EvaluationDimension(name="adoption_barriers", score=45, weight=0.10, explanation="Cannot assess without customer context", confidence="low"),
            EvaluationDimension(name="team_requirements", score=50, weight=0.10, explanation="Not assessed", confidence="low"),
        ]
    return [
        EvaluationDimension(name="problem_pain", score=40, weight=0.15, explanation="Problem not clearly stated — cannot assess urgency", confidence="low"),
        EvaluationDimension(name="customer_clarity", score=25, weight=0.15, explanation="Customer not identified", confidence="low"),
        EvaluationDimension(name="solution_fit", score=40, weight=0.10, explanation="Solution too vague to evaluate fit", confidence="low"),
        EvaluationDimension(name="competitive_position", score=45, weight=0.15, explanation="Insufficient data to assess competition", confidence="low"),
        EvaluationDimension(name="technical_feasibility", score=45, weight=0.15, explanation="Technical approach not described", confidence="low"),
        EvaluationDimension(name="business_model", score=25, weight=0.10, explanation="Business model unknown", confidence="low"),
        EvaluationDimension(name="adoption_barriers", score=45, weight=0.10, explanation="Cannot assess without customer context", confidence="low"),
        EvaluationDimension(name="team_requirements", score=50, weight=0.10, explanation="Not assessed", confidence="low"),
    ]


def _fallback_evaluation(demand: DemandSignal, competitors: list[CompetitorEntry], input_quality: str = "poor") -> OverallEvaluation:
    demand_score = {"weak": 30, "moderate": 55, "strong": 80}.get(demand.strength, 50)
    comp_score = max(30, 80 - len(competitors) * 5)

    if input_quality == "good":
        dims = [
            EvaluationDimension(name="problem_pain", score=demand_score, weight=0.15, explanation=f"Demand signal suggests {demand.strength} market interest", confidence="medium"),
            EvaluationDimension(name="customer_clarity", score=55, weight=0.15, explanation="Customer partially described but needs specificity", confidence="medium"),
            EvaluationDimension(name="solution_fit", score=55, weight=0.10, explanation="Solution described, fit depends on execution", confidence="medium"),
            EvaluationDimension(name="competitive_position", score=comp_score, weight=0.15, explanation=f"Based on {len(competitors)} competitors found", confidence="medium"),
            EvaluationDimension(name="technical_feasibility", score=55, weight=0.15, explanation="Broadly feasible but risks unknown", confidence="low"),
            EvaluationDimension(name="business_model", score=35, weight=0.10, explanation="Business model not described", confidence="low"),
            EvaluationDimension(name="adoption_barriers", score=50, weight=0.10, explanation="Cannot fully assess without customer context", confidence="low"),
            EvaluationDimension(name="team_requirements", score=50, weight=0.10, explanation="Not assessed", confidence="low"),
        ]
        verdict = "narrow"
        summary = "Promising direction but needs more validation before committing resources."
    else:
        dims = [
            EvaluationDimension(name="problem_pain", score=demand_score, weight=0.15, explanation=f"Demand signal is {demand.strength}, but problem is unclear from input", confidence="low"),
            EvaluationDimension(name="customer_clarity", score=25, weight=0.15, explanation="Customer not identified in input", confidence="low"),
            EvaluationDimension(name="solution_fit", score=40, weight=0.10, explanation="Solution too vague to evaluate", confidence="low"),
            EvaluationDimension(name="competitive_position", score=comp_score, weight=0.15, explanation=f"Based on {len(competitors)} competitors found", confidence="low"),
            EvaluationDimension(name="technical_feasibility", score=45, weight=0.15, explanation="Technical approach not described", confidence="low"),
            EvaluationDimension(name="business_model", score=25, weight=0.10, explanation="Business model not described", confidence="low"),
            EvaluationDimension(name="adoption_barriers", score=45, weight=0.10, explanation="Cannot assess without customer context", confidence="low"),
            EvaluationDimension(name="team_requirements", score=50, weight=0.10, explanation="Not assessed", confidence="low"),
        ]
        verdict = "insufficient-info"
        summary = "Input lacks sufficient detail for a meaningful evaluation. Please specify customer, problem, and solution."

    overall = round(sum(d.score * d.weight for d in dims))
    return OverallEvaluation(
        dimensions=dims,
        overall_score=overall,
        reasoning=f"Assessment based on demand signal ({demand.strength}) and {len(competitors)} competitors. "
                  f"Input quality is {input_quality}. Key gaps remain in business model and customer definition.",
        recommendation=Recommendation(
            verdict=verdict,
            summary=summary,
            kill_criteria=["Unclear target audience", "Unvalidated business model", "Technical feasibility unknown"],
            next_steps=["Specify target customer", "Describe the problem in detail", "Explain why your solution is differentiated", "Research existing alternatives"],
        ),
    )
