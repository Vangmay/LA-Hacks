"""Offline ResearchGraph builder test with a mocked OpenAI client."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from agents.base import AgentContext  # noqa: E402
from agents.graph_builder import GraphBuilderAgent  # noqa: E402
from models import AtomImportance, ResearchAtom, ResearchAtomType, SourceSpan  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _atom(atom_id: str, atom_type: ResearchAtomType, text: str) -> ResearchAtom:
    return ResearchAtom(
        atom_id=atom_id,
        paper_id="mock-paper",
        atom_type=atom_type,
        text=text,
        section_heading="Main",
        source_span=SourceSpan(
            paper_id="mock-paper",
            raw_excerpt=text,
            match_confidence=1.0,
        ),
        extraction_confidence=1.0,
        importance=AtomImportance.HIGH,
    )


class _FakeCompletions:
    async def create(self, **_kwargs):
        payload = {
            "edges": [
                {
                    "source_id": "atom_002",
                    "target_id": "atom_001",
                    "edge_type": "uses_lemma",
                    "rationale": "the theorem invokes the lemma",
                    "confidence": 0.9,
                },
                {
                    "source_id": "atom_003",
                    "target_id": "atom_002",
                    "edge_type": "depends_on",
                    "rationale": "corollary follows from theorem",
                    "confidence": 0.8,
                },
            ],
            "warnings": [],
        }
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
        )


class _FakeOpenAI:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=_FakeCompletions())


async def main_async() -> None:
    atoms = [
        _atom("atom_001", ResearchAtomType.LEMMA, "For all n, a base identity holds."),
        _atom("atom_002", ResearchAtomType.THEOREM, "Using the lemma, the main result holds."),
        _atom("atom_003", ResearchAtomType.COROLLARY, "As a corollary, a special case holds."),
    ]
    result = await GraphBuilderAgent(client=_FakeOpenAI()).run(
        AgentContext(job_id="graph-test", extra={"atoms": atoms})
    )
    _assert(result.status == "success", f"graph builder failed: {result.error}")
    graph = result.output["graph"]
    _assert(len(graph["edges"]) == 2, f"wrong edge count: {graph}")
    _assert(graph["roots"] == ["atom_001"], f"wrong roots: {graph['roots']}")
    _assert(graph["topological_order"][0] == "atom_001", "topological order inverted")


def main() -> int:
    asyncio.run(main_async())
    print("ResearchGraph builder test OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
