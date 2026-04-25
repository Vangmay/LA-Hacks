from .base import BaseAgent, AgentContext, AgentResult


class CounterexampleSearchAgent(BaseAgent):
    agent_id = "counterexample_search"

    async def run(self, context: AgentContext) -> AgentResult:
        claim_id = context.claim.claim_id if context.claim else None
        return self._mock_result(claim_id=claim_id, output={"challenges": []})
