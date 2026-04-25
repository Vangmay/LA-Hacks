"""PoC mode stub."""
from .base import AgentContext, AgentResult, BaseAgent

class ReproducibilityReportAgent(BaseAgent):
    agent_id = "reproducibility_report"

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"markdown_report": "# Reproducibility Report"},
            confidence=0.5,
        )
"""PoC mode stub."""
from .base import AgentContext, AgentResult, BaseAgent


class ReproducibilityReportAgent(BaseAgent):
    agent_id = "reproducibility_report"

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"markdown_report": "# Reproducibility Report"},
            confidence=0.5,
        )
