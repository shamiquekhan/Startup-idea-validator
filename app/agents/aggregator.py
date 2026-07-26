"""Evidence Aggregator — merges, deduplicates, and consolidates findings across agents."""

from app.schemas import (
    IntakeResult,
    DemandSignal,
    CompetitorEntry,
    MarketSizing,
    ValidationReport,
    OverallEvaluation,
    SourcedClaim,
    CompletenessResult,
)


def aggregate(
    intake: IntakeResult,
    demand: DemandSignal,
    competitors: list[CompetitorEntry],
    market_sizing: MarketSizing,
    risks: list[str],
    evaluation: OverallEvaluation | None = None,
    completeness: CompletenessResult | None = None,
) -> ValidationReport:
    demand = _dedup_demand(demand)
    competitors = _dedup_competitors(competitors)
    market_sizing = _dedup_market_sizing(market_sizing)

    return ValidationReport(
        intake=intake,
        demand=demand,
        competitors=competitors,
        market_sizing=market_sizing,
        risks=risks,
        evaluation=evaluation,
        business_plan_draft="",
        completeness=completeness,
    )


def _dedup_demand(demand: DemandSignal) -> DemandSignal:
    seen = set()
    unique = []
    for c in demand.evidence:
        key = c.source_url.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(c)
    return DemandSignal(evidence=unique, strength=demand.strength)


def _dedup_competitors(competitors: list[CompetitorEntry]) -> list[CompetitorEntry]:
    seen = set()
    unique = []
    for c in competitors:
        key = c.name.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def _dedup_market_sizing(market: MarketSizing) -> MarketSizing:
    seen = set()
    unique = []
    for c in market.basis:
        key = c.source_url.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(c)
    return MarketSizing(
        estimate_summary=market.estimate_summary,
        basis=unique,
        confidence=market.confidence,
    )
