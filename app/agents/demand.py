import json
import re
from langchain_ollama import ChatOllama
from app.schemas import DemandSignal, SourcedClaim, IntakeResult
from app.search import search_web


_DOMAIN_QUERY_PROMPT = """You are a market research expert. Given a startup idea, generate 5 web search queries that would find relevant market signals, trends, news, and discussions about this domain.

CRITICAL: Do NOT use the literal wording of the idea. Instead, extract the core domain and generate queries using standard industry terminology.

Example:
Idea: "AI-powered app that helps people track daily water intake"
Bad queries: "AI-powered water intake tracking app review", "water intake app alternative for people"
Good queries: "hydration tracking market trends 2025", "digital health consumer behavior", "health wellness app growth"

Idea: {problem}
Solution: {solution}
Category: {category}
Target user: {target_user}

Return ONLY a valid JSON array of 5 query strings. No other text.
JSON:"""

_CATEGORY_ALIASES = {
    "deep-tech": "deeptech",
    "enterprise-saas": "saas",
    "smb-saas": "saas",
}

_FALLBACK_CATEGORY_QUERIES = {
    "cleantech": [
        "battery technology innovation", "energy storage market growth",
        "renewable energy trends", "grid modernization AI",
        "clean technology funding",
    ],
    "fintech": [
        "digital banking trends 2025", "fintech payment solutions",
        "personal finance app market", "bnpl market growth",
        "neobank customer acquisition",
    ],
    "healthtech": [
        "digital health market trends", "telemedicine adoption 2025",
        "healthcare AI applications", "remote patient monitoring growth",
        "healthtech funding 2025",
    ],
    "saas": [
        "b2b saas market trends 2025", "enterprise software growth",
        "saas customer acquisition cost", "cloud software adoption",
        "business productivity tools market",
    ],
    "deeptech": [
        "materials informatics AI", "scientific machine learning",
        "deep tech research commercialization", "ai drug discovery market",
        "deep tech venture funding 2025",
    ],
    "ecommerce": [
        "ecommerce market growth 2025", "online shopping trends",
        "direct to consumer brands", "retail technology adoption",
        "ecommerce customer behavior",
    ],
}


async def _build_queries(intake: IntakeResult) -> list[str]:
    cat = (intake.category or "").lower()
    cat = _CATEGORY_ALIASES.get(cat, cat)

    if cat in _FALLBACK_CATEGORY_QUERIES:
        return _FALLBACK_CATEGORY_QUERIES[cat]

    try:
        llm = ChatOllama(model="qwen3:1.7b", temperature=0.3, num_predict=512)
        prompt = _DOMAIN_QUERY_PROMPT.format(
            problem=intake.problem_statement,
            solution=intake.proposed_solution,
            category=intake.category or "general",
            target_user=intake.target_user,
        )
        response = llm.invoke(prompt)
        text = response.content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        queries = json.loads(text)
        if isinstance(queries, list) and len(queries) >= 3:
            return [q.strip() for q in queries[:6] if q.strip()]
    except Exception:
        pass

    return _keyword_fallback_queries(intake.proposed_solution, intake.category)


def _keyword_fallback_queries(solution: str, category: str | None) -> list[str]:
    sol = _shorten(solution, 30)
    for prefix in ["i want to build ", "i want to create ", "build an ", "create a ", "develop a ",
                    "an ai-powered ", "a ", "an "]:
        if sol.lower().startswith(prefix):
            sol = sol[len(prefix):]
            break
    sol = _shorten(sol, 30)
    cat = category or ""
    queries = [
        f"{sol} market trends",
        f"{sol} industry",
    ]
    if cat:
        queries.append(f"{cat} {_shorten(sol, 20)}")
        queries.append(f"{cat} market size")
    queries.append(f"{sol} technology")
    return [q for q in queries if len(q) > 10 and q.split()[0] not in ("a", "an", "the")]


def _shorten(text: str, max_len: int = 40) -> str:
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: text.rfind(" ", 0, max_len)]


_DOMAIN_BLOCKLIST = [
    "wikipedia.org", "dictionary", "thesaurus", "synonym",
    "amazon.com", "wikihow.com", "britannica.com", "merriam",
]


def _is_relevant(text: str, url: str) -> bool:
    lower = (text + " " + url).lower()
    if any(d in lower for d in _DOMAIN_BLOCKLIST):
        return False
    return len(text) > 30


async def run_demand_signal(intake: IntakeResult) -> DemandSignal:
    queries = await _build_queries(intake)
    all_results = []
    for q in queries:
        results = await search_web(q, max_results=3)
        all_results.extend(results)

    seen_urls = set()
    evidence = []
    for r in all_results:
        if r.url in seen_urls:
            continue
        seen_urls.add(r.url)
        if not _is_relevant(r.snippet or r.title, r.url):
            continue
        evidence.append(
            SourcedClaim(
                text=r.snippet[:300] if r.snippet else r.title,
                source_url=r.url,
                source_name=r.title[:80] or r.url,
            )
        )

    strength = _classify_strength(evidence)
    return DemandSignal(evidence=evidence[:15], strength=strength)


def _classify_strength(evidence: list[SourcedClaim]) -> str:
    count = len(evidence)
    if count >= 8:
        return "strong"
    elif count >= 3:
        return "moderate"
    return "weak"
