from .base import BaseAgent, AgentContext, AgentResult


class SymbolicVerifierAgent(BaseAgent):
    agent_id = "symbolic_verifier"

    async def run(self, context: AgentContext) -> AgentResult:
        claim_id = context.claim.claim_id if context.claim else None
        return self._mock_result(claim_id=claim_id, output={
            "tier": "symbolic",
            "status": "inconclusive",
            "evidence": "stub",
            "confidence": 0.5,
        })
