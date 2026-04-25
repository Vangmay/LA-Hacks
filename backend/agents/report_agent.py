import json
import logging
from datetime import datetime
from typing import Dict, List

from openai import AsyncOpenAI

from config import settings
from models import ClaimVerdict, ReviewReport

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = (
    "Generate a structured peer review report in markdown. Include: executive "
    "summary, critical findings (refuted claims with rationale), contested "
    "claims requiring attention, cascade failure chain if present, and an "
    "overall assessment. Be direct and technical."
)


class ReportAgent(BaseAgent):
    agent_id = "report_agent"

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        extra = context.extra or {}
        verdicts_in = extra.get("verdicts") or {}
        paper_meta = extra.get("paper_metadata") or {}
        dag_summary = extra.get("dag_summary") or {"nodes": [], "edges": []}

        verdicts: List[ClaimVerdict] = []
        for cid, v in verdicts_in.items():
            if isinstance(v, ClaimVerdict):
                verdicts.append(v)
                continue
            try:
                verdicts.append(ClaimVerdict.model_validate(v))
            except Exception as exc:
                logger.warning("report_agent: skipping unparseable verdict %s: %s", cid, exc)

        total_claims = len(verdicts)
        supported = sum(1 for v in verdicts if v.verdict == "SUPPORTED")
        contested = sum(1 for v in verdicts if v.verdict == "CONTESTED")
        refuted = sum(1 for v in verdicts if v.verdict == "REFUTED")
        cascaded_failures = sum(1 for v in verdicts if v.is_cascaded)

        markdown = await self._generate_markdown(
            verdicts=verdicts,
            paper_meta=paper_meta,
            stats={
                "total_claims": total_claims,
                "supported": supported,
                "contested": contested,
                "refuted": refuted,
                "cascaded_failures": cascaded_failures,
            },
        )

        report = ReviewReport(
            paper_title=paper_meta.get("title") or "Untitled Paper",
            paper_hash=paper_meta.get("hash") or "0" * 16,
            reviewed_at=datetime.utcnow(),
            total_claims=total_claims,
            supported=supported,
            contested=contested,
            refuted=refuted,
            cascaded_failures=cascaded_failures,
            verdicts=verdicts,
            dag_summary=dag_summary,
            markdown_report=markdown,
        )

        return AgentResult(
            agent_id=self.agent_id,
            claim_id=None,
            status="success",
            output={
                "report": report.model_dump(mode="json"),
                "markdown": markdown,
            },
            confidence=0.9,
        )

    async def _generate_markdown(
        self,
        verdicts: List[ClaimVerdict],
        paper_meta: Dict,
        stats: Dict,
    ) -> str:
        payload = {
            "paper_metadata": paper_meta,
            "summary": stats,
            "verdicts": [v.model_dump(mode="json") for v in verdicts],
        }

        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload, default=str)},
                ],
                max_tokens=2000,
            )
            content = response.choices[0].message.content or ""
            if content.strip():
                return content.strip()
            logger.warning("report_agent: empty LLM markdown, falling back")
        except Exception as exc:
            logger.exception("report_agent: LLM call failed: %s", exc)

        return _fallback_markdown(verdicts, paper_meta, stats)


def _fallback_markdown(
    verdicts: List[ClaimVerdict],
    paper_meta: Dict,
    stats: Dict,
) -> str:
    title = paper_meta.get("title") or "Untitled Paper"
    lines: List[str] = [
        f"# Peer Review Report — {title}",
        "",
        "## Executive Summary",
        f"- Total claims: {stats['total_claims']}",
        f"- Supported: {stats['supported']}",
        f"- Contested: {stats['contested']}",
        f"- Refuted: {stats['refuted']}",
        f"- Cascaded failures: {stats['cascaded_failures']}",
        "",
    ]

    refuted = [v for v in verdicts if v.verdict == "REFUTED"]
    if refuted:
        lines.append("## Critical Findings (Refuted)")
        for v in refuted:
            lines.append(f"- **{v.claim_id}** (confidence {v.confidence:.2f})")
            for ch in v.challenges[:3]:
                lines.append(f"  - Challenge: {ch.challenge_text}")
        lines.append("")

    contested = [v for v in verdicts if v.verdict == "CONTESTED"]
    if contested:
        lines.append("## Contested Claims")
        for v in contested:
            lines.append(f"- **{v.claim_id}** (confidence {v.confidence:.2f})")
        lines.append("")

    cascaded = [v for v in verdicts if v.is_cascaded]
    if cascaded:
        lines.append("## Cascade Failure Chain")
        for v in cascaded:
            lines.append(f"- {v.claim_id} ← {v.cascade_source}")
        lines.append("")

    lines.append("## Overall Assessment")
    if stats["refuted"] > 0:
        lines.append("Paper has refuted claims; results are not reliable as stated.")
    elif stats["contested"] > 0:
        lines.append("Paper has contested claims requiring author attention.")
    else:
        lines.append("All claims supported by available verification.")

    return "\n".join(lines)
