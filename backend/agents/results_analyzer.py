"""PoC mode stub."""
from .base import AgentContext, AgentResult, BaseAgent


class ResultsAnalyzerAgent(BaseAgent):
    agent_id = "results_analyzer"

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"results": []},
            confidence=0.5,
        )
