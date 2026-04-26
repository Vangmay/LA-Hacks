"""Two-pass research-atom extractor.

Pass A — deterministic: regex over the assembled TeX for `theorem`,
`lemma`, `corollary`, `proposition`, `definition`, `assumption`,
`conjecture`, `example`, `counterexample`, `algorithm`, and `proof`
environments. Each match becomes a high-confidence atom anchored by
its TeX span.

Pass B — LLM: a structured pass over the parsed paper sections that
fills in the things environments alone miss — definitions stated in
prose, key assumptions, limitations, open problems, and central
techniques. The LLM is required to return a verbatim `source_quote`
for every atom; the resolver pins each quote to a span.

Merge: deduplicate LLM atoms whose quote overlaps a deterministic
atom's TeX span (keep the deterministic one, since it has a
canonical environment label and a 1.0 span match).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Awaitable, Callable, Optional

from openai import AsyncOpenAI

from config import settings
from core.openai_client import make_async_openai
from core.span_resolver import resolve_span
from models import (
    AtomExtractionResult,
    AtomImportance,
    ParsedPaper,
    ResearchAtom,
    ResearchAtomType,
    SourceSpan,
)

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


_ENV_TO_TYPE: dict[str, ResearchAtomType] = {
    "theorem": ResearchAtomType.THEOREM,
    "lemma": ResearchAtomType.LEMMA,
    "corollary": ResearchAtomType.COROLLARY,
    "proposition": ResearchAtomType.PROPOSITION,
    "conjecture": ResearchAtomType.CONJECTURE,
    "definition": ResearchAtomType.DEFINITION,
    "defn": ResearchAtomType.DEFINITION,
    "assumption": ResearchAtomType.ASSUMPTION,
    "hypothesis": ResearchAtomType.ASSUMPTION,
    "example": ResearchAtomType.EXAMPLE,
    "counterexample": ResearchAtomType.COUNTEREXAMPLE,
    "algorithm": ResearchAtomType.ALGORITHM,
    "proof": ResearchAtomType.PROOF_STEP,
    "claim": ResearchAtomType.ASSERTION,
    "remark": ResearchAtomType.RELATED_WORK_CLAIM,
    "fact": ResearchAtomType.ASSERTION,
}

_ENV_PATTERN = re.compile(
    r"\\begin\s*\{(?P<env>[A-Za-z*]+)\}(?:\s*\[(?P<title>[^\]]*)\])?(?P<body>.*?)\\end\s*\{(?P=env)\}",
    re.DOTALL,
)
_RESEARCH_ENV_PATTERN = re.compile(
    r"\\begin\s*\{(?P<env>"
    + "|".join(re.escape(env) for env in sorted(_ENV_TO_TYPE, key=len, reverse=True))
    + r")(?P<star>\*?)\}(?:\s*\[(?P<title>[^\]]*)\])?"
    + r"(?P<body>.*?)\\end\s*\{(?P=env)(?P=star)\}",
    re.DOTALL,
)
_LATEX_LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
_DEFAULT_IMPORTANCE = {
    ResearchAtomType.THEOREM: AtomImportance.HIGH,
    ResearchAtomType.PROPOSITION: AtomImportance.HIGH,
    ResearchAtomType.LEMMA: AtomImportance.MEDIUM,
    ResearchAtomType.COROLLARY: AtomImportance.MEDIUM,
    ResearchAtomType.CONJECTURE: AtomImportance.HIGH,
    ResearchAtomType.DEFINITION: AtomImportance.MEDIUM,
    ResearchAtomType.ASSUMPTION: AtomImportance.HIGH,
    ResearchAtomType.PROOF_STEP: AtomImportance.LOW,
    ResearchAtomType.EXAMPLE: AtomImportance.LOW,
    ResearchAtomType.COUNTEREXAMPLE: AtomImportance.MEDIUM,
    ResearchAtomType.ALGORITHM: AtomImportance.HIGH,
}


_SYSTEM_PROMPT = (
    "You are a precise extractor of source-grounded research atoms from a "
    "theoretical paper. A research atom is a discrete unit such as a "
    "definition, assumption, theorem, lemma, proposition, corollary, "
    "construction, algorithm, limitation, open problem, technique, or "
    "load-bearing assertion stated in prose. Every atom MUST quote the "
    "paper verbatim. Do not invent claims. Output JSON only."
)

_USER_PROMPT_TMPL = """Extract research atoms from the paper sections below.

Already-detected environment-based atoms (do NOT duplicate these):
{seen_block}

Sections (heading + body):
\"\"\"
{sections_text}
\"\"\"

Return a JSON object:
{{
  "atoms": [
    {{
      "atom_type": "definition|assumption|theorem|lemma|corollary|proposition|conjecture|proof_step|construction|algorithm|bound|example|counterexample|limitation|open_problem|related_work_claim|technique|assertion",
      "source_quote": "<verbatim excerpt from the section text>",
      "text": "<atom statement, can be cleaned but must preserve meaning>",
      "normalized_text": "<one-sentence paraphrase, optional>",
      "section_heading": "<which section heading this came from>",
      "importance": "low|medium|high|core",
      "role_in_paper": "<one short phrase>",
      "assumptions": ["..."],
      "conclusions": ["..."],
      "key_terms": ["..."],
      "symbols": ["..."],
      "confidence": 0.0
    }}
  ],
  "warnings": []
}}

Rules:
- Prefer definitions stated in prose, key assumptions, limitations, and
  central techniques. Skip generic background prose, motivation, and
  acknowledgements.
- For theorem-like atoms, separate `assumptions` and `conclusions` when
  the statement makes them explicit; otherwise leave them empty.
- `source_quote` must appear verbatim (modulo whitespace) in the section
  body. Do not paraphrase the quote.
- `confidence` is 0.0–1.0. Be conservative.
- Return ONLY the JSON object. No prose. No markdown.
"""


class AtomExtractorAgent(BaseAgent):
    agent_id = "atom_extractor"

    def __init__(
        self,
        client: Optional[AsyncOpenAI] = None,
        max_section_chars: int = 14000,
        progress_callback: Optional[
            Callable[[list[ResearchAtom], dict[str, Any]], Awaitable[None]]
        ] = None,
    ) -> None:
        self._client = client
        self._max_section_chars = max_section_chars
        self._progress_callback = progress_callback

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = make_async_openai()
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        paper = context.parsed_paper
        if paper is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"atoms": [], "warnings": []},
                confidence=0.0,
                error="parsed_paper missing from context",
            )

        deterministic = self._extract_environments(paper)
        warnings: list[str] = []
        await self._emit_progress(
            _merge_atoms(deterministic, []),
            {
                "stage": "Extracting atoms",
                "batches_completed": 0,
                "batches_total": len(_section_batches(paper, self._max_section_chars)),
            },
        )

        try:
            llm_atoms, llm_warnings = await self._extract_with_llm(paper, deterministic)
            warnings.extend(llm_warnings)
        except Exception as exc:
            logger.exception("LLM atom extraction failed")
            warnings.append(f"llm_extraction_failed: {exc}")
            llm_atoms = []

        merged = _merge_atoms(deterministic, llm_atoms)
        result = AtomExtractionResult(
            paper_id=paper.paper_id,
            atoms=merged,
            warnings=warnings,
        )

        confidence = 0.85 if merged else 0.2
        return AgentResult(
            agent_id=self.agent_id,
            status="success" if merged else "inconclusive",
            output=result.model_dump(),
            confidence=confidence,
        )

    # --------------------------------------------------------------- pass A

    def _extract_environments(self, paper: ParsedPaper) -> list[ResearchAtom]:
        atoms: list[ResearchAtom] = []
        assembled = paper.assembled_tex or ""
        if not assembled:
            return atoms

        counter = 0
        for match in _iter_research_env_matches(assembled):
            raw_env = match.group("env").lower().rstrip("*")
            atom_type = _ENV_TO_TYPE.get(raw_env)
            if atom_type is None:
                continue

            body = match.group("body").strip()
            if not body:
                continue

            counter += 1
            tex_start = match.start()
            tex_end = match.end()
            label_match = _LATEX_LABEL_RE.search(body)
            label = label_match.group(1) if label_match else None

            section_id = _section_id_for_tex_offset(paper, tex_start)
            section_heading = _section_heading_for_id(paper, section_id)

            cleaned = _strip_tex(body)
            atom_id = f"atom_env_{counter:03d}"
            importance = _DEFAULT_IMPORTANCE.get(atom_type, AtomImportance.MEDIUM)

            atoms.append(
                ResearchAtom(
                    atom_id=atom_id,
                    paper_id=paper.paper_id,
                    atom_type=atom_type,
                    text=cleaned[:2000],
                    section_id=section_id,
                    section_heading=section_heading,
                    source_span=SourceSpan(
                        paper_id=paper.paper_id,
                        section_id=section_id,
                        tex_start=tex_start,
                        tex_end=tex_end,
                        raw_excerpt=cleaned[:1000],
                        match_confidence=1.0,
                    ),
                    extraction_confidence=0.95,
                    importance=importance,
                    role_in_paper=f"{atom_type.value} from \\begin{{{raw_env}}} environment"
                    + (f" (label {label})" if label else ""),
                )
            )

        return atoms

    # --------------------------------------------------------------- pass B

    async def _extract_with_llm(
        self,
        paper: ParsedPaper,
        seen: list[ResearchAtom],
    ) -> tuple[list[ResearchAtom], list[str]]:
        batches = _section_batches(paper, self._max_section_chars)
        if not batches:
            return [], ["llm_skipped: empty section text"]

        client = self._get_client()
        atoms: list[ResearchAtom] = []
        warnings: list[str] = []
        counter = 0

        for batch_idx, sections_text in enumerate(batches, start=1):
            seen_block = _format_seen_block([*seen, *atoms]) or "(none)"
            prompt = _USER_PROMPT_TMPL.format(
                seen_block=seen_block,
                sections_text=sections_text,
            )

            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=4500,
            )
            raw = response.choices[0].message.content or ""
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                warnings.append(f"llm_json_parse_failed_batch_{batch_idx}: {exc}")
                continue

            atoms_data = data.get("atoms") if isinstance(data, dict) else None
            if not isinstance(atoms_data, list):
                warnings.append(f"llm_response_missing_atoms_array_batch_{batch_idx}")
                continue

            batch_warnings = data.get("warnings") if isinstance(data, dict) else None
            if isinstance(batch_warnings, list):
                warnings.extend(str(w) for w in batch_warnings if str(w).strip())

            for entry in atoms_data:
                if not isinstance(entry, dict):
                    continue
                atom = _atom_from_llm_entry(entry, paper, counter)
                if atom is None:
                    continue
                atoms.append(atom)
                counter += 1

            await self._emit_progress(
                _merge_atoms(seen, atoms),
                {
                    "stage": f"Extracting atoms ({batch_idx}/{len(batches)})",
                    "batches_completed": batch_idx,
                    "batches_total": len(batches),
                },
            )

        return atoms, warnings

    async def _emit_progress(self, atoms: list[ResearchAtom], progress: dict[str, Any]) -> None:
        if self._progress_callback is None:
            return
        try:
            await self._progress_callback(atoms, progress)
        except Exception as exc:  # noqa: BLE001
            logger.warning("atom extraction progress callback failed: %s", exc)


# ---------------------------------------------------------------------------
# helpers


def _section_id_for_tex_offset(paper: ParsedPaper, offset: int) -> Optional[str]:
    best: Optional[str] = None
    for section in paper.sections:
        start = section.source_span.tex_start
        if start is None:
            continue
        if start > offset:
            break
        best = section.section_id
    return best


def _section_heading_for_id(paper: ParsedPaper, section_id: Optional[str]) -> Optional[str]:
    if not section_id:
        return None
    for section in paper.sections:
        if section.section_id == section_id:
            return section.heading
    return None


def _strip_tex(body: str) -> str:
    text = re.sub(r"\\label\{[^{}]+\}", "", body)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _iter_research_env_matches(assembled: str) -> list[re.Match[str]]:
    """Find atom-bearing environments without a broad document-level match.

    A single regex over all TeX environments can consume `document` and hide
    theorem-like environments nested inside it. This narrower pattern only
    targets environments that map to `ResearchAtomType`.
    """
    return sorted(_RESEARCH_ENV_PATTERN.finditer(assembled), key=lambda m: m.start())


def _section_batches(paper: ParsedPaper, max_chars: int) -> list[str]:
    batches: list[str] = []
    current: list[str] = []
    used = 0
    for section in paper.sections:
        if section.section_id == "sec_abstract":
            continue
        base_header = f"\n## {section.heading} [{section.section_id}]\n"
        body = section.content.strip()
        if not body:
            continue
        remaining = body
        first_chunk = True
        while remaining:
            header = (
                base_header
                if first_chunk
                else f"\n## {section.heading} [{section.section_id}, continued]\n"
            )
            if current and used + len(header) + min(len(remaining), max_chars) > max_chars:
                batches.append("\n".join(current).strip())
                current = []
                used = 0

            available = max(1, max_chars - used - len(header))
            chunk_body = remaining[:available]
            chunk = header + chunk_body
            current.append(chunk)
            used += len(chunk)
            remaining = remaining[available:]
            first_chunk = False

            if remaining:
                batches.append("\n".join(current).strip())
                current = []
                used = 0

    if current:
        batches.append("\n".join(current).strip())
    return [batch for batch in batches if batch]


def _format_seen_block(seen: list[ResearchAtom]) -> str:
    if not seen:
        return ""
    lines: list[str] = []
    for atom in seen[:30]:
        snippet = atom.text[:140].replace("\n", " ")
        lines.append(f"- {atom.atom_type.value} ({atom.section_heading or '?'}): {snippet}")
    if len(seen) > 30:
        lines.append(f"- ... ({len(seen) - 30} more deterministic atoms)")
    return "\n".join(lines)


def _atom_from_llm_entry(
    entry: dict[str, Any],
    paper: ParsedPaper,
    index: int,
) -> Optional[ResearchAtom]:
    atom_type = _coerce_atom_type(entry.get("atom_type"))
    if atom_type is None:
        return None

    source_quote = (entry.get("source_quote") or "").strip()
    text = (entry.get("text") or source_quote).strip()
    if not source_quote and not text:
        return None
    if not source_quote:
        source_quote = text

    span = resolve_span(paper, source_quote, entry.get("section_heading"))

    importance = _coerce_importance(entry.get("importance"))
    confidence = _coerce_confidence(entry.get("confidence"), default=0.6)

    atom_id = f"atom_llm_{index + 1:03d}"
    return ResearchAtom(
        atom_id=atom_id,
        paper_id=paper.paper_id,
        atom_type=atom_type,
        text=text[:2000],
        normalized_text=(entry.get("normalized_text") or None),
        section_id=span.section_id,
        section_heading=entry.get("section_heading") or _section_heading_for_id(paper, span.section_id),
        source_span=span,
        extraction_confidence=confidence,
        importance=importance,
        role_in_paper=(entry.get("role_in_paper") or None),
        assumptions=_coerce_str_list(entry.get("assumptions")),
        conclusions=_coerce_str_list(entry.get("conclusions")),
        key_terms=_coerce_str_list(entry.get("key_terms")),
        symbols=_coerce_str_list(entry.get("symbols")),
    )


def _coerce_atom_type(value: Any) -> Optional[ResearchAtomType]:
    if not isinstance(value, str):
        return None
    key = value.strip().lower().replace(" ", "_")
    try:
        return ResearchAtomType(key)
    except ValueError:
        # Tolerate close variants.
        synonyms = {
            "definitional": ResearchAtomType.DEFINITION,
            "thm": ResearchAtomType.THEOREM,
            "limitation_claim": ResearchAtomType.LIMITATION,
            "limit": ResearchAtomType.LIMITATION,
            "open": ResearchAtomType.OPEN_PROBLEM,
            "open_question": ResearchAtomType.OPEN_PROBLEM,
            "technique_claim": ResearchAtomType.TECHNIQUE,
            "claim": ResearchAtomType.ASSERTION,
        }
        return synonyms.get(key)


def _coerce_importance(value: Any) -> AtomImportance:
    if isinstance(value, str):
        try:
            return AtomImportance(value.strip().lower())
        except ValueError:
            pass
    return AtomImportance.MEDIUM


def _coerce_confidence(value: Any, default: float) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, f))


def _coerce_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _merge_atoms(
    deterministic: list[ResearchAtom],
    llm_atoms: list[ResearchAtom],
) -> list[ResearchAtom]:
    """Drop LLM atoms that overlap a deterministic atom's TeX span."""
    merged: list[ResearchAtom] = list(deterministic)

    det_ranges: list[tuple[int, int]] = []
    for atom in deterministic:
        s = atom.source_span.tex_start
        e = atom.source_span.tex_end
        if s is not None and e is not None:
            det_ranges.append((s, e))

    for atom in llm_atoms:
        s = atom.source_span.tex_start
        e = atom.source_span.tex_end
        overlap = False
        if s is not None and e is not None:
            for ds, de in det_ranges:
                if not (e < ds or s > de):
                    overlap = True
                    break
        if overlap:
            continue

        # Also drop near-duplicate text bodies.
        if any(_text_overlap(atom.text, d.text) for d in deterministic):
            continue

        merged.append(atom)

    # Renumber to a clean sequence.
    renumbered: list[ResearchAtom] = []
    for idx, atom in enumerate(merged, start=1):
        new_id = f"atom_{idx:03d}"
        renumbered.append(atom.model_copy(update={"atom_id": new_id}))
    return renumbered


def _text_overlap(a: str, b: str) -> bool:
    if not a or not b:
        return False
    a_short = a[:200].strip().lower()
    b_short = b[:200].strip().lower()
    if not a_short or not b_short:
        return False
    return a_short in b_short or b_short in a_short
