"""Run multiple sample ideas through the pipeline and print summary stats."""

import asyncio
from app.pipeline import run_pipeline


IDEAS = [
    # Strong idea — clear problem, existing demand
    (
        "freelance-expense-tracker",
        "Small businesses waste hours manually tracking expenses across multiple bank accounts. "
        "Building an expense tracker that auto-categorizes transactions and generates reports. "
        "Target: freelancers and micro-businesses."
    ),
    # Crowded space — project management
    (
        "remote-pm-tool",
        "Remote teams struggle to keep track of who is working on what. "
        "A visual project management tool integrating with Slack showing real-time progress. "
        "Target: distributed tech teams of 5-20 people."
    ),
    # Niche idea — specific audience
    (
        "vegan-meal-planning",
        "Vegans and vegetarians find it hard to plan balanced meals that meet nutritional needs. "
        "A meal planning app with nutrition tracking and grocery list generation. "
        "Target: health-conscious vegans and vegetarians."
    ),
    # Weak/vague idea
    (
        "social-app",
        "A social network app that uses AI to connect people with similar interests. "
        "Target: young adults."
    ),
    # Local service
    (
        "pet-sitting",
        "Pet owners in cities struggle to find trusted pet sitters on short notice. "
        "An on-demand pet sitting marketplace with background checks and reviews. "
        "Target: urban pet owners aged 25-45."
    ),
]


async def main():
    for name, idea in IDEAS:
        print(f"\n{'='*60}")
        print(f"  {name}")
        print(f"{'='*60}")
        try:
            result = await run_pipeline(idea)
            r = result
            print(f"  Score:       {r['viability'].score}/100")
            print(f"  Demand:      {len(r['demand'].evidence)} evidence ({r['demand'].strength})")
            print(f"  Competitors: {len(r['competitors'])} found")
            if r['competitors']:
                print(f"  Names:       {', '.join(c.name for c in r['competitors'][:5])}")
            print(f"  Market:      {len(r['market_sizing'].basis)} sources ({r['market_sizing'].confidence})")
            print(f"  Risks:       {len(r['risks'])} flags")
            for risk in r['risks']:
                print(f"               - {risk[:90]}...")
            print(f"  Stripped:    {r['unresolved_claims_stripped']}")
            print(f"  Report:      {len(r['markdown'])} chars")
        except Exception as e:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
