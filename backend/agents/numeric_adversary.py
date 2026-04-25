from .base import BaseAgent, AgentContext, AgentResult


class NumericAdversaryAgent(BaseAgent):
    agent_id = "numeric_adversary"

    async def run(self, context: AgentContext) -> AgentResult:
        claim_id = context.claim.claim_id if context.claim else None
        return self._mock_result(claim_id=claim_id, output={
            "tier": "numeric",
            "status": "inconclusive",
            "evidence": "stub",
            "confidence": 0.5,
        })
