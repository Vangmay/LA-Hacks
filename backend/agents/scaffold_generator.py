from .base import BaseAgent, AgentContext, AgentResult


class ScaffoldGeneratorAgent(BaseAgent):
    agent_id = "scaffold_generator"

    async def run(self, context: AgentContext) -> AgentResult:
        return self._mock_result(output={
            "scaffold_files": {"README.md": "# Mock scaffold"},
            "readme": "Mock",
        })
