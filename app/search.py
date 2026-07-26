"""Shared search utility — free DuckDuckGo backend (via ddgs), structured for Apify swap-in."""

import asyncio
from typing import Protocol
from dataclasses import dataclass

from ddgs import DDGS
from ddgs.exceptions import DDGSException


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchBackend(Protocol):
    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        ...


class DuckDuckGoBackend:
    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        loop = asyncio.get_event_loop()
        try:
            results = await loop.run_in_executor(
                None, lambda: list(DDGS().text(query, max_results=max_results))
            )
        except (DDGSException, Exception):
            return []
        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("href", ""),
                snippet=r.get("body", ""),
            )
            for r in results
        ]


_current_backend: SearchBackend = DuckDuckGoBackend()


def set_backend(backend: SearchBackend):
    global _current_backend
    _current_backend = backend


async def search_web(query: str, max_results: int = 10) -> list[SearchResult]:
    try:
        return await _current_backend.search(query, max_results)
    except Exception:
        return []
