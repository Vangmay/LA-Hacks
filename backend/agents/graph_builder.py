"""Build a typed `ResearchGraph` over extracted atoms.

The agent asks the LLM for typed edges (`depends_on`, `uses_definition`,
`proof_step_for`, etc.). Edges that introduce a cycle in the
`DEPENDS_ON`/`uses_*` projection are dropped via the existing
`core/dag.py` Kahn-style detector. Roots and topological order are
computed only over the dependency projection so cascading reasons about
"if B fails, A is affected".
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Iterable, Optional

from openai import AsyncOpenAI

from config import settings
from core.dag import DAG
from core.openai_client import make_async_openai
from models import (
    DEPENDENCY_EDGE_TYPES,
    ResearchAtom,
    ResearchGraph,
    ResearchGraphEdge,
    ResearchGraphEdgeType,
)

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = (
    "You build dependency graphs over research atoms extracted from a "
    "theoretical paper. Output JSON only. Be conservative — only add an "
    "edge if you can name a concrete reason."
)

_USER_PROMPT_TMPL = """Atoms (id, type, section, snippet):
{atoms_block}

Allowed edge types (and meaning):
- depends_on: source needs target to be true.
- uses_definition: source's statement only makes sense given target's
  definition.
- uses_lemma: source's proof or argument relies on target.
- uses_assumption: source assumes target (an explicit assumption).
- proof_step_for: source is a step inside the proof of target.
- example_for: source is an example illustrating target.
- counterexample_to: source is a counterexample to target.
- generalizes: source is a strictly more general statement than target.
- special_case_of: source is a special case of target.
- motivates: source motivates target (no logical dependency).
- supports: source provides empirical or argumentative support for target.
- contradicts: source contradicts target.
- related_to: weak topical relation.

Edge convention:
"source_id depends_on target_id" means source REQUIRES target. Process
target first; if target is refuted, source is at risk.

Return:
{{
  "edges": [
    {{
      "source_id": "...",
      "target_id": "...",
      "edge_type": "...",
      "rationale": "<one short phrase>",
      "confidence": 0.0,
      "source_quote": "<optional verbatim quote from atom showing the link>"
    }}
  ],
  "warnings": []
}}

Rules:
- Use only the atom ids listed above.
- Never connect an atom to itself.
- Skip pairs that have no clear relation. Topical similarity is NOT enough.
- Output ONLY the JSON object.
"""


class GraphBuilderAgent(BaseAgent):
    agent_id = "graph_builder"

    def __init__(self, client: Optional[AsyncOpenAI] = None) -> None:
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = make_async_openai()
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        atoms: list[ResearchAtom] = list(context.extra.get("atoms") or [])
        if not atoms:
            return AgentResult(
                agent_id=self.agent_id,
                status="inconclusive",
                output={"graph": None},
                confidence=0.0,
                error="no atoms provided",
            )

        atom_ids = [atom.atom_id for atom in atoms]
        paper_id = atoms[0].paper_id
        warnings: list[str] = []

        try:
            raw_edges = await self._infer_edges(atoms)
        except Exception as exc:
            logger.exception("graph_builder LLM call failed")
            warnings.append(f"llm_edges_failed: {exc}")
            raw_edges = []

        edges = _build_edges(raw_edges, atom_ids, warnings)

        graph = _finalize_graph(
            paper_id=paper_id,
            atom_ids=atom_ids,
            edges=edges,
            warnings=warnings,
        )

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"graph": graph.model_dump()},
            confidence=0.85 if edges else 0.4,
        )

    async def _infer_edges(self, atoms: list[ResearchAtom]) -> list[dict[str, Any]]:
        atoms_block = "\n".join(
            f"- {atom.atom_id} ({atom.atom_type.value}, {atom.section_heading or 'n/a'}): "
            f"{_short(atom.text)}"
            for atom in atoms
        )
        prompt = _USER_PROMPT_TMPL.format(atoms_block=atoms_block)

        response = await self._get_client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        raw = response.choices[0].message.content or ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("graph_builder: JSON parse failed, returning no edges")
            return []
        edges = data.get("edges") if isinstance(data, dict) else None
        return edges or []


def _build_edges(
    raw_edges: Iterable[dict[str, Any]],
    atom_ids: list[str],
    warnings: list[str],
) -> list[ResearchGraphEdge]:
    valid_ids = set(atom_ids)
    edges: list[ResearchGraphEdge] = []
    seen: set[tuple[str, str, ResearchGraphEdgeType]] = set()
    counter = 0

    for raw in raw_edges:
        if not isinstance(raw, dict):
            continue
        source = (raw.get("source_id") or raw.get("from") or "").strip()
        target = (raw.get("target_id") or raw.get("to") or "").strip()
        if source == target:
            continue
        if source not in valid_ids or target not in valid_ids:
            warnings.append(f"edge with unknown atom: {source!r} -> {target!r}")
            continue
        edge_type = _coerce_edge_type(raw.get("edge_type"))
        if edge_type is None:
            warnings.append(f"unknown edge_type: {raw.get('edge_type')!r}")
            continue
        key = (source, target, edge_type)
        if key in seen:
            continue
        seen.add(key)
        counter += 1

        confidence = _coerce_confidence(raw.get("confidence"), default=0.6)
        edges.append(
            ResearchGraphEdge(
                edge_id=f"edge_{counter:03d}",
                source_id=source,
                target_id=target,
                edge_type=edge_type,
                rationale=str(raw.get("rationale") or ""),
                confidence=confidence,
                source_quote=raw.get("source_quote"),
            )
        )
    return edges


def _finalize_graph(
    *,
    paper_id: str,
    atom_ids: list[str],
    edges: list[ResearchGraphEdge],
    warnings: list[str],
) -> ResearchGraph:
    dag = DAG()
    for atom_id in atom_ids:
        dag.add_node(atom_id)

    accepted: list[ResearchGraphEdge] = []
    for edge in edges:
        if edge.edge_type not in DEPENDENCY_EDGE_TYPES:
            accepted.append(edge)
            continue
        # DAG semantics: edge from source -> target means source depends on target.
        dag.add_edge(edge.source_id, edge.target_id)
        if dag.has_cycle():
            dag.edges[edge.source_id].discard(edge.target_id)
            dag.reverse[edge.target_id].discard(edge.source_id)
            warnings.append(
                f"dropped cyclic edge {edge.source_id} -> {edge.target_id} ({edge.edge_type.value})"
            )
            continue
        accepted.append(edge)

    try:
        topo = dag.topological_sort()
    except ValueError:
        warnings.append("topological sort failed even after cycle removal")
        topo = atom_ids
    roots = dag.get_roots()

    return ResearchGraph(
        paper_id=paper_id,
        atom_ids=atom_ids,
        edges=accepted,
        roots=roots,
        topological_order=topo,
        warnings=warnings,
    )


def _coerce_edge_type(value: Any) -> Optional[ResearchGraphEdgeType]:
    if not isinstance(value, str):
        return None
    cleaned = value.strip().lower().replace("-", "_").replace(" ", "_")
    try:
        return ResearchGraphEdgeType(cleaned)
    except ValueError:
        weak_relation_synonyms = {
            "definition": ResearchGraphEdgeType.RELATED_TO,
            "technique": ResearchGraphEdgeType.RELATED_TO,
            "construction": ResearchGraphEdgeType.RELATED_TO,
            "algorithm": ResearchGraphEdgeType.RELATED_TO,
            "assertion": ResearchGraphEdgeType.RELATED_TO,
        }
        return weak_relation_synonyms.get(cleaned)


def _coerce_confidence(value: Any, default: float) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, f))


def _short(text: str, limit: int = 160) -> str:
    flat = re.sub(r"\s+", " ", text).strip()
    return flat[:limit] + ("…" if len(flat) > limit else "")
