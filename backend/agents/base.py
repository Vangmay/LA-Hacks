from abc import ABC, abstractmethod
from typing import Optional, Literal
from pydantic import BaseModel, Field

from models import ClaimUnit


class AgentContext(BaseModel):
    job_id: str
    claim: Optional[ClaimUnit] = None
    extra: dict = Field(default_factory=dict)


class AgentResult(BaseModel):
    agent_id: str
    claim_id: Optional[str] = None
    status: Literal["success", "error", "inconclusive"]
    output: dict
    confidence: float
    error: Optional[str] = None


class BaseAgent(ABC):
    agent_id: str = "base_agent"

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        ...

    def _mock_result(
        self,
        claim_id: Optional[str] = None,
        output: Optional[dict] = None,
    ) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim_id,
            status="success",
            output=output or {},
            confidence=0.5,
        )
