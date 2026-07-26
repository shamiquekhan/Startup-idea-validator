import json
import re
from langchain_ollama import ChatOllama
from app.schemas import CompetitorEntry, IntakeResult
from app.search import search_web


_DOMAIN_COMPETITOR_QUERIES = {
    "cleantech": [
        "energy grid optimization company",
        "grid management software vendors",
        "utility demand response platform",
        "renewable energy software",
    ],
    "fintech": [
        "fintech payment processing companies",
        "digital banking platform",
        "personal finance app",
    ],
    "healthtech": [
        "healthtech companies digital health",
        "telemedicine platform vendors",
        "healthcare software",
    ],
    "enterprise-saas": [
        "enterprise software companies",
        "b2b saas platform",
    ],
    "smb-saas": [
        "small business software tools",
        "saas for freelancers",
        "business management software",
    ],
    "ecommerce": [
        "ecommerce platform companies",
        "online retail software",
    ],
    "deeptech": [
        "ai ml platform companies",
        "deep tech startup",
    ],
    "developer-tools": [
        "developer tools companies",
        "developer platform",
    ],
    "consumer-app": [
        "consumer app companies",
        "mobile app",
    ],
}


def _build_queries(intake: IntakeResult) -> list[str]:
    cat = (intake.category or "").lower()
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


_COMPETITOR_CLASSIFY_PROMPT = """You are a startup analyst. Given a search result and the startup's domain, determine if this is an actual company operating in a related space.

Startup domain: {domain}
Title: {title}
URL: {url}
Snippet: {snippet}

Return ONLY valid JSON:
{"is_relevant_company": true/false, "company_name": "extracted name or null", "reason": "brief justification"}

Criteria for is_relevant_company = true:
- Must be an actual company, product, or startup (not a news article, blog, forum, directory, list, or review site)
- Must operate in the same or adjacent domain as the startup (not SEO tools if the startup is energy grid)
- Company name should be recognizable (not a generic term)

JSON:"""


async def _classify_result(title: str, url: str, snippet: str, domain_context: str = "") -> tuple[bool, str | None]:
    if _is_blocklisted(url, title):
        return False, None

    try:
        llm = ChatOllama(model="qwen3:1.7b", temperature=0.1, num_predict=256)
        prompt = _COMPETITOR_CLASSIFY_PROMPT.format(
            domain=domain_context,
            title=title,
            url=url,
            snippet=snippet[:500],
        )
        response = llm.invoke(prompt)
        text = response.content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
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
        "g2", "capterra", "trustpilot", "getapp",
        "hubspot", "zendesk", "intercom",
        "cnet", "zdnet", "arstechnica", "engadget", "theverge",
        "sciencedaily", "phys", "eurekalert",
        "researchgate", "academia",
        "quora", "stackexchange", "stackoverflow",
        "slideshare", "scribd", "issuu",
        "eventbrite", "meetup",
        "pcworld", "pcmag", "techradar",
        "entrepreneur", "smallbiztrends",
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
        results = await search_web(q, max_results=8)
        all_results.extend(results)

    domain_context = f"{intake.problem_statement[:80]} / {intake.proposed_solution[:80]} / {intake.category or 'general'}"

    seen_urls = set()
    entries: list[CompetitorEntry] = []
    for r in all_results:
        if r.url in seen_urls:
            continue
        seen_urls.add(r.url)
        is_company, name = await _classify_result(r.title, r.url, r.snippet or "", domain_context)
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

    return _deduplicate(entries)[:12]


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
