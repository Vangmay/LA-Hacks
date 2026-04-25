from .base import BaseAgent, AgentContext, AgentResult


class RAGRetrievalAgent(BaseAgent):
    agent_id = "rag_retrieval"

    async def run(self, context: AgentContext) -> AgentResult:
        claim_id = context.claim.claim_id if context.claim else None
        return self._mock_result(claim_id=claim_id, output={
            "tier": "semantic",
            "status": "inconclusive",
            "evidence": "stub",
            "confidence": 0.5,
        })
