"""PoC mode stub."""
from .base import AgentContext, AgentResult, BaseAgent

class MetricExtractorAgent(BaseAgent):
    agent_id = "metric_extractor"

    async def run(self, context: AgentContext) -> AgentResult:
        atom_id = context.atom.atom_id if context.atom else "atom_001"
        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={
                "spec_id": "spec_001",
                "atom_id": atom_id,
                "testability": "testable",
                "success_criteria": [],
                "failure_criteria": [],
            },
            confidence=0.5,
        )
"""PoC mode stub."""
from .base import AgentContext, AgentResult, BaseAgent


class MetricExtractorAgent(BaseAgent):
    agent_id = "metric_extractor"

    async def run(self, context: AgentContext) -> AgentResult:
        atom_id = context.atom.atom_id if context.atom else "atom_001"
        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={
                "spec_id": "spec_001",
                "atom_id": atom_id,
                "testability": "testable",
                "success_criteria": [],
                "failure_criteria": [],
            },
            confidence=0.5,
        )
