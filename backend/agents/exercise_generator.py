"""ExerciseGeneratorAgent - generate comprehension exercises for a ResearchAtom."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from openai import AsyncOpenAI

from config import settings
from core.openai_client import make_async_openai

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Generate 2-3 exercises to test understanding of the given research atom at "
    "the specified comprehension level. Generate one exercise of each applicable type:\n"
    "- counterexample_mcq: a direct multiple-choice question with exactly four "
    "options: one correct option and three plausible distractors\n"
    "- computational: a numerical or algebraic calculation that tests the atom\n"
    "- proof_fill: 'Fill in the missing step: Given X, we know Y because ___'\n\n"
    "Return a JSON object with key 'exercises' containing an array of objects, each with: "
    "prompt (str), exercise_type (counterexample_mcq|computational|proof_fill), "
    "answer_key (str), and for counterexample_mcq only, options ([str]) with exactly "
    "four answer choices. Return ONLY the JSON object."
)

_VALID_TYPES = {"conceptual", "computational", "counterexample_mcq", "proof_fill"}


class ExerciseGeneratorAgent(BaseAgent):
    agent_id = "exercise_generator"

    def __init__(self, client: Optional[AsyncOpenAI] = None) -> None:
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = make_async_openai()
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        atom = context.atom
        if atom is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"exercises": []},
                confidence=0.0,
                error="atom missing from context",
            )

        level = context.extra.get("comprehension_level", "undergraduate")

        user_content = (
            f"Comprehension level: {level}\n\n"
            f"Atom type: {atom.atom_type.value}\n"
            f"Section: {atom.section_heading or 'unknown'}\n\n"
            f"Atom text:\n{atom.text}"
        )

        try:
            response = await self._get_client().chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                max_tokens=900,
            )
            raw = response.choices[0].message.content or ""
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"exercises": []},
                confidence=0.0,
                error=f"json_parse_failed: {exc}",
            )
        except Exception as exc:
            logger.exception("ExerciseGeneratorAgent LLM call failed")
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"exercises": []},
                confidence=0.0,
                error=str(exc),
            )

        raw_exercises = data.get("exercises") if isinstance(data, dict) else None
        if not isinstance(raw_exercises, list):
            raw_exercises = []

        exercises: list[dict] = []
        for ex in raw_exercises:
            if not isinstance(ex, dict):
                continue
            prompt = str(ex.get("prompt", "")).strip()
            ex_type = str(ex.get("exercise_type", "")).strip()
            answer_key = str(ex.get("answer_key", "")).strip()
            raw_options = ex.get("options") or []
            if not prompt or not answer_key:
                continue
            if ex_type not in _VALID_TYPES:
                ex_type = "computational"

            clean_exercise = {
                "exercise_id": str(uuid.uuid4()),
                "prompt": prompt,
                "exercise_type": ex_type,
                "answer_key": answer_key,
            }
            if ex_type == "counterexample_mcq" and isinstance(raw_options, list):
                options = [
                    str(option).strip()
                    for option in raw_options
                    if str(option).strip()
                ][:4]
                if len(options) == 4:
                    clean_exercise["options"] = options

            exercises.append(clean_exercise)

        return AgentResult(
            agent_id=self.agent_id,
            status="success" if exercises else "inconclusive",
            output={"exercises": exercises},
            confidence=0.85 if exercises else 0.3,
        )
