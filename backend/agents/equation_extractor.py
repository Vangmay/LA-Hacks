import json
import logging
import re
from typing import List

from openai import AsyncOpenAI

from config import settings
from .base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)

# Regex patterns for explicit LaTeX delimiters in raw text
_DISPLAY_BLOCK = re.compile(
    r'\$\$(.+?)\$\$'
    r'|\\begin\{equation\*?\}(.+?)\\end\{equation\*?\}'
    r'|\\begin\{align\*?\}(.+?)\\end\{align\*?\}'
    r'|\\begin\{eqnarray\*?\}(.+?)\\end\{eqnarray\*?\}',
    re.DOTALL,
)
_INLINE = re.compile(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)')

_SYSTEM_PROMPT = (
    "You are a mathematical equation extractor. "
    "Given a passage of text from a research paper, identify every mathematical equation, "
    "formula, or quantitative relationship stated in the text. "
    "Return them as LaTeX strings in a JSON object: {\"equations\": [\"...\", \"...\"]}. "
    "Include only genuine equations or inequalities — not prose descriptions. "
    "If there are no equations, return {\"equations\": []}."
)


class EquationExtractorAgent(BaseAgent):
    """Extracts LaTeX equations from raw text.

    Used as a fallback when the parser's equation list is empty.
    Owned by Person B — supplements SymbolicVerifierAgent.
    """

    agent_id = "equation_extractor"
    _client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def run(self, context: AgentContext) -> AgentResult:
        raw_text: str = context.extra.get("raw_text", "")
        claim_text: str = context.extra.get("claim_text", "")

        # Prefer a focused window around the claim if available
        search_text = self._window(raw_text, claim_text) if claim_text else raw_text

        # Step 1: fast regex pass
        regex_eqs = self._regex_extract(search_text)

        # Step 2: GPT-4o pass (always — catches equations written without LaTeX markers)
        gpt_eqs = await self._gpt_extract(search_text)

        # Merge, deduplicate, preserve order
        seen = set()
        merged = []
        for eq in regex_eqs + gpt_eqs:
            eq = eq.strip()
            if eq and eq not in seen:
                seen.add(eq)
                merged.append(eq)

        logger.info(
            "equation_extractor: found %d equations (%d regex, %d gpt)",
            len(merged), len(regex_eqs), len(gpt_eqs),
        )

        return AgentResult(
            agent_id=self.agent_id,
            claim_id=context.extra.get("claim_id"),
            status="success" if merged else "inconclusive",
            output={"equations": merged, "count": len(merged)},
            confidence=0.8 if merged else 0.3,
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    def _window(self, raw_text: str, claim_text: str, radius: int = 600) -> str:
        """Return up to `radius` chars around the first occurrence of claim_text."""
        idx = raw_text.find(claim_text[:40])
        if idx == -1:
            return raw_text[:3000]  # fall back to start of doc
        start = max(0, idx - radius)
        end = min(len(raw_text), idx + len(claim_text) + radius)
        return raw_text[start:end]

    def _regex_extract(self, text: str) -> List[str]:
        results = []
        for m in _DISPLAY_BLOCK.finditer(text):
            eq = next((g for g in m.groups() if g), "").strip()
            if eq:
                results.append(eq)
        for m in _INLINE.finditer(text):
            eq = m.group(1).strip()
            if eq and len(eq) > 1:  # skip single-char inline like $x$
                results.append(eq)
        return results

    async def _gpt_extract(self, text: str) -> List[str]:
        # Truncate to avoid token overflow
        snippet = text[:4000]
        try:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": snippet},
                ],
                response_format={"type": "json_object"},
                max_tokens=500,
            )
            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
            eqs = data.get("equations", [])
            return [e for e in eqs if isinstance(e, str) and e.strip()]
        except Exception as exc:
            logger.warning("equation_extractor: GPT call failed: %s", exc)
            return []
