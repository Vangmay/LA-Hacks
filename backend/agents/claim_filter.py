"""PoC mode stub. Implementation lives in a future phase."""
from .base import AgentContext, AgentResult, BaseAgent


class ClaimFilterAgent(BaseAgent):
    agent_id = "claim_filter"

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"testable": [], "theoretical": [], "classifications": {}},
            confidence=0.5,
        )
