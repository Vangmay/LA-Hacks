from .base import BaseAgent, AgentContext, AgentResult


class ClaimFilterAgent(BaseAgent):
    agent_id = "claim_filter"

    async def run(self, context: AgentContext) -> AgentResult:
        return self._mock_result(output={
            "testable": ["claim_001"],
            "theoretical": [],
            "classifications": {},
        })
