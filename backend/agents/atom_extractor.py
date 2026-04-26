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
from core.openai_client import build_messages, extract_json, json_response_format, make_async_openai
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

_HEADER_SYSTEM_PROMPT = (
    "You clean source-grounded research atoms into concise standalone atom headers. "
    "You never invent claims. If an atom cannot be expressed as a clear concise "
    "standalone header from the supplied source text, mark it keep=false. Output JSON only."
)

_HEADER_PROMPT_TMPL = """Normalize these extracted research atoms into concise, standalone atom headers.

Each input atom includes its current extracted text and source excerpt. Return one decision for every atom_id.

Atoms:
{atoms_json}

Return a JSON object:
{{
  "atoms": [
    {{
      "atom_id": "atom_001",
      "keep": true,
      "header": "concise standalone atom header",
      "drop_reason": ""
    }}
  ],
  "warnings": []
}}

Rules:
- `header` must be a complete standalone claim/title, not a dangling fragment.
- Headers should name the concept or claim being reviewed, not copy the first words near an equation.
- Never end a header with a dangling word such as at, to, of, by, with, for, and, or, but, less, more, using, because.
- Examples of invalid fragments: "Research goal make sequence generation less"; "Transformer decoder has six layers and".
- Keep headers concise: normally 5-24 words, maximum 160 characters.
- Preserve the atom's meaning and type. Do not add claims not present in the source excerpt.
- Prefer a clear noun phrase or short sentence over copied surrounding prose.
- Drop atoms that are just equation-neighbor fragments, citations, captions, section transitions, or incomplete clauses.
- Drop atoms that require too much context to state concisely and faithfully.
- Return every atom_id exactly once. No prose. No markdown.
"""

_DANGLING_HEADER_ENDINGS = {
    "a",
    "an",
    "the",
    "at",
    "to",
    "of",
    "by",
    "with",
    "for",
    "from",
    "in",
    "on",
    "and",
    "or",
    "but",
    "as",
    "than",
    "that",
    "which",
    "less",
    "more",
    "very",
    "much",
    "many",
    "such",
    "where",
    "when",
    "while",
    "because",
    "via",
    "using",
}

_MAX_HEADER_BATCH_ATOMS = 50


class AtomExtractorAgent(BaseAgent):
    agent_id = "atom_extractor"

    def __init__(
        self,
        client: Optional[AsyncOpenAI] = None,
        max_section_chars: int = 14000,
        progress_callback: Optional[
            Callable[[list[ResearchAtom], dict[str, Any]], Awaitable[None]]
        ] = None,
        normalize_headers: bool = True,
    ) -> None:
        self._client = client
        self._max_section_chars = max_section_chars
        self._progress_callback = progress_callback
        self._normalize_headers = normalize_headers

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = make_async_openai()
        return self._client

    async def run(self, context: AgentContext) -> AgentResult:
        import time
        paper = context.parsed_paper
        if paper is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"atoms": [], "warnings": []},
                confidence=0.0,
                error="parsed_paper missing from context",
            )

        timings = {}
        t0 = time.perf_counter()
        deterministic = self._extract_environments(paper)
        t1 = time.perf_counter()
        timings["deterministic"] = t1 - t0
        warnings: list[str] = []
        logger.warning(f"[DEBUG] Deterministic atoms extracted: {len(deterministic)}")
        for atom in deterministic:
            logger.warning(f"[DEBUG] Deterministic atom: {atom.atom_type} | {atom.text[:80]}")
        await self._emit_progress(
            _merge_atoms(deterministic, []),
            {
                "stage": "Extracting atoms",
                "batches_completed": 0,
                "batches_total": len(_section_batches(paper, self._max_section_chars)),
            },
        )

        try:
            t2 = time.perf_counter()
            llm_atoms, llm_warnings = await self._extract_with_llm_parallel(paper, deterministic)
            t3 = time.perf_counter()
            timings["llm"] = t3 - t2
            warnings.extend(llm_warnings)
            logger.warning(f"[DEBUG] LLM atoms extracted: {len(llm_atoms)}")
            for atom in llm_atoms:
                logger.warning(f"[DEBUG] LLM atom: {atom.atom_type} | {atom.text[:80]}")
        except Exception as exc:
            logger.exception("LLM atom extraction failed")
            warnings.append(f"llm_extraction_failed: {exc}")
            llm_atoms = []

        # Early deduplication/filtering before normalization
        merged = _merge_atoms(deterministic, llm_atoms)
        logger.warning(f"[DEBUG] Atoms after merge: {len(merged)}")
        merged = _filter_duplicate_and_low_confidence_atoms(merged)
        logger.warning(f"[DEBUG] Atoms after filtering: {len(merged)}")

        if self._normalize_headers and merged:
            try:
                t4 = time.perf_counter()
                merged, normalization_warnings = await self._normalize_headers_with_llm(merged)
                t5 = time.perf_counter()
                timings["normalize_headers"] = t5 - t4
                warnings.extend(normalization_warnings)
                logger.warning(f"[DEBUG] Atoms after header normalization: {len(merged)}")
                for atom in merged:
                    logger.warning(f"[DEBUG] Normalized atom: {atom.atom_type} | {atom.text[:80]}")
                await self._emit_progress(
                    merged,
                    {
                        "stage": "Normalizing atom headers",
                        "batches_completed": 1,
                        "batches_total": 1,
                    },
                )
            except Exception as exc:
                logger.exception("LLM atom header normalization failed")
                warnings.append(f"llm_header_normalization_failed: {exc}")
        result = AtomExtractionResult(
            paper_id=paper.paper_id,
            atoms=merged,
            warnings=warnings + [f"timings: {timings}"],
        )

        confidence = 0.85 if merged else 0.2
        return AgentResult(
            agent_id=self.agent_id,
            status="success" if merged else "inconclusive",
            output=result.model_dump(),
            confidence=confidence,
        )

    async def _extract_with_llm_parallel(self, paper: ParsedPaper, seen: list[ResearchAtom], max_concurrency: int = 4) -> tuple[list[ResearchAtom], list[str]]:
        import asyncio
        batches = _section_batches(paper, self._max_section_chars)
        if not batches:
            return [], ["llm_skipped: empty section text"]

        client = self._get_client()
        atoms: list[ResearchAtom] = []
        warnings: list[str] = []
        counter = 0

        semaphore = asyncio.Semaphore(max_concurrency)
        results = [None] * len(batches)

        async def process_batch(batch_idx, sections_text):
            nonlocal counter
            async with semaphore:
                seen_block = _format_seen_block([*seen, *atoms]) or "(none)"
                prompt = _USER_PROMPT_TMPL.format(
                    seen_block=seen_block,
                    sections_text=sections_text,
                )
                try:
                    response = await client.chat.completions.create(
                        model=settings.openai_model,
                        messages=build_messages(_SYSTEM_PROMPT, prompt),
                        **json_response_format(),
                        max_tokens=16000,
                    )
                    raw = extract_json(response.choices[0].message.content or "")
                    data = json.loads(raw)
                except Exception as exc:
                    warnings.append(f"llm_batch_{batch_idx}_failed: {exc}")
                    return

                atoms_data = data.get("atoms") if isinstance(data, dict) else None
                if not isinstance(atoms_data, list):
                    warnings.append(f"llm_response_missing_atoms_array_batch_{batch_idx}")
                    return

                batch_warnings = data.get("warnings") if isinstance(data, dict) else None
                if isinstance(batch_warnings, list):
                    warnings.extend(str(w) for w in batch_warnings if str(w).strip())

                batch_atoms = []
                for entry in atoms_data:
                    if not isinstance(entry, dict):
                        continue
                    atom = _atom_from_llm_entry(entry, paper, counter)
                    if atom is None:
                        continue
                    batch_atoms.append(atom)
                    counter += 1
                results[batch_idx] = batch_atoms
                await self._emit_progress(
                    _merge_atoms(seen, atoms + batch_atoms),
                    {
                        "stage": f"Extracting atoms ({batch_idx+1}/{len(batches)})",
                        "batches_completed": batch_idx+1,
                        "batches_total": len(batches),
                    },
                )

        await asyncio.gather(*(process_batch(i, batch) for i, batch in enumerate(batches)))
        # Flatten results and filter out None
        for batch_atoms in results:
            if batch_atoms:
                atoms.extend(batch_atoms)
        return atoms, warnings


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
                messages=build_messages(_SYSTEM_PROMPT, prompt),
                **json_response_format(),
                max_tokens=16000,
            )
            raw = extract_json(response.choices[0].message.content or "")
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

    async def _normalize_headers_with_llm(
        self,
        atoms: list[ResearchAtom],
    ) -> tuple[list[ResearchAtom], list[str]]:
        client = self._get_client()
        warnings: list[str] = []
        decisions: dict[str, dict[str, Any]] = {}

        for batch_idx, batch in enumerate(_atom_batches(atoms, _MAX_HEADER_BATCH_ATOMS), start=1):
            payload = [
                {
                    "atom_id": atom.atom_id,
                    "atom_type": atom.atom_type.value,
                    "section_heading": atom.section_heading,
                    "current_text": atom.text[:600],
                    "normalized_text": (atom.normalized_text or "")[:300],
                    "source_excerpt": (atom.source_span.raw_excerpt or atom.text)[:900],
                    "role_in_paper": atom.role_in_paper,
                }
                for atom in batch
            ]
            prompt = _HEADER_PROMPT_TMPL.format(
                atoms_json=json.dumps(payload, ensure_ascii=False, indent=2)
            )
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=build_messages(_HEADER_SYSTEM_PROMPT, prompt),
                **json_response_format(),
                max_tokens=16000,
            )
            raw = extract_json(response.choices[0].message.content or "")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                warnings.append(f"llm_header_json_parse_failed_batch_{batch_idx}: {exc}")
                continue

            atom_entries = data.get("atoms") if isinstance(data, dict) else None
            if not isinstance(atom_entries, list):
                warnings.append(f"llm_header_response_missing_atoms_array_batch_{batch_idx}")
                continue

            batch_warnings = data.get("warnings") if isinstance(data, dict) else None
            if isinstance(batch_warnings, list):
                warnings.extend(str(w) for w in batch_warnings if str(w).strip())

            for entry in atom_entries:
                if not isinstance(entry, dict):
                    continue
                atom_id = str(entry.get("atom_id") or "").strip()
                if atom_id:
                    decisions[atom_id] = entry

        if not decisions:
            warnings.append("llm_header_normalization_returned_no_decisions")
            return _renumber_atoms([atom for atom in atoms if _locally_keepable_header(atom.text)] or atoms), warnings

        cleaned: list[ResearchAtom] = []
        missing_decisions = 0
        dropped = 0
        for atom in atoms:
            decision = decisions.get(atom.atom_id)
            if decision is None:
                missing_decisions += 1
                if _locally_keepable_header(atom.text):
                    cleaned.append(atom.model_copy(update={"text": _compact_header(atom.text)}))
                continue

            keep = _coerce_bool(decision.get("keep"), default=True)
            header = _compact_header(str(decision.get("header") or ""))
            if not keep:
                dropped += 1
                continue
            if not _valid_atom_header(header):
                dropped += 1
                continue
            cleaned.append(
                atom.model_copy(
                    update={
                        "text": header,
                        "normalized_text": header,
                    }
                )
            )

        if missing_decisions:
            warnings.append(f"llm_header_missing_decisions: {missing_decisions}")
        if dropped:
            warnings.append(f"llm_header_dropped_atoms: {dropped}")
        if not cleaned:
            warnings.append("llm_header_normalization_dropped_all_atoms; preserving local keepable originals")
            cleaned = [atom.model_copy(update={"text": _compact_header(atom.text)}) for atom in atoms if _locally_keepable_header(atom.text)]
        return _renumber_atoms(cleaned), warnings

    async def _emit_progress(self, atoms: list[ResearchAtom], progress: dict[str, Any]) -> None:
        if self._progress_callback is None:
            return
        try:
            await self._progress_callback(atoms, progress)
        except Exception as exc:  # noqa: BLE001
            logger.warning("atom extraction progress callback failed: %s", exc)


# ---------------------------------------------------------------------------
# helpers


def _filter_duplicate_and_low_confidence_atoms(
    atoms: list[ResearchAtom], min_confidence: float = 0.5
) -> list[ResearchAtom]:
    seen_texts = set()
    filtered = []
    for atom in atoms:
        key = (atom.text or "").strip().lower()
        if atom.extraction_confidence is not None and atom.extraction_confidence < min_confidence:
            continue
        if key and key not in seen_texts:
            seen_texts.add(key)
            filtered.append(atom)
    return filtered


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


def _atom_batches(atoms: list[ResearchAtom], batch_size: int) -> list[list[ResearchAtom]]:
    size = max(1, batch_size)
    return [atoms[idx : idx + size] for idx in range(0, len(atoms), size)]


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "keep"}:
            return True
        if normalized in {"false", "no", "0", "drop"}:
            return False
    return default


def _compact_header(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = text.strip(" -:;,.")
    if len(text) <= 160:
        return text
    clipped = text[:160].rsplit(" ", 1)[0].strip(" -:;,.")
    return clipped or text[:160].strip(" -:;,.")


def _valid_atom_header(value: str) -> bool:
    text = _compact_header(value)
    if not text:
        return False
    words = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text)
    if len(words) < 3:
        return False
    if len(text) > 180:
        return False
    last = words[-1].lower()
    if last in _DANGLING_HEADER_ENDINGS:
        return False
    if re.search(r"(?:\bat\b|\bto\b|\band\b|\bby\b)\s*$", text, flags=re.IGNORECASE):
        return False
    if text.count("$") % 2 == 1:
        return False
    return True


def _locally_keepable_header(value: str) -> bool:
    text = _compact_header(value)
    if _valid_atom_header(text):
        return True
    words = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text)
    return len(words) >= 6 and (words[-1].lower() not in _DANGLING_HEADER_ENDINGS)


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

    return _renumber_atoms(merged)


def _renumber_atoms(atoms: list[ResearchAtom]) -> list[ResearchAtom]:
    renumbered: list[ResearchAtom] = []
    for idx, atom in enumerate(atoms, start=1):
        renumbered.append(atom.model_copy(update={"atom_id": f"atom_{idx:03d}"}))
    return renumbered


def _text_overlap(a: str, b: str) -> bool:
    if not a or not b:
        return False
    a_short = a[:200].strip().lower()
    b_short = b[:200].strip().lower()
    if not a_short or not b_short:
        return False
    return a_short in b_short or b_short in a_short
