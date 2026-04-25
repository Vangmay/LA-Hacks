from .base import BaseAgent, AgentContext, AgentResult


class CascadeAgent(BaseAgent):
    agent_id = "cascade"

    async def run(self, context: AgentContext) -> AgentResult:
        return self._mock_result(output={"updated_verdicts": {}})
