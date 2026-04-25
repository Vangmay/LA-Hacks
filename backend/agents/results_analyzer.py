from .base import BaseAgent, AgentContext, AgentResult


class ResultsAnalyzerAgent(BaseAgent):
    agent_id = "results_analyzer"

    async def run(self, context: AgentContext) -> AgentResult:
        return self._mock_result(output={"results": [], "claim_statuses": {}})
