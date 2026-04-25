from .base import BaseAgent, AgentContext, AgentResult


class MetricExtractorAgent(BaseAgent):
    agent_id = "metric_extractor"

    async def run(self, context: AgentContext) -> AgentResult:
        claim_id = context.claim.claim_id if context.claim else "claim_001"
        return self._mock_result(claim_id=claim_id, output={
            "spec_id": "spec_001",
            "claim_id": claim_id,
            "testability": "testable",
            "success_criteria": [],
            "failure_criteria": [],
        })
