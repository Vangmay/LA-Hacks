import logging

from agents.base import AgentContext, AgentResult, BaseAgent
from models import ResearchAtom

logger = logging.getLogger(__name__)

_SCAFFOLD_FILES = (
    "implementation.py",
    "test_harness.py",
    "results_logger.py",
    "requirements.txt",
    "README.md",
)


class ScaffoldGeneratorAgent(BaseAgent):
    agent_id = "scaffold_generator"

    async def run(self, context: AgentContext) -> AgentResult:
        atom: ResearchAtom | None = context.atom or context.extra.get("atom")
        if atom is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"scaffold_files": {}},
                confidence=0.0,
                error="No atom provided in context.atom",
            )

        poc_spec: dict = context.extra.get("poc_spec", {})

        # PoC scaffolding is intentionally empty: each testable atom gets the
        # canonical file layout with no contents, leaving the user to write the
        # implementation. Metrics from the spec still drive the success criteria
        # the user will eventually report via /poc/{id}/results.
        scaffold_files = {fname: "" for fname in _SCAFFOLD_FILES}

        updated_spec = dict(poc_spec)
        updated_spec["scaffold_files"] = scaffold_files
        updated_spec["readme"] = ""

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={"scaffold_files": scaffold_files, "poc_spec": updated_spec},
            confidence=1.0,
        )
