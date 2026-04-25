"""PrerequisiteMapperAgent — identify external concepts needed to understand an atom.

Wikipedia URLs returned by the LLM are validated with a HEAD request;
404s are replaced with the Wikipedia search URL for that concept.
"""
from __future__ import annotations

import json
import logging
from typing import Optional
from urllib.parse import quote

import httpx
from openai import AsyncOpenAI

from config import settings
from core.openai_client import make_async_openai
from models import CitationEntry

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Identify mathematical concepts from OUTSIDE this paper that a reader needs "
    "to understand the given research atom. For each concept provide: concept name, "
    "one-sentence description, and 1-2 resource links. For resource links, use real "
    "Wikipedia URLs (https://en.wikipedia.org/wiki/[Topic]) for fundamental concepts. "
    "Return a JSON object with key 'prerequisites' containing an array of objects, "
    "each with fields: concept (str), description (str), resource_links ([str])."
)

_WIKI_SEARCH = "https://en.wikipedia.org/wiki/Special:Search?search={query}"


async def _validate_url(client: httpx.AsyncClient, url: str, concept: str) -> str:
    try:
        r = await client.head(url, follow_redirects=True, timeout=5.0)
        if r.status_code == 404:
            return _WIKI_SEARCH.format(query=quote(concept))
    except Exception:
        return _WIKI_SEARCH.format(query=quote(concept))
    return url


def _citation_links(citations: list[CitationEntry]) -> list[str]:
    """Prefer source-paper references before general web resources."""
    links: list[str] = []
    seen: set[str] = set()

    def add(url: str | None) -> None:
        clean = (url or "").strip()
        if not clean or clean in seen:
            return
        seen.add(clean)
        links.append(clean)

    for citation in citations:
        add(citation.url)
        if citation.doi:
            doi = citation.doi.strip()
            if doi:
                add(doi if doi.startswith("http") else f"https://doi.org/{doi}")

    return links


class PrerequisiteMapperAgent(BaseAgent):
    agent_id = "prerequisite_mapper"

    def __init__(self, client: Optional[AsyncOpenAI] = None) -> None:
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = make_async_openai()
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        atom = context.atom
        if atom is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"prerequisites": []},
                confidence=0.0,
                error="atom missing from context",
            )

        user_content = (
            f"Atom type: {atom.atom_type.value}\n"
            f"Section: {atom.section_heading or 'unknown'}\n\n"
            f"Atom text:\n{atom.text}"
        )

        try:
            response = await self._get_client().chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            raw = response.choices[0].message.content or ""
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"prerequisites": []},
                confidence=0.0,
                error=f"json_parse_failed: {exc}",
            )
        except Exception as exc:
            logger.exception("PrerequisiteMapperAgent LLM call failed")
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"prerequisites": []},
                confidence=0.0,
                error=str(exc),
            )

        prereqs = data.get("prerequisites") if isinstance(data, dict) else None
        if not isinstance(prereqs, list):
            prereqs = []

        source_links = _citation_links(atom.citations)

        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as http:
            validated: list[dict] = []
            for p in prereqs:
                if not isinstance(p, dict):
                    continue
                concept = str(p.get("concept", ""))
                description = str(p.get("description", ""))
                raw_links = p.get("resource_links") or []
                if not isinstance(raw_links, list):
                    raw_links = []

                good_links: list[str] = []
                for link in raw_links:
                    if isinstance(link, str) and link.startswith("http"):
                        good_links.append(await _validate_url(http, link, concept))
                ordered_links = list(dict.fromkeys(source_links + good_links))

                validated.append(
                    {
                        "concept": concept,
                        "description": description,
                        "resource_links": ordered_links,
                    }
                )

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"prerequisites": validated},
            confidence=0.85,
        )
