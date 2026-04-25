"""Smoke test for DefenderAgent.

Usage (from backend/):
    python scripts/test_defender.py            # live OpenAI call (~$0.01)
    python scripts/test_defender.py --mock     # offline, mocked client

Live mode requires OPENAI_API_KEY in backend/.env.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import dotenv

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

dotenv.load_dotenv(BACKEND / ".env")

from agents.base import AgentContext
from agents.defender import DefenderAgent
from config import settings
from models import ClaimUnit


CLAIM = ClaimUnit(
    claim_id="claim_001",
    text="Self-attention has O(n^2) time and memory complexity per layer in the sequence length n.",
    claim_type="theorem",
    section="3.2",
    equations=[],
    citations=[],
    dependencies=[],
)

CHALLENGES = [
    {
        "challenge_id": "ch_1",
        "claim_id": "claim_001",
        "attacker_agent": "attacker",
        "challenge_text": (
            "For long sequences this is impractical compared to linear-attention "
            "variants like Performer or Linformer, so the claim's practical value is overstated."
        ),
        "supporting_evidence": [],
    },
    {
        "challenge_id": "ch_2",
        "claim_id": "claim_001",
        "attacker_agent": "attacker",
        "challenge_text": (
            "The O(n^2) bound hides a large constant factor from multi-head projections, "
            "so the asymptotic claim does not reflect real-world cost."
        ),
        "supporting_evidence": [],
    },
]


def _make_mock_client() -> MagicMock:
    fake = MagicMock()
    fake.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content=json.dumps(
                            {
                                "rebuttal_text": (
                                    "The complexity claim is asymptotic and stated per layer; "
                                    "linear-attention variants trade approximation error for speed "
                                    "and do not invalidate the bound for the architecture analyzed."
                                ),
                                "supporting_evidence": [
                                    "Section 3.2 explicitly scopes the result to standard self-attention.",
                                    "Theoretical complexity is independent of constant-factor hardware costs.",
                                ],
                            }
                        )
                    )
                )
            ]
        )
    )
    return fake


async def run(use_mock: bool) -> int:
    if use_mock:
        print("=== DefenderAgent (mocked client) ===")
        agent = DefenderAgent(client=_make_mock_client())
    else:
        if not settings.openai_api_key:
            print("OPENAI_API_KEY not set. Add it to backend/.env or run with --mock.")
            return 1
        print(f"=== DefenderAgent (live, model={settings.openai_model}) ===")
        agent = DefenderAgent()

    ctx = AgentContext(
        job_id="defender-smoke",
        claim=CLAIM,
        extra={"challenges": CHALLENGES},
    )

    print(f"  claim:      {CLAIM.text!r}")
    print(f"  challenges: {len(CHALLENGES)}")

    result = await agent.run(ctx)

    print(f"\n  status:     {result.status}")
    print(f"  confidence: {result.confidence}")
    print(f"  error:      {result.error}")

    rebuttals = result.output.get("rebuttals", [])
    print(f"  rebuttals:  {len(rebuttals)}")
    for r in rebuttals:
        snippet = (r.get("rebuttal_text") or "").replace("\n", " ")[:160]
        print(f"\n  [{r.get('challenge_id')}] {snippet}...")
        for ev in r.get("supporting_evidence", []):
            print(f"      - {ev[:120]}")

    challenge_ids = {c["challenge_id"] for c in CHALLENGES}
    rebuttal_ids = {r.get("challenge_id") for r in rebuttals}
    if challenge_ids != rebuttal_ids:
        print(f"\nFAIL: challenge_id mismatch. expected={challenge_ids} got={rebuttal_ids}")
        return 1
    if result.status != "success":
        print(f"\nFAIL: expected status=success, got {result.status}")
        return 1

    print("\nOK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use a mocked OpenAI client (no network, no API key needed).",
    )
    args = parser.parse_args()
    return asyncio.run(run(use_mock=args.mock))


if __name__ == "__main__":
    sys.exit(main())
