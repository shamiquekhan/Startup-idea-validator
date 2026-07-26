"""Derives risk flags dynamically from evidence data."""

from app.schemas import DemandSignal, MarketSizing, CompetitorEntry, IntakeResult


def derive_risks(
    intake: IntakeResult,
    demand: DemandSignal,
    competitors: list[CompetitorEntry],
    market_sizing: MarketSizing,
) -> list[str]:
    risks = []

    if demand.strength == "weak":
        risks.append(
            "Weak demand signal — limited public evidence that the problem "
            "is widely felt or actively discussed"
        )
    elif demand.strength == "moderate" and len(demand.evidence) < 5:
        risks.append(
            "Moderate but thin demand signal — only a few sources found; "
            "recommend primary research to validate"
        )

    if len(competitors) >= 5:
        risks.append(
            f"Crowded market — {len(competitors)} potential competitors "
            "identified; differentiation will be critical"
        )
    elif len(competitors) >= 3:
        risks.append(
            f"{len(competitors)} competitors found — moderate competition; "
            "clear positioning needed"
        )
    elif len(competitors) == 0:
        risks.append(
            "No direct competitors found — this may indicate a blue ocean "
            "opportunity OR that the problem isn't widely recognized yet"
        )

    if market_sizing.confidence == "low":
        risks.append(
            "Market size confidence is low — limited public data available; "
            "primary research recommended to size the opportunity"
        )

    cat = (intake.category or "").lower()
    regulatory_categories = {
        "fintech", "healthtech", "medtech", "biotech", "crypto",
        "blockchain", "legaltech", "insurtech", "proptech",
    }
    if cat in regulatory_categories:
        risks.append(
            f"Regulatory considerations for {cat} sector — verify compliance "
            "requirements early"
        )

    capital_intensive = {"deeptech", "cleantech", "biotech", "medtech", "manufacturing"}
    if cat in capital_intensive:
        risks.append(
            f"Capital-intensive sector ({cat}) — may require significant "
            "funding for R&D, equipment, or lab infrastructure before generating revenue"
        )

    if not risks:
        risks.append("No significant red flags identified from public data")

    return risks
