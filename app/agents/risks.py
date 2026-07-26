"""Derives risk flags dynamically from evidence data."""

from app.schemas import DemandSignal, MarketSizing, CompetitorEntry, IntakeResult

_CATEGORY_ALIASES = {
    "deep-tech": "deeptech",
    "enterprise-saas": "saas",
    "smb-saas": "saas",
}


def derive_risks(
    intake: IntakeResult,
    demand: DemandSignal,
    competitors: list[CompetitorEntry],
    market_sizing: MarketSizing,
) -> list[str]:
    risks = []
    cat = (intake.category or "").lower()
    cat = _CATEGORY_ALIASES.get(cat, cat)

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
        if cat in ("deeptech", "cleantech", "biotech", "medtech"):
            risks.append(
                "No competitors found in search — likely a retrieval gap rather than a "
                "blue ocean; deep-tech markets typically have active competition"
            )
        else:
            risks.append(
                "No direct competitors found — this may indicate a blue ocean "
                "opportunity OR that the problem isn't widely recognized yet"
            )

    if market_sizing.confidence == "low":
        risks.append(
            "Market size confidence is low — limited public data available; "
            "primary research recommended to size the opportunity"
        )

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
            "Capital-intensive sector — may require significant "
            "funding for R&D, equipment, or lab infrastructure before generating revenue"
        )

    deep_tech_categories = {"deeptech", "cleantech", "biotech", "medtech"}
    if cat in deep_tech_categories:
        risks.append(
            "Long enterprise sales cycles — deep-tech products often require "
            "lengthy procurement, pilots, and validation before purchase decisions"
        )
        risks.append(
            "Experimental validation cost — scientific/technical claims need "
            "real-world proof, which is expensive and time-consuming"
        )
        if intake.target_user in ("not specified", "unknown", ""):
            risks.append(
                "Customer not identified — deep-tech solutions need a specific "
                "buyer; without one, product-market fit is uncertain"
            )

    if not risks:
        risks.append("No significant red flags identified from public data")

    return risks
