"""Executable tool runtime for live research deep-dives."""
from __future__ import annotations

import json
import math
import re
import asyncio
import random
import time
from pathlib import Path
from typing import Any

import httpx

from config import settings

from .tools import PAPER_FIELDS, PAPER_FIELDS_WITH_EMBEDDING, SEARCH_PAPER_FIELDS
from .workspace import WorkspaceManager


ARXIV_RE = re.compile(r"(?:arxiv\.org/(?:abs|pdf)/)?([0-9]{4}\.[0-9]{4,5})(?:v[0-9]+)?")
S2_BASE = "https://api.semanticscholar.org/graph/v1"
S2_DATASETS = "https://api.semanticscholar.org/datasets/v1"
SERPAPI_BASE = "https://serpapi.com/search"
NESTED_PAPER_FIELDS = (
    "paperId,title,abstract,year,publicationDate,authors,venue,"
    "citationCount,influentialCitationCount,url,fieldsOfStudy,s2FieldsOfStudy"
)


def _trim(value: Any, char_limit: int) -> Any:
    text = json.dumps(value, default=str)
    if len(text) <= char_limit:
        return value
    return {"truncated": True, "char_limit": char_limit, "prefix": text[:char_limit]}


def extract_arxiv_id(arxiv_url_or_id: str) -> str:
    match = ARXIV_RE.search(arxiv_url_or_id)
    if match:
        return match.group(1)
    cleaned = arxiv_url_or_id.strip().removeprefix("ARXIV:").removeprefix("arxiv:")
    if re.fullmatch(r"[0-9]{4}\.[0-9]{4,5}", cleaned):
        return cleaned
    raise ValueError(f"could not parse arXiv id from {arxiv_url_or_id!r}")


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def prefix_fields(prefix: str, fields: str) -> str:
    return ",".join(f"{prefix}.{field}" for field in fields.split(","))


def normalize_bulk_sort(sort_value: Any) -> str | None:
    if not sort_value:
        return None
    sort_text = str(sort_value).strip()
    if not sort_text or sort_text.lower() == "relevance":
        return None
    field = sort_text.split(":", 1)[0]
    if field not in {"paperId", "publicationDate", "citationCount"}:
        return None
    return sort_text


class ToolRuntime:
    def __init__(
        self,
        *,
        workspace: WorkspaceManager,
        http_timeout_seconds: float,
        result_char_limit: int,
        semantic_scholar_min_interval_seconds: float = 1.2,
        semantic_scholar_max_retries: int = 4,
        serpapi_max_requests: int = 50,
    ) -> None:
        self.workspace = workspace
        self.result_char_limit = result_char_limit
        self.semantic_scholar_min_interval_seconds = semantic_scholar_min_interval_seconds
        self.semantic_scholar_max_retries = semantic_scholar_max_retries
        self.serpapi_max_requests = serpapi_max_requests
        self._serpapi_requests_used = 0
        self._serpapi_lock = asyncio.Lock()
        self._s2_lock = asyncio.Lock()
        self._last_s2_request_at = 0.0
        self.client = httpx.AsyncClient(timeout=http_timeout_seconds, follow_redirects=True)

    def executable_tool_names(self) -> set[str]:
        names = {
            "resolve_arxiv_paper",
            "get_paper_metadata",
            "get_paper_tldr",
            "get_paper_embedding",
            "get_references",
            "get_citations",
            "paper_bulk_search",
            "paper_relevance_search",
            "batch_get_papers",
            "rank_candidates_by_specter2_similarity",
            "read_workspace_file",
            "read_workspace_markdown",
            "write_workspace_markdown",
            "append_workspace_markdown",
        }
        if self._serpapi_key():
            names.add("google_scholar_search")
        return names

    async def execute(self, tool_name: str, arguments: dict[str, Any], workspace_path: Path) -> Any:
        if tool_name not in self.executable_tool_names():
            raise ValueError(f"tool is not executable in live runtime: {tool_name}")
        method = getattr(self, f"_tool_{tool_name}", None)
        if method is None:
            raise ValueError(f"missing implementation for executable tool: {tool_name}")
        result = await method(arguments, workspace_path)
        return _trim(result, self.result_char_limit)

    async def aclose(self) -> None:
        await self.client.aclose()

    def _s2_headers(self) -> dict[str, str]:
        if settings.semantic_scholar_api_key:
            return {"x-api-key": settings.semantic_scholar_api_key}
        return {}

    def _serpapi_key(self) -> str:
        return settings.serpapi_api_key or settings.serp_api_key

    async def _s2_get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(1, self.semantic_scholar_max_retries + 1):
            await self._pace_s2()
            response = await self.client.get(
                f"{S2_BASE}{path}",
                params={k: v for k, v in params.items() if v is not None and v != ""},
                headers=self._s2_headers(),
            )
            if response.status_code != 429:
                response.raise_for_status()
                return response.json()
            if attempt == self.semantic_scholar_max_retries:
                response.raise_for_status()
            await asyncio.sleep(self._retry_after_seconds(response, attempt))
        raise RuntimeError("unreachable Semantic Scholar retry state")

    async def _s2_post(self, path: str, params: dict[str, Any], body: dict[str, Any]) -> Any:
        for attempt in range(1, self.semantic_scholar_max_retries + 1):
            await self._pace_s2()
            response = await self.client.post(
                f"{S2_BASE}{path}",
                params={k: v for k, v in params.items() if v is not None and v != ""},
                json=body,
                headers=self._s2_headers(),
            )
            if response.status_code != 429:
                response.raise_for_status()
                return response.json()
            if attempt == self.semantic_scholar_max_retries:
                response.raise_for_status()
            await asyncio.sleep(self._retry_after_seconds(response, attempt))
        raise RuntimeError("unreachable Semantic Scholar retry state")

    async def _pace_s2(self) -> None:
        async with self._s2_lock:
            elapsed = time.monotonic() - self._last_s2_request_at
            wait = self.semantic_scholar_min_interval_seconds - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_s2_request_at = time.monotonic()

    def _retry_after_seconds(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return max(float(retry_after), self.semantic_scholar_min_interval_seconds)
            except ValueError:
                pass
        base = max(self.semantic_scholar_min_interval_seconds, 1.0)
        jitter = random.uniform(0.0, 0.25 * base)
        return min(60.0, base * (2 ** (attempt - 1)) + jitter)

    async def _tool_resolve_arxiv_paper(self, arguments: dict[str, Any], _: Path) -> dict[str, Any]:
        arxiv_id = extract_arxiv_id(arguments["arxiv_url"])
        fields = arguments.get("fields") or PAPER_FIELDS
        paper = await self._s2_get(f"/paper/ARXIV:{arxiv_id}", {"fields": fields})
        return {
            "paper": paper,
            "canonical_paper_id": paper["paperId"],
            "arxiv_id": arxiv_id,
            "warnings": [],
        }

    async def _tool_get_paper_metadata(self, arguments: dict[str, Any], _: Path) -> dict[str, Any]:
        fields = arguments.get("fields") or PAPER_FIELDS
        paper = await self._s2_get(f"/paper/{arguments['paper_id']}", {"fields": fields})
        return {"paper": paper, "warnings": []}

    async def _tool_get_paper_tldr(self, arguments: dict[str, Any], _: Path) -> dict[str, Any]:
        paper = await self._s2_get(f"/paper/{arguments['paper_id']}", {"fields": "paperId,title,tldr"})
        return {"paper_id": paper.get("paperId", arguments["paper_id"]), "title": paper.get("title"), "tldr": paper.get("tldr")}

    async def _tool_get_paper_embedding(self, arguments: dict[str, Any], _: Path) -> dict[str, Any]:
        paper = await self._s2_get(f"/paper/{arguments['paper_id']}", {"fields": "paperId,embedding.specter_v2"})
        return {"paper_id": paper.get("paperId", arguments["paper_id"]), "embedding": paper.get("embedding")}

    async def _tool_get_references(self, arguments: dict[str, Any], _: Path) -> dict[str, Any]:
        data = await self._s2_get(
            f"/paper/{arguments['paper_id']}/references",
            {
                "fields": arguments.get("fields") or prefix_fields("citedPaper", NESTED_PAPER_FIELDS),
                "limit": arguments.get("limit", 50),
                "offset": arguments.get("offset", 0),
            },
        )
        return {
            "references": data.get("data", []),
            "total": data.get("total"),
            "next_token": data.get("next"),
            "warnings": [],
        }

    async def _tool_get_citations(self, arguments: dict[str, Any], _: Path) -> dict[str, Any]:
        data = await self._s2_get(
            f"/paper/{arguments['paper_id']}/citations",
            {
                "fields": arguments.get("fields") or prefix_fields("citingPaper", NESTED_PAPER_FIELDS),
                "limit": arguments.get("limit", 50),
                "offset": arguments.get("offset", 0),
            },
        )
        return {
            "citations": data.get("data", []),
            "total": data.get("total"),
            "next_token": data.get("next"),
            "warnings": [],
        }

    async def _tool_paper_bulk_search(self, arguments: dict[str, Any], _: Path) -> dict[str, Any]:
        params = dict(arguments)
        params["fields"] = SEARCH_PAPER_FIELDS
        normalized_sort = normalize_bulk_sort(params.get("sort"))
        if normalized_sort:
            params["sort"] = normalized_sort
        else:
            params.pop("sort", None)
        params.setdefault("limit", 25)
        data = await self._s2_get("/paper/search/bulk", params)
        return {
            "papers": data.get("data", []),
            "total": data.get("total"),
            "next_token": data.get("token"),
            "warnings": [],
        }

    async def _tool_paper_relevance_search(self, arguments: dict[str, Any], _: Path) -> dict[str, Any]:
        params = dict(arguments)
        params.setdefault("fields", PAPER_FIELDS)
        params.setdefault("limit", 10)
        data = await self._s2_get("/paper/search", params)
        return {
            "papers": data.get("data", []),
            "total": data.get("total"),
            "next_token": data.get("next"),
            "warnings": [],
        }

    async def _tool_batch_get_papers(self, arguments: dict[str, Any], _: Path) -> dict[str, Any]:
        ids = arguments.get("ids") or []
        if not ids:
            raise ValueError("batch_get_papers requires non-empty ids")
        fields = arguments.get("fields") or PAPER_FIELDS_WITH_EMBEDDING
        papers = await self._s2_post("/paper/batch", {"fields": fields}, {"ids": ids[:500]})
        return {"papers": papers, "warnings": []}

    async def _tool_rank_candidates_by_specter2_similarity(self, arguments: dict[str, Any], workspace_path: Path) -> dict[str, Any]:
        seed = await self._tool_get_paper_metadata(
            {"paper_id": arguments["seed_paper_id"], "fields": "paperId,title,embedding.specter_v2"},
            workspace_path,
        )
        seed_embedding = (seed["paper"].get("embedding") or {}).get("vector")
        if not seed_embedding:
            raise ValueError(f"missing SPECTER2 seed embedding for {arguments['seed_paper_id']}")
        candidates = await self._tool_batch_get_papers(
            {"ids": arguments["candidate_paper_ids"], "fields": PAPER_FIELDS_WITH_EMBEDDING},
            workspace_path,
        )
        ranked: list[dict[str, Any]] = []
        missing: list[str] = []
        for paper in candidates["papers"]:
            if not paper:
                continue
            embedding = (paper.get("embedding") or {}).get("vector")
            if not embedding:
                missing.append(paper.get("paperId", "unknown"))
                continue
            item = {
                "paperId": paper.get("paperId"),
                "title": paper.get("title"),
                "year": paper.get("year"),
                "citationCount": paper.get("citationCount"),
                "url": paper.get("url"),
                "bucket": arguments.get("bucket", ""),
                "semantic_similarity": cosine(seed_embedding, embedding),
            }
            ranked.append(item)
        ranked.sort(key=lambda item: item["semantic_similarity"], reverse=True)
        return {"ranked_candidates": ranked, "missing_embeddings": missing}

    async def _tool_google_scholar_search(self, arguments: dict[str, Any], _: Path) -> dict[str, Any]:
        serpapi_key = self._serpapi_key()
        if not serpapi_key:
            raise RuntimeError("SERPAPI_API_KEY is required for google_scholar_search")
        async with self._serpapi_lock:
            if self._serpapi_requests_used >= self.serpapi_max_requests:
                raise RuntimeError(
                    f"SerpAPI request budget exhausted: "
                    f"{self._serpapi_requests_used}/{self.serpapi_max_requests}"
                )
            self._serpapi_requests_used += 1
        params = dict(arguments)
        query = params.pop("query")
        params.update({"engine": "google_scholar", "q": query, "api_key": serpapi_key})
        response = await self.client.get(SERPAPI_BASE, params={k: v for k, v in params.items() if v is not None and v != ""})
        response.raise_for_status()
        data = response.json()
        return {
            "organic_results": data.get("organic_results", []),
            "search_information": data.get("search_information", {}),
            "citations_per_year": data.get("citations_per_year", []),
        }

    async def _tool_read_workspace_file(self, arguments: dict[str, Any], workspace_path: Path) -> dict[str, Any]:
        content, line_count = self.workspace.read_owned_text(
            workspace_path,
            arguments["path"],
            start_line=arguments.get("start_line", 1),
            end_line=arguments.get("end_line"),
        )
        return {"content": content, "line_count": line_count}

    async def _tool_read_workspace_markdown(self, arguments: dict[str, Any], workspace_path: Path) -> dict[str, Any]:
        return await self._tool_read_workspace_file(arguments, workspace_path)

    async def _tool_write_workspace_markdown(self, arguments: dict[str, Any], workspace_path: Path) -> dict[str, Any]:
        path = self.workspace.write_owned_markdown(workspace_path, arguments["path"], arguments["content"])
        return {"path": str(path.resolve().relative_to(workspace_path.resolve()))}

    async def _tool_append_workspace_markdown(self, arguments: dict[str, Any], workspace_path: Path) -> dict[str, Any]:
        path = self.workspace.append_owned_markdown(
            workspace_path,
            arguments["path"],
            arguments["content"],
            heading=arguments.get("heading", ""),
        )
        return {"path": str(path.resolve().relative_to(workspace_path.resolve()))}
