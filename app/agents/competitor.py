import asyncio
import json
import re
from app.model_config import get_llm_with_fallback as get_llm
from app.schemas import CompetitorEntry, IntakeResult
from app.search import search_web


_CATEGORY_ALIASES = {
    "deep-tech": "deeptech",
    "enterprise-saas": "saas",
    "smb-saas": "saas",
    "sales-tech": "sales-tech",
    "revops": "sales-tech",
}

_DOMAIN_COMPETITOR_QUERIES = {
    "cleantech": [
        "battery technology company",
        "energy storage startup",
        "renewable energy software platform",
        "clean tech",
    ],
    "fintech": [
        "fintech payment processing companies",
        "digital banking platform",
        "personal finance app",
    ],
    "healthtech": [
        "digital health platform company",
        "healthcare software vendor",
        "medical practice software",
    ],
    "legaltech": [
        "legal tech software company",
        "legal AI platform",
        "law practice management software",
    ],
    "edtech": [
        "edtech platform company",
        "learning management system",
        "education software vendor",
    ],
    "insurtech": [
        "insurtech company",
        "insurance software platform",
        "digital insurance provider",
    ],
    "proptech": [
        "proptech company",
        "real estate software platform",
        "property technology startup",
    ],
    "agtech": [
        "agriculture technology company",
        "precision farming software",
        "agtech startup",
    ],
    "saas": [
        "enterprise software companies",
        "b2b saas platform",
    ],
    "ecommerce": [
        "ecommerce platform companies",
        "online retail software",
    ],
    "deeptech": [
        "materials informatics platform",
        "ai scientific discovery startup",
        "deep tech ai company",
        "battery materials ai",
    ],
    "developer-tools": [
        "developer tools companies",
        "developer platform",
    ],
    "consumer-app": [
        "consumer app companies",
        "mobile app",
    ],
    "sales-tech": [
        "ai sdr platform",
        "sales engagement platform",
        "prospect research tool",
        "sales outreach automation",
        "revenue operations software",
        "crm automation tool",
        "sales copilot",
        "outbound sales assistant",
    ],
}


def _build_queries(intake: IntakeResult) -> list[str]:
    cat = (intake.category or "").lower()
    cat = _CATEGORY_ALIASES.get(cat, cat)
    sol = intake.proposed_solution
    prob = intake.problem_statement

    for prefix in ["i want to build ", "i want to create ", "build an ", "create a ", "develop a "]:
        if sol.lower().startswith(prefix):
            sol = sol[len(prefix):]

    for prefix in ["an ai-powered ", "a "]:
        if sol.lower().startswith(prefix):
            sol = sol[len(prefix):]

    if cat in _DOMAIN_COMPETITOR_QUERIES:
        queries = _DOMAIN_COMPETITOR_QUERIES[cat][:]
    else:
        queries = []

    sol_keywords = [w for w in sol.split()[:4] if w.lower() not in
                    ("a", "an", "the", "for", "to", "of", "in", "and", "that", "with", "using")]

    queries.append(" ".join(sol_keywords) if sol_keywords else sol[:30])

    queries.append(f"{' '.join(sol_keywords[:3])} vendor" if sol_keywords else f"{sol[:25]} vendor")

    if prob:
        prob_keywords = [w for w in prob.split()[:3] if w.lower() not in
                        ("a", "an", "the", "for", "to", "of", "in", "and", "that", "with", "using")]
        if prob_keywords:
            queries.append(f"{' '.join(prob_keywords)} solution")

    return [q for q in queries if len(q) > 10][:6]


def _shorten(text: str, max_len: int) -> str:
    if not text or len(text) <= max_len:
        return text or ""
    return text[: text.rfind(" ", 0, max_len)]


_COMPETITOR_CLASSIFY_PROMPT = """Startup domain: {domain}
Title: {title}
URL: {url}
Snippet: {snippet}

Is this an actual company in the same domain? Return ONLY valid JSON: {{"is_relevant_company": true/false, "company_name": "name or null", "reason": "10 words max"}}

Criteria for true: must be an actual company/product/startup (NOT a news article, blog, forum, directory, list, review, or research report). Must operate in the same domain as the startup.

JSON:"""


async def _classify_result(title: str, url: str, snippet: str, domain_context: str = "") -> tuple[bool, str | None]:
    if _is_blocklisted(url, title):
        return False, None

    try:
        llm = get_llm(model="qwen3:1.7b", temperature=0.1, num_predict=256)
        prompt = _COMPETITOR_CLASSIFY_PROMPT.format(
            domain=domain_context,
            title=title,
            url=url,
            snippet=(snippet or "")[:500],
        )
        response = llm.invoke(prompt)
        text = response.content.strip()
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            text = text[start:end+1]
        data = json.loads(text)
        if data.get("is_relevant_company"):
            name = data.get("company_name")
            if name and _looks_like_company_name(name):
                return True, name
        return False, None
    except Exception:
        return _heuristic_classify(title, url, domain_context)


def _is_blocklisted(url: str, title: str) -> bool:
    url_lower = url.lower()
    title_lower = title.lower()

    blocklisted_domains = {
        "google", "bing", "yahoo", "duckduckgo",
        "facebook", "twitter", "instagram", "linkedin", "youtube", "tiktok", "x.com",
        "wikipedia", "wikihow", "wikidata", "wikimedia",
        "amazon", "ebay", "etsy", "aliexpress", "alibaba",
        "reddit", "quora", "medium", "substack", "quora",
        "rense", "naturalnews", "infowars", "nypost", "dailymail",
        "crunchbase", "pitchbook", "cbinsights", "tracxn",
        "forbes", "fortune", "inc", "fastcompany",
        "venturebeat", "techcrunch",
        "reuters", "bloomberg", "wsj", "ft", "nytimes",
        "washingtonpost", "theguardian", "economist",
        "bbc", "cnn", "nbc", "cbs", "abc", "npr", "pbs",
        "cbc", "cnbc", "msnbc", "foxnews", "huffpost",
        "nature", "science", "cell", "elsevier", "springer", "arxiv",
        "ieee", "acm", "wiley", "tandfonline", "mdpi",
        "gov", "edu", "nih", "nsf", "doe", "nrel", "ornl", "lbl", "anl", "pnnl",
        "gartner", "forrester", "idc", "spglobal",
        "microsoft", "apple", "google", "ibm", "oracle", "salesforce", "sap", "aws",
        "github", "gitlab", "bitbucket",
        "producthunt", "betalist", "alternative", "alternativeto",
        "ycombinator", "ycombinator.com", "500", "techstars",
        "sequoiacap", "a16z", "andrewchen", "greylock", "benchmark",
        "investopedia", "nerdwallet", "bankrate", "creditkarma",
        "glassdoor", "indeed", "monster", "ziprecruiter",
        "similarweb", "semrush", "ahrefs", "moz",
        "statista", "grandviewresearch", "marketsandmarkets",
        "meticulousresearch", "sphericalinsights", "cervicornconsulting",
        "verifiedmarketresearch", "exactitudeconsultancy", "dataintelo",
        "startus-insights", "startus",
        "g2", "capterra", "trustpilot", "getapp",
        "f6s", "tracxn", "pitchbook", "cbinsights", "crunchbase",
        "linkedin", "zoominfo", "apollo", "lusha",
        "hubspot", "zendesk", "intercom",
        "cnet", "zdnet", "arstechnica", "engadget", "theverge",
        "sciencedaily", "phys", "eurekalert",
        "researchgate", "academia",
        "quora", "stackexchange", "stackoverflow",
        "slideshare", "scribd", "issuu",
        "eventbrite", "meetup",
        "pcworld", "pcmag", "techradar",
        "entrepreneur", "smallbiztrends",
        "toolify", "interestingengineering", "nationaldefensemagazine",
        "newmarketpitch", "intuitionlabs",
        "ensun", "aiwa-ai", "paradromics",
        "sifted", "dealroom", "pitchbook",
    }

    domain = _domain_from_url(url)
    if domain and domain in blocklisted_domains:
        return True

    non_company_title_indicators = [
        "definition", "synonym", "dictionary", "how to", "what is",
        "sign in", "log in", "homepage", "newsletter", "subscribe",
        "best ", "top ", " vs ", "alternative", "review",
        "list of", "directory", "ranking", "comparison",
    ]
    for ind in non_company_title_indicators:
        if ind in title_lower:
            return True

    if any(tld in url_lower for tld in (".gov", ".edu", ".org")):
        return True

    return False


def _heuristic_classify(title: str, url: str, domain_context: str = "") -> tuple[bool, str | None]:
    domain = _domain_from_url(url)
    if not domain or len(domain) <= 2:
        return False, None

    url_lower = url.lower()

    if _is_news_or_article_url(url):
        return False, None

    title_lower = title.lower()
    non_company_keywords = [
        "definition", "synonym", "how to", "what is",
        "sign in", "log in", "subscribe", "newsletter",
        "best ", "top ", " vs ", "alternatives", "alternative to",
        "list of", "directory", "ranking", "comparison",
        "review", "reviews", "price", "pricing",
        "forum", "thread", "discussion",
    ]
    for kw in non_company_keywords:
        if kw in title_lower:
            return False, None

    path = _url_path(url)
    is_homepage = path in ("", "/", "/index", "/index.html", "/home", "/en", "/us")
    is_company_page = is_homepage or any(
        path.startswith(p) for p in ("/products", "/solutions", "/about", "/company", "/platform")
    )

    if is_company_page:
        name = _extract_company_name_from_title(title, domain)
        if name:
            return True, name
        return True, domain.capitalize()

    return False, None


def _url_path(url: str) -> str:
    m = re.search(r"https?://[^/]+(/[^?#]*)", url)
    return m.group(1) if m else ""


def _extract_company_name_from_title(title: str, domain: str) -> str | None:
    title = title.split(" - ")[0].split(" | ")[0].split(": ")[0].strip()
    if title and len(title) > 1 and " " in title:
        return title
    return domain.capitalize()


def _is_news_or_article_url(url: str) -> bool:
    url_lower = url.lower()
    article_patterns = ["/news/", "/article/", "/blog/", "/story/", "/opinion/",
                        "/category/", "/tag/", "/author/", "/press-release/",
                        "/pr/", "/media/"]
    for pat in article_patterns:
        if pat in url_lower:
            return True
    if re.search(r"/\d{4}/\d{2}/", url_lower):
        return True
    return False


def _domain_from_url(url: str) -> str | None:
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if m:
        parts = m.group(1).split(".")
        return parts[-2] if len(parts) >= 2 else None
    return None


def _looks_like_company_name(name: str) -> bool:
    name = name.strip().strip(".")
    if len(name) < 2 or len(name) > 40:
        return False
    skip_words = {"how to", "what is", "why ", "the ", "best ", "top ",
                  "list of", "guide", "tutorial", "review", "definition", "example"}
    if any(name.lower().startswith(w) for w in skip_words):
        return False
    return True


async def run_competitor_discovery(intake: IntakeResult) -> list[CompetitorEntry]:
    queries = _build_queries(intake)
    all_results = []
    for q in queries:
        results = await search_web(q, max_results=5)
        all_results.extend(results)

    domain_context = f"{intake.problem_statement[:80]} / {intake.proposed_solution[:80]} / {intake.category or 'general'}"

    seen_urls = set()
    unique_results = []
    for r in all_results:
        if r.url not in seen_urls:
            seen_urls.add(r.url)
            unique_results.append(r)

    classifications = await asyncio.gather(*[
        _classify_result(r.title, r.url, r.snippet or "", domain_context)
        for r in unique_results
    ])

    entries: list[CompetitorEntry] = []
    for r, (is_company, name) in zip(unique_results, classifications):
        if not is_company:
            continue
        final_name = name or _simple_extract_name(r.title)
        if final_name and _looks_like_company_name(final_name):
            entries.append(
                CompetitorEntry(
                    name=final_name,
                    description=r.snippet[:300] or r.title,
                    funding_signal=None,
                    source_url=r.url,
                    is_verified_competitor=True,
                )
            )

    if entries:
        entries = await _enrich_competitors(entries, domain_context)
        entries = _filter_by_workflow_overlap(entries, intake)

    return _deduplicate(entries)[:12]


_COMPETITOR_ENRICH_PROMPT = """For each competitor below, infer their focus area, target customer, competitive weakness, and YOUR edge (why a customer would choose YOUR startup over this competitor). The weakness should be a specific relative positioning gap, not a generic criticism.

Domain context: {domain}

Return ONLY valid JSON as an array: [{{"name": "...", "focus_area": "...", "target_customer": "...", "weakness": "relative weakness vs your startup", "your_edge": "why customer chooses you"}}, ...]

Competitor list:
{competitors_json}

JSON:"""


async def _enrich_competitors(entries: list[CompetitorEntry], domain_context: str) -> list[CompetitorEntry]:
    if not entries:
        return entries

    competitors_json = json.dumps([
        {"name": e.name, "description": e.description}
        for e in entries
    ], indent=2)

    try:
        llm = get_llm(model="qwen3:1.7b", temperature=0.2, num_predict=1024)
        prompt = _COMPETITOR_ENRICH_PROMPT.format(
            domain=domain_context[:200],
            competitors_json=competitors_json,
        )
        response = llm.invoke(prompt)
        text = response.content.strip()
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            text = text[start:end+1]
        enriched = json.loads(text)

        name_map = {e.name: e for e in entries}
        for item in enriched:
            name = item.get("name", "")
            if name in name_map:
                name_map[name].focus_area = item.get("focus_area") or None
                name_map[name].target_customer = item.get("target_customer") or None
                name_map[name].weakness = item.get("weakness") or None
                name_map[name].your_edge = item.get("your_edge") or None
    except Exception:
        pass

    return entries


def _simple_extract_name(title: str) -> str | None:
    candidates = [title.split(" - ")[0].split(" | ")[0].split(": ")[0]]
    for c in candidates:
        cleaned = c.strip().strip(" -:|")
        if cleaned and len(cleaned) > 1:
            return cleaned
    return None


def _deduplicate(entries: list[CompetitorEntry]) -> list[CompetitorEntry]:
    seen = set()
    unique = []
    for e in entries:
        key = e.name.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def _filter_by_workflow_overlap(entries: list[CompetitorEntry], intake: IntakeResult) -> list[CompetitorEntry]:
    """Filter competitors to only those that actually overlap with the idea's workflow.

    Uses the idea's solution description to build a set of workflow keywords.
    A competitor passes if its focus_area, description, or name contains
    at least one workflow keyword from the startup's domain.
    """
    lower_solution = intake.proposed_solution.lower()
    lower_problem = intake.problem_statement.lower()

    keywords = set()
    for text in [lower_solution, lower_problem]:
        for kw in _WORKFLOW_KEYWORDS_BY_DOMAIN.get(intake.startup_type, []):
            if kw in text:
                keywords.add(kw)

    if not keywords:
        keywords.update(_WORKFLOW_KEYWORDS_BY_DOMAIN.get(intake.startup_type, []))

    if not keywords:
        return entries

    filtered = []
    for e in entries:
        search_text = " ".join(filter(None, [
            e.name or "",
            e.description or "",
            e.focus_area or "",
            e.target_customer or "",
        ])).lower()
        if any(kw in search_text for kw in keywords):
            filtered.append(e)

    if not filtered:
        return entries

    return filtered


_WORKFLOW_KEYWORDS_BY_DOMAIN: dict[str, list[str]] = {
    "sales-tech": [
        "lead", "prospect", "outreach", "email", "call", "crm",
        "sales engagement", "sdr", "revenue", "pipeline",
        "demo", "account", "contact", "client", "deal",
        "sales automation", "cold email", "sequencing",
    ],
    "revops": [
        "revenue", "quote", "crm", "forecast", "pipeline",
        "billing", "subscription", "contract",
    ],
    "deep-tech": [
        "material", "molecule", "compound", "chemical", "discovery",
        "simulation", "scientific", "r&d", "research",
    ],
    "legaltech": [
        "contract", "legal", "law", "case", "document",
        "compliance", "attorney", "court",
    ],
    "fintech": [
        "payment", "bank", "account", "transaction", "invoice",
        "card", "lending", "credit", "finance",
    ],
    "healthtech": [
        "patient", "clinical", "medical", "health", "doctor",
        "hospital", "ehr", "diagnostic",
    ],
    "enterprise-saas": [
        "workflow", "enterprise", "analytics", "dashboard",
        "compliance", "automation", "platform",
    ],
    "smb-saas": [
        "small business", "freelancer", "solo", "micro",
    ],
    "marketplace": [
        "marketplace", "buyer", "seller", "listing", "transaction",
    ],
    "ecommerce": [
        "shop", "store", "product", "order", "cart", "inventory",
    ],
    "consumer-app": [
        "social", "chat", "message", "friend", "community",
    ],
    "developer-tools": [
        "api", "sdk", "developer", "code", "deploy", "pipeline",
    ],
    "cleantech": [
        "energy", "solar", "battery", "carbon", "emission",
        "renewable", "grid", "sustainable",
    ],
    "biotech": [
        "drug", "protein", "genomic", "clinical trial", "lab",
    ],
    "edtech": [
        "course", "student", "teacher", "learning", "classroom",
    ],
    "insurtech": [
        "insurance", "policy", "claim", "underwriting",
    ],
    "proptech": [
        "property", "real estate", "rental", "tenant", "lease",
    ],
    "agtech": [
        "farm", "crop", "agriculture", "soil", "harvest",
    ],
    "hardware": [
        "device", "sensor", "hardware", "physical", "iot",
    ],
}
