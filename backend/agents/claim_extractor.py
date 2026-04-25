from .base import BaseAgent, AgentContext, AgentResult


class ClaimExtractorAgent(BaseAgent):
    agent_id = "claim_extractor"

    async def run(self, context: AgentContext) -> AgentResult:
        return self._mock_result(output={
            "claims": [{
                "claim_id": "claim_001",
                "text": "Mock theorem",
                "claim_type": "theorem",
                "section": "1",
                "equations": [],
                "citations": [],
                "dependencies": [],
            }],
        })
