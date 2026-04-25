from .base import BaseAgent, AgentContext, AgentResult


class VerdictAggregatorAgent(BaseAgent):
    agent_id = "verdict_aggregator"

    async def run(self, context: AgentContext) -> AgentResult:
        claim_id = context.claim.claim_id if context.claim else "claim_001"
        return self._mock_result(claim_id=claim_id, output={
            "claim_id": claim_id,
            "verdict": "SUPPORTED",
            "confidence": 0.8,
            "is_cascaded": False,
            "cascade_source": None,
            "challenges": [],
            "rebuttals": [],
            "verification_results": [],
        })
