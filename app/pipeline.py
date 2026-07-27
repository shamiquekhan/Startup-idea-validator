import asyncio
import json
from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.schemas import (
    IntakeResult,
    DemandSignal,
    CompetitorEntry,
    MarketSizing,
    ViabilityScore,
    ValidationReport,
    OverallEvaluation,
    CompletenessResult,
)
from app.agents.intake import parse_intake
from app.agents.completeness import check_completeness
from app.agents.demand import run_demand_signal
from app.agents.competitor import run_competitor_discovery
from app.agents.market_sizing import run_market_sizing
from app.agents.scoring import evaluation_to_viability
from app.agents.risks import derive_risks
from app.agents.aggregator import aggregate
from app.agents.validator import validate_report
from app.agents.evaluator import evaluate
from app.agents.decision_support import generate_decision_support
from app.agents.plan_writer import draft_business_plan
from app.renderer import render_to_markdown
from caching.cache import load_cached, save_cache


class PipelineState(TypedDict):
    raw_idea: str
    intake: IntakeResult | None
    completeness: dict | None
    demand: DemandSignal | None
    competitors: list[CompetitorEntry] | None
    market_sizing: MarketSizing | None
    risks: list[str] | None
    viability: ViabilityScore | None
    evaluation: OverallEvaluation | None
    decision_support: dict | None
    business_plan_draft: str | None
    report: ValidationReport | None
    markdown: str | None
    unresolved_claims_stripped: int
    error: str | None


async def node_completeness(state: PipelineState) -> dict:
    result = await check_completeness(state["raw_idea"])
    return {"completeness": result}


def node_intake(state: PipelineState) -> dict:
    result = parse_intake(state["raw_idea"])
    return {"intake": result}


async def node_research(state: PipelineState) -> dict:
    intake = state["intake"]
    demand_task = run_demand_signal(intake)
    comp_task = run_competitor_discovery(intake)
    market_task = run_market_sizing(intake)

    demand, competitors, market_sizing = await asyncio.gather(
        demand_task, comp_task, market_task,
    )

    return {
        "demand": demand,
        "competitors": competitors,
        "market_sizing": market_sizing,
    }


async def node_evaluate(state: PipelineState) -> dict:
    evaluation = await evaluate(
        intake=state["intake"],
        demand=state["demand"],
        competitors=state.get("competitors", []),
        market_sizing=state["market_sizing"],
    )

    risks = derive_risks(
        intake=state["intake"],
        demand=state["demand"],
        competitors=state.get("competitors", []),
        market_sizing=state["market_sizing"],
        evaluation=evaluation,
    )

    viability = evaluation_to_viability(evaluation)
    return {"evaluation": evaluation, "viability": viability, "risks": risks}


def node_aggregate(state: PipelineState) -> dict:
    completeness_dict = state.get("completeness") or {}
    completeness_model = CompletenessResult(
        completeness_score=completeness_dict.get("completeness_score", 0),
        fields=completeness_dict.get("fields", {}),
        follow_up_questions=completeness_dict.get("follow_up_questions", []),
        summary=completeness_dict.get("summary", ""),
    )
    report = aggregate(
        intake=state["intake"],
        demand=state["demand"],
        competitors=state.get("competitors", []),
        market_sizing=state["market_sizing"],
        risks=state.get("risks", []),
        evaluation=state["evaluation"],
        completeness=completeness_model,
    )
    report.viability = state["viability"]
    return {"report": report}


async def node_decision_support(state: PipelineState) -> dict:
    ds = await generate_decision_support(
        intake=state["intake"],
        demand=state["demand"],
        competitors=state.get("competitors", []),
        market_sizing=state["market_sizing"],
        evaluation=state["evaluation"],
    )
    report = state["report"]
    report.decision_support = ds
    return {"decision_support": ds, "report": report}


def node_validate(state: PipelineState) -> dict:
    validated, stripped = validate_report(state["report"])
    return {"report": validated, "unresolved_claims_stripped": stripped}


async def node_plan_writer(state: PipelineState) -> dict:
    report = state["report"]
    draft = await draft_business_plan(report)
    report.business_plan_draft = draft
    return {"business_plan_draft": draft, "report": report}


def node_render(state: PipelineState) -> dict:
    md = render_to_markdown(state["report"])
    return {"markdown": md}


def build_pipeline() -> StateGraph:
    builder = StateGraph(PipelineState)

    builder.add_node("completeness", node_completeness)
    builder.add_node("intake", node_intake)
    builder.add_node("research", node_research)
    builder.add_node("evaluate", node_evaluate)
    builder.add_node("aggregate", node_aggregate)
    builder.add_node("decision_support", node_decision_support)
    builder.add_node("validate", node_validate)
    builder.add_node("plan_writer", node_plan_writer)
    builder.add_node("render", node_render)

    builder.set_entry_point("completeness")
    builder.add_edge("completeness", "intake")
    builder.add_edge("intake", "research")
    builder.add_edge("research", "evaluate")
    builder.add_edge("evaluate", "aggregate")
    builder.add_edge("aggregate", "decision_support")
    builder.add_edge("decision_support", "validate")
    builder.add_edge("validate", "plan_writer")
    builder.add_edge("plan_writer", "render")
    builder.add_edge("render", END)

    return builder.compile()


async def run_pipeline(raw_idea: str) -> PipelineState:
    cached = load_cached(raw_idea)
    if cached:
        report_data = cached.get("report")
        if report_data:
            return _state_from_cache(cached)

    # Clear stale cache to force fresh run
    save_cache(raw_idea, {"raw_idea": raw_idea, "markdown": "", "error": None, "report": None})

    graph = build_pipeline()
    initial = PipelineState(
        raw_idea=raw_idea,
        intake=None,
        demand=None,
        competitors=None,
        market_sizing=None,
        risks=None,
        viability=None,
        evaluation=None,
        business_plan_draft=None,
        report=None,
        markdown=None,
        unresolved_claims_stripped=0,
        error=None,
    )
    try:
        result = await asyncio.wait_for(graph.ainvoke(initial), timeout=250)
        save_cache(raw_idea, _state_to_cache(result))
        return result
    except asyncio.TimeoutError:
        return PipelineState(
            raw_idea=raw_idea,
            intake=None,
            completeness=None,
            demand=None,
            competitors=None,
            market_sizing=None,
            risks=None,
            viability=None,
            evaluation=None,
            decision_support=None,
            business_plan_draft=None,
            report=None,
            error="Pipeline timed out after 250 seconds. Try a simpler or more specific idea.",
            markdown="# Pipeline Timeout\n\nThe validation pipeline timed out. This can happen with very complex ideas combined with slow LLM inference. Try simplifying your idea description or providing more specific customer and solution details.",
            unresolved_claims_stripped=0,
        )


def _state_to_cache(state: PipelineState) -> dict:
    return {
        "raw_idea": state["raw_idea"],
        "markdown": state.get("markdown"),
        "unresolved_claims_stripped": state.get("unresolved_claims_stripped", 0),
        "error": state.get("error"),
        "report": state["report"].model_dump(mode="json") if state.get("report") else None,
    }


def _state_from_cache(cached: dict) -> PipelineState:
    report_data = cached.get("report")
    report = ValidationReport(**report_data) if report_data else None
    return PipelineState(
        raw_idea=cached["raw_idea"],
        intake=report.intake if report else None,
        demand=report.demand if report else None,
        competitors=report.competitors if report else None,
        market_sizing=report.market_sizing if report else None,
        risks=report.risks if report else None,
        viability=report.viability if report else None,
        evaluation=report.evaluation if report else None,
        business_plan_draft=report.business_plan_draft if report else None,
        report=report,
        markdown=cached.get("markdown"),
        unresolved_claims_stripped=cached.get("unresolved_claims_stripped", 0),
        error=cached.get("error"),
    )
