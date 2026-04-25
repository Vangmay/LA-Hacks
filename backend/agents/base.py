"""Base agent contract for the v0.4 source-grounded pipeline.

`AgentContext` carries the parsed paper, atom under inspection, graph,
and previously computed checks/challenges/rebuttals. Deterministic helpers
(span resolver, equation linker, citation linker, checks) are not agents
and live outside this hierarchy.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from models import (
    Challenge,
    CheckResult,
    Rebuttal,
    ResearchAtom,
    ResearchGraph,
    ParsedPaper,
)


class AgentContext(BaseModel):
    job_id: str

    parsed_paper: Optional[ParsedPaper] = None
    atom: Optional[ResearchAtom] = None
    graph: Optional[ResearchGraph] = None

    checks: list[CheckResult] = Field(default_factory=list)
    challenges: list[Challenge] = Field(default_factory=list)
    rebuttals: list[Rebuttal] = Field(default_factory=list)

    extra: dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    agent_id: str
    status: Literal["success", "error", "inconclusive"]

    output: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)

    error: Optional[str] = None


class BaseAgent(ABC):
    agent_id: str = "base_agent"

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        ...
