from .base import BaseAgent, AgentContext, AgentResult


class ReportAgent(BaseAgent):
    agent_id = "report_agent"

    async def run(self, context: AgentContext) -> AgentResult:
        return self._mock_result(output={"markdown": "# Mock Report"})
