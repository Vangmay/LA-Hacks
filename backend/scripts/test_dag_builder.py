"""
Quick smoke-test for DAGBuilderAgent.
Run from the backend/ directory:

    python scripts/test_dag_builder.py
"""
import asyncio
import sys
import os
from pathlib import Path
import dotenv

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
dotenv.load_dotenv(BACKEND / ".env")

from agents.dag_builder import DAGBuilderAgent
from agents.base import AgentContext

MOCK_CLAIMS = [
    {
        "claim_id": "claim_001",
        "text": "For all n ≥ 1, the sum of the first n positive integers equals n(n+1)/2.",
        "claim_type": "theorem",
        "section": "2",
        "equations": ["eq_1"],
        "citations": [],
        "dependencies": [],
    },
    {
        "claim_id": "claim_002",
        "text": "The closed-form n(n+1)/2 can be derived by induction using the base case n=1.",
        "claim_type": "lemma",
        "section": "2",
        "equations": [],
        "citations": [],
        "dependencies": [],
    },
    {
        "claim_id": "claim_003",
        "text": "As a corollary, the average of the first n integers is (n+1)/2, which follows directly from claim_001.",
        "claim_type": "corollary",
        "section": "3",
        "equations": [],
        "citations": [],
        "dependencies": [],
    },
    {
        "claim_id": "claim_004",
        "text": "The sum formula generalizes: for an arithmetic sequence with first term a and common difference d, the sum of n terms is n/2 * (2a + (n-1)d). This builds on claim_001.",
        "claim_type": "proposition",
        "section": "4",
        "equations": ["eq_2"],
        "citations": [],
        "dependencies": [],
    },
]


async def main():
    agent = DAGBuilderAgent()
    context = AgentContext(
        job_id="test-job",
        extra={"claims": MOCK_CLAIMS},
    )

    print("Running DAGBuilderAgent on 4 mock claims...\n")
    result = await agent.run(context)

    print(f"Status    : {result.status}")
    print(f"Confidence: {result.confidence}")
    if result.error:
        print(f"Error     : {result.error}")
        return

    out = result.output
    print(f"\nEdges ({len(out['edges'])}):")
    for e in out["edges"]:
        print(f"  {e['from']} → {e['to']}")

    print(f"\nRoots: {out['roots']}")
    print(f"Topological order: {out['topological_order']}")

    print("\nAdjacency (claim → depends on):")
    for cid, deps in out["adjacency"].items():
        print(f"  {cid}: {deps or '(none)'}")

    print("\nBack-filled dependencies on claim dicts:")
    for c in MOCK_CLAIMS:
        print(f"  {c['claim_id']}: {c['dependencies']}")

    dag = out.get("dag")
    if dag:
        print(f"\nDAG.to_dict(): {dag.to_dict()}")


if __name__ == "__main__":
    asyncio.run(main())
