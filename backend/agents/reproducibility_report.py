from .base import BaseAgent, AgentContext, AgentResult


class ReproducibilityReportAgent(BaseAgent):
    agent_id = "reproducibility_report"

    async def run(self, context: AgentContext) -> AgentResult:
        return self._mock_result(output={"markdown": "# Mock reproducibility report"})
