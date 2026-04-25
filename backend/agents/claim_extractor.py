import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI
from pydantic import ValidationError

from config import settings
from models import ClaimUnit

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_CITATION_RE = re.compile(r"\[(\d+)\]")
_CLAIM_TYPE_RE = re.compile(r"(theorem|lemma|corollary|proposition|assertion)", re.IGNORECASE)
_MAX_CHARS = 48000  # ~12k tokens @ 4 chars/token

_SYSTEM_PROMPT = (
    "You are a mathematical claim extractor. Given sections of a research paper, "
    "identify every theorem, lemma, corollary, proposition, and key load-bearing "
    "assertion. For each, return a JSON object with the fields specified. "
    "Be exhaustive — include informal assertions that are critical to the proof "
    "chain even if not labeled."
)

_USER_PROMPT = """Extract every theorem, lemma, corollary, proposition, and load-bearing assertion from the paper text below.

Return a JSON object with this exact shape:
{{
  "claims": [
    {{
      "text": "<the claim as stated, verbatim or near-verbatim>",
      "claim_type": "theorem|lemma|corollary|proposition|assertion",
      "section": "<section name or number where it appears>"
    }}
  ]
}}

Rules:
- Be exhaustive. Include informal but load-bearing assertions even if unlabeled.
- claim_type MUST be exactly one of: theorem, lemma, corollary, proposition, assertion.
- Output ONLY the JSON object. No prose, no markdown, no code fences.

PAPER TEXT:
\"\"\"
{text}
\"\"\""""

_RETRY_PROMPT = """Your previous response was not valid JSON. Return ONLY a JSON object with this exact schema, no prose, no markdown, no code fences:

{{ "claims": [ {{ "text": "...", "claim_type": "theorem|lemma|corollary|proposition|assertion", "section": "..." }} ] }}

PAPER TEXT:
\"\"\"
{text}
\"\"\""""


class ClaimExtractorAgent(BaseAgent):
    agent_id = "claim_extractor"

    EMPTY_OUTPUT: Dict[str, Any] = {"claims": []}

    def __init__(self, client: Optional[AsyncOpenAI] = None) -> None:
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        parser_output = (context.extra or {}).get("parser_output") or {}
        raw_text: str = parser_output.get("raw_text") or ""
        equations: List[Dict[str, str]] = parser_output.get("equations") or []

        if not raw_text.strip():
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="error",
                output=dict(self.EMPTY_OUTPUT),
                confidence=0.0,
                error="parser_output.raw_text is empty",
            )

        truncated = raw_text[:_MAX_CHARS]

        try:
            raw_resp = await self._call_llm(_USER_PROMPT.format(text=truncated))
            data, err = _safe_load(raw_resp)
            if err:
                logger.warning("Initial JSON parse failed (%s) — retrying once", err)
                raw_resp = await self._call_llm(_RETRY_PROMPT.format(text=truncated))
                data, err = _safe_load(raw_resp)
                if err:
                    logger.error("Retry JSON parse also failed: %s", err)
                    return AgentResult(
                        agent_id=self.agent_id,
                        claim_id=None,
                        status="inconclusive",
                        output=dict(self.EMPTY_OUTPUT),
                        confidence=0.0,
                        error=f"could not parse LLM JSON: {err}",
                    )
        except Exception as e:
            logger.exception("LLM call failed in ClaimExtractorAgent")
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="error",
                output=dict(self.EMPTY_OUTPUT),
                confidence=0.0,
                error=str(e),
            )

        claims = self._build_claims(data, raw_text, equations)
        if not claims:
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="inconclusive",
                output={"claims": []},
                confidence=0.2,
            )
        return AgentResult(
            agent_id=self.agent_id,
            claim_id=None,
            status="success",
            output={"claims": [c.model_dump() for c in claims]},
            confidence=0.7,
        )

    async def _call_llm(self, user_prompt: str) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=4000,
        )
        return response.choices[0].message.content or ""

    def _build_claims(
        self,
        data: Dict[str, Any],
        raw_text: str,
        equations: List[Dict[str, str]],
    ) -> List[ClaimUnit]:
        out: List[ClaimUnit] = []
        for i, raw_claim in enumerate(data.get("claims") or []):
            if not isinstance(raw_claim, dict):
                logger.warning("Dropping non-dict claim at index %d", i)
                continue

            text = (raw_claim.get("text") or "").strip()
            if not text:
                logger.warning("Dropping empty claim at index %d", i)
                continue

            claim_type = _normalize_claim_type(raw_claim.get("claim_type"))
            section = (raw_claim.get("section") or "").strip()
            claim_id = f"claim_{len(out) + 1:03d}"

            matched_equations = _match_equations(text, raw_text, equations)
            citations = _match_citations(text, raw_text)

            try:
                claim = ClaimUnit(
                    claim_id=claim_id,
                    text=text,
                    claim_type=claim_type,
                    section=section,
                    equations=matched_equations,
                    citations=citations,
                    dependencies=[],
                )
            except ValidationError as e:
                logger.warning("Dropping malformed claim at index %d: %s", i, e)
                continue
            out.append(claim)
        return out


def _safe_load(raw: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not raw or not raw.strip():
        return None, "empty response"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, str(e)
    if not isinstance(data, dict):
        return None, "response is not a JSON object"
    return data, None


def _normalize_claim_type(value: Any) -> str:
    if not isinstance(value, str):
        return "assertion"
    m = _CLAIM_TYPE_RE.search(value)
    return m.group(1).lower() if m else "assertion"


def _claim_position(claim_text: str, raw_text: str) -> int:
    """Locate `claim_text` in `raw_text`. Returns -1 if not found.

    LLMs tend to terminate verbatim claims with punctuation that may not match
    the source. Try progressively shorter prefixes, trimming punctuation, until
    we find a hit.
    """
    if not claim_text or not raw_text:
        return -1
    for length in (80, 60, 40):
        needle = claim_text[:length].rstrip(" .,;:")
        if len(needle) < 20:
            continue
        pos = raw_text.find(needle)
        if pos != -1:
            return pos
    return -1


def _match_equations(
    claim_text: str,
    raw_text: str,
    equations: List[Dict[str, str]],
    window: int = 200,
) -> List[str]:
    if not equations or not claim_text or not raw_text:
        return []
    pos = _claim_position(claim_text, raw_text)
    if pos == -1:
        return []
    start = max(0, pos - window)
    end = min(len(raw_text), pos + len(claim_text) + window)
    region = raw_text[start:end]

    matched: List[str] = []
    for eq in equations:
        eq_id = eq.get("id")
        latex = (eq.get("latex") or "").strip()
        if not eq_id or not latex:
            continue
        signature = latex[:40]
        if signature and signature in region:
            matched.append(eq_id)
    return matched


def _match_citations(claim_text: str, raw_text: str, window: int = 400) -> List[str]:
    found: set = set()
    for m in _CITATION_RE.finditer(claim_text or ""):
        found.add(m.group(1))

    pos = _claim_position(claim_text, raw_text)
    if pos != -1:
        start = max(0, pos - 50)
        end = min(len(raw_text), pos + len(claim_text) + window)
        for m in _CITATION_RE.finditer(raw_text[start:end]):
            found.add(m.group(1))

    return [f"[{n}]" for n in sorted(found, key=int)]
