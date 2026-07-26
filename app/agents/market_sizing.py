from app.schemas import MarketSizing, SourcedClaim, IntakeResult, CompetitorEntry
from app.search import search_web


def _build_queries(intake: IntakeResult) -> list[str]:
    solution = intake.proposed_solution
    problem = intake.problem_statement
    category = intake.category or ""

    core = _extract_core(solution, category)

    queries = [
        f"{core} market size",
        f"{core} industry growth",
        f"{core} market revenue",
    ]
    if category:
        queries.append(f"{category} market size billion")
        queries.append(f"{category} industry report 2025")
    queries.append(f"{_shorten(problem, 45)} market")

    return [q for q in queries if len(q) > 10]


def _extract_core(solution: str, category: str) -> str:
    s = solution.lower()
    for prefix in ["i want to build ", "i want to create ", "build an ", "create a ", "develop a ", "an ai-powered "]:
        if prefix in s:
            rest = s.split(prefix)[-1].strip()
            return _shorten(rest, 40)
    return category or _shorten(s, 40)


def _shorten(text: str, max_len: int) -> str:
    if not text or len(text) <= max_len:
        return text or ""
    return text[: text.rfind(" ", 0, max_len)]


async def run_market_sizing(
    intake: IntakeResult,
    competitors: list[CompetitorEntry] | None = None,
) -> MarketSizing:
    queries = _build_queries(intake)
    all_results = []
    for q in queries:
        results = await search_web(q, max_results=3)
        all_results.extend(results)

    seen_urls = set()
    basis = []
    for r in all_results:
        if r.url in seen_urls:
            continue
        seen_urls.add(r.url)
        snippet = r.snippet or r.title
        if len(snippet) < 40:
            continue
        basis.append(
            SourcedClaim(
                text=snippet[:300],
                source_url=r.url,
                source_name=r.title[:80] or r.url,
            )
        )

    summary = _build_estimate_summary(basis, competitors)
    confidence = "medium" if len(basis) >= 3 else "low"

    return MarketSizing(
        estimate_summary=summary,
        basis=basis[:8],
        confidence=confidence,
    )


def _build_estimate_summary(
    basis: list[SourcedClaim],
    competitors: list[CompetitorEntry] | None,
) -> str:
    comp_count = len(competitors) if competitors else 0
    funded_count = sum(1 for c in (competitors or []) if c.funding_signal)
    parts = [f"Directional estimate based on {len(basis)} public sources."]
    if comp_count > 0:
        parts.append(
            f"Identified {comp_count} competitor(s) in the space"
            f"{', including ' + str(funded_count) + ' with known funding' if funded_count else ''}."
        )
    parts.append(
        "No authoritative market report found — this estimate is directional, "
        "not a validated figure. Treat as low confidence."
    )
    return " ".join(parts)
