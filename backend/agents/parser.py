from .base import BaseAgent, AgentContext, AgentResult


class ParserAgent(BaseAgent):
    agent_id = "parser"

    async def run(self, context: AgentContext) -> AgentResult:
        return self._mock_result(output={
            "title": "Mock Paper",
            "sections": [],
            "equations": [],
            "bibliography": [],
            "raw_text": "",
        })
