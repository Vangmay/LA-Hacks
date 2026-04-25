"""PoC mode stub."""
from .base import AgentContext, AgentResult, BaseAgent


class ScaffoldGeneratorAgent(BaseAgent):
    agent_id = "scaffold_generator"

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"scaffold_files": {}, "readme": ""},
            confidence=0.5,
        )
