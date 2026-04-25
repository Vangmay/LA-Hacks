import json
import logging
from typing import List, Optional

from openai import AsyncOpenAI

from config import settings
from core.dag import DAG
from .base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a mathematical dependency analyzer. "
    "Given a list of claims from a paper, determine which claims logically depend on which others. "
    "The repository DAG convention is: an edge A -> B means claim A depends on claim B, "
    "so B must be established before A. "
    'Return ONLY a JSON object with one key "edges" whose value is an array of dependency edges: '
    '[{"from": claim_id, "to": claim_id}] where \'from\' depends on \'to\'. '
    "Be conservative — only add an edge if the dependency is clear."
)


class DAGBuilderAgent(BaseAgent):
    agent_id = "dag_builder"

    def __init__(self, client: Optional[AsyncOpenAI] = None) -> None:
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        claims: List[dict] = context.extra.get("claims", [])
        if not claims:
            return AgentResult(
                agent_id=self.agent_id,
                status="inconclusive",
                output={"edges": [], "adjacency": {}, "roots": [], "topological_order": []},
                confidence=0.0,
                error="no claims provided",
            )

        claim_ids = [c["claim_id"] for c in claims]
        raw_edges = await self._infer_edges(claims)

        dag = DAG()
        for cid in claim_ids:
            dag.add_node(cid)

        added_edges = []
        for edge in raw_edges:
            frm, to = edge.get("from"), edge.get("to")
            if frm not in dag.nodes or to not in dag.nodes:
                logger.warning("dag_builder: skipping edge with unknown node (%s -> %s)", frm, to)
                continue
            dag.add_edge(frm, to)
            if dag.has_cycle():
                logger.warning("dag_builder: cycle detected adding edge %s -> %s, removing", frm, to)
                dag.edges[frm].discard(to)
                dag.reverse[to].discard(frm)
            else:
                added_edges.append({"from": frm, "to": to})

        topo = dag.topological_sort()
        roots = dag.get_roots()
        adjacency = {n: sorted(dag.edges[n]) for n in dag.nodes}

        # Update the dependencies field on each ClaimUnit dict with its incoming neighbors
        for claim in claims:
            cid = claim["claim_id"]
            claim["dependencies"] = sorted(dag.edges[cid])

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={
                "edges": added_edges,
                "adjacency": adjacency,
                "roots": roots,
                "topological_order": topo,
                "dag": dag,
            },
            confidence=0.85,
        )

    async def _infer_edges(self, claims: List[dict]) -> List[dict]:
        compact = [{"id": c["claim_id"], "text": c["text"]} for c in claims]
        user_prompt = json.dumps(compact, ensure_ascii=False)

        raw = await self._call_openai(user_prompt)
        if raw is None:
            return []

        try:
            parsed = json.loads(raw)
            edges = parsed.get("edges", [])
            if not isinstance(edges, list):
                raise ValueError("edges is not a list")
            return [e for e in edges if isinstance(e, dict) and "from" in e and "to" in e]
        except (json.JSONDecodeError, ValueError, AttributeError) as exc:
            logger.warning("dag_builder: failed to parse edges (%s), retrying", exc)
            raw2 = await self._call_openai(
                user_prompt + '\n\nReturn ONLY {"edges": [...]} — no prose, no markdown.'
            )
            if raw2 is None:
                return []
            try:
                parsed = json.loads(raw2)
                edges = parsed.get("edges", [])
                return [e for e in edges if isinstance(e, dict) and "from" in e and "to" in e]
            except Exception:
                logger.error("dag_builder: retry also failed, returning no edges")
                return []

    async def _call_openai(self, user_prompt: str):
        try:
            response = await self._get_client().chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=1000,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error("dag_builder: OpenAI call failed: %s", exc)
            return None
