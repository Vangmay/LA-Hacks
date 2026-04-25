from .base import BaseAgent, AgentContext, AgentResult


class CitationGapAgent(BaseAgent):
    agent_id = "citation_gap"

    async def run(self, context: AgentContext) -> AgentResult:
        claim_id = context.claim.claim_id if context.claim else None
        return self._mock_result(claim_id=claim_id, output={"challenges": []})
