"""Apify-powered search backend — Google SERP, Crunchbase, Reddit."""

import os
from app.search import SearchBackend, SearchResult

_APIFY_API_KEY: str | None = None


def _api_key() -> str:
    global _APIFY_API_KEY
    if _APIFY_API_KEY is None:
        _APIFY_API_KEY = os.environ.get("APIFY_API_KEY", "")
    return _APIFY_API_KEY


class ApifyGoogleBackend(SearchBackend):
    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        key = _api_key()
        if not key:
            return []
        from apify_client import ApifyClient
        client = ApifyClient(key)
        try:
            run = client.actor("nFJndsJwoQhpc2Q8w").call(
                run_input={"queries": query, "maxPagesPerQuery": 1, "resultsPerPage": max_results}
            )
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            return [
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                )
                for item in items[:max_results]
            ]
        except Exception:
            return []


class ApifyCrunchbaseBackend(SearchBackend):
    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        key = _api_key()
        if not key:
            return []
        from apify_client import ApifyClient
        client = ApifyClient(key)
        try:
            run = client.actor("o0C1JWM0mBcj5m4fD").call(
                run_input={"search": query, "maxItems": max_results}
            )
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            return [
                SearchResult(
                    title=item.get("name", item.get("title", "")),
                    url=item.get("url", item.get("cb_url", "")),
                    snippet=item.get("shortDescription", item.get("description", "")),
                )
                for item in items[:max_results]
            ]
        except Exception:
            return []


class ApifyRedditBackend(SearchBackend):
    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        key = _api_key()
        if not key:
            return []
        from apify_client import ApifyClient
        client = ApifyClient(key)
        try:
            run = client.actor("WU6J68FJ5O5dJ7F7C").call(
                run_input={"searchTerms": [query], "maxPosts": max_results}
            )
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            return [
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("text", item.get("selfText", "")),
                )
                for item in items[:max_results]
            ]
        except Exception:
            return []


class ApifyMultiBackend(SearchBackend):
    def __init__(self, backends: list[SearchBackend] | None = None):
        self._backends = backends or [
            ApifyGoogleBackend(),
            ApifyCrunchbaseBackend(),
            ApifyRedditBackend(),
        ]

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        seen_urls: set[str] = set()
        combined: list[SearchResult] = []
        for backend in self._backends:
            results = await backend.search(query, max_results)
            for r in results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    combined.append(r)
        return combined[:max_results]