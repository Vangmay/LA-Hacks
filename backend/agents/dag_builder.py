from .base import BaseAgent, AgentContext, AgentResult


class DAGBuilderAgent(BaseAgent):
    agent_id = "dag_builder"

    async def run(self, context: AgentContext) -> AgentResult:
        return self._mock_result(output={
            "edges": [],
            "adjacency": {},
            "roots": ["claim_001"],
            "topological_order": ["claim_001"],
        })
