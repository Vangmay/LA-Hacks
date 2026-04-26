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
from json_repair import repair_json

from config import settings
from core.openai_client import make_async_openai
from core.span_resolver import resolve_span
from models import (
    AtomCandidate,
    AtomCheckability,
    AtomExtractionResult,
    AtomImportance,
    AtomReviewability,
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
    "You extract source-grounded candidates for a review dependency DAG. "
    "You are not summarizing the paper. A valid candidate is one discrete "
    "claim, concept, definition, assumption, theorem, construction, algorithm, "
    "limitation, open problem, technique, or load-bearing assertion that can "
    "be grounded by a verbatim quote. Do not invent claims. Output JSON only."
)

_USER_PROMPT_TMPL = """Extract review-DAG atom candidates from the paper sections below.

Already-detected TeX-environment candidates (do NOT duplicate these):
{seen_block}

Sections (heading + body):
\"\"\"
{sections_text}
\"\"\"

Return a JSON object:
{{
  "candidates": [
    {{
      "atom_type": "definition|assumption|theorem|lemma|corollary|proposition|conjecture|proof_step|construction|algorithm|bound|example|counterexample|limitation|open_problem|related_work_claim|technique|assertion",
      "source_quote": "<verbatim excerpt from the section text>",
      "text": "<complete clean English atom statement with no raw LaTeX macros>",
      "normalized_text": "<one-sentence clean English paraphrase, optional>",
      "section_heading": "<which section heading this came from>",
      "importance": "low|medium|high|core",
      "reviewability": "reviewable|learning_only|background|drop",
      "checkability": "symbolic|numeric|citation|proof_only|conceptual|not_checkable",
      "claim_scope": "<what assumptions/context bound this candidate>",
      "why_this_is_an_atom": "<why this is a standalone review-DAG atom>",
      "role_in_paper": "<one short phrase>",
      "assumptions": ["..."],
      "conclusions": ["..."],
      "key_terms": ["..."],
      "symbols": ["..."],
      "dependency_hints": ["Uses the definition of ...", "Depends on ..."],
      "equation_refs": ["eq:label or visible equation reference"],
      "citation_refs": ["citation keys or bracket labels mentioned in the quote"],
      "confidence": 0.0
    }}
  ],
  "warnings": []
}}

Rules:
- You are not summarizing the paper. You are extracting candidates for a
  review dependency DAG.
- A candidate must be source-grounded by a verbatim quote, self-contained
  enough to review or teach, one claim/concept only, and not merely section
  narration or an equation-neighbor fragment.
- Do not collapse a technical section into one summary node. Preserve the
  central definitions, mechanisms, assumptions, guarantees, limitations,
  algorithms, and evaluation claims as separate candidates.
- For a dense technical batch, returning 6-18 candidates is normal. Return fewer
  only when the text is mostly background, logistics, captions, or bibliography.
- Keep central architecture, training, optimization, and evaluation claims when
  they are important to the paper; use `learning_only` or `conceptual` rather
  than dropping them just because they are not symbolic theorems.
- If one sentence contains three separable claims, split it into separate
  candidates with the same or overlapping source quote.
- If a candidate requires too much missing context, mark it
  `learning_only` or `drop`.
- Prefer definitions stated in prose, key assumptions, limitations, and
  central techniques. Skip generic background prose, motivation, and
  acknowledgements.
- An atom must be a reviewable scientific concept or claim, not a clipped
  sentence fragment, equation neighbor, citation sentence, table/caption
  text, or local implementation detail.
- For theorem-like atoms, separate `assumptions` and `conclusions` when
  the statement makes them explicit; otherwise leave them empty.
- `source_quote` must appear verbatim (modulo whitespace) in the section
  body. Do not paraphrase the quote.
- JSON strings must escape LaTeX backslashes correctly. For example, write
  `\\\\alpha` in JSON, not `\\alpha`.
- `text` and `normalized_text` are display statements. They must be complete
  clean English, and they must translate notation into words instead of copying
  raw LaTeX. Prefer "the latent variable has a standard normal prior" over
  "$z \\sim \\mathcal{{N}}(0,I)$".
- Display text may be longer than a graph label when needed. Do not truncate a
  sentence to fit the UI.
- Use `reviewability=background` for generic prior work or motivation.
- Use `reviewability=learning_only` for definitions, examples, techniques, or
  explanations useful to a reader but not themselves adversarially checkable.
- Use `reviewability=drop` for fragments, captions, generic logistics, and
  ungrounded or overly broad summary claims.
- `confidence` is 0.0–1.0. Be conservative.
- Return ONLY the JSON object. No prose. No markdown.

Positive examples to extract:
- Definition: "We define the self-attention layer as mapping a sequence of
  queries and keys to a weighted sum of values."
- Assumption: "We assume the input graph is connected and has bounded degree."
- Technique: "Residual connections are applied around every sub-layer before
  layer normalization."
- Limitation: "The method requires paired supervision and does not address
  fully unsupervised transfer."
- Bound/theorem-like assertion: "Under Lipschitz losses, the regret is
  O(sqrt(T)) with high probability."
- Open problem: "Whether the same guarantee holds for adaptive adversaries
  remains open."

Negative examples to drop:
- Dangling fragments: "Transformer decoder has six layers and";
  "Research goal make sequence generation less"; "where d_k is".
- Equation-neighbor snippets: "as shown in Eq. (3)", "we set alpha = 0.1",
  or a line that only introduces notation for the next display.
- Narrative glue: "We now describe the experiments", "The rest of the paper is
  organized as follows", "This motivates our approach."
- Citations/background only: "Prior work studied this problem [12]" unless the
  paper makes a specific related-work claim that matters to its argument.
- Captions/results narration: "Accuracy on WMT14 is shown in Table 2" unless it
  states a central empirical claim.
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
- `header` must be clean English with no raw LaTeX macros. Translate notation
  into words instead of copying formula text.
- Headers should name the concept or claim being reviewed, not copy the first words near an equation.
- Never end a header with a dangling word such as at, to, of, by, with, for, and, or, but, less, more, using, because.
- Examples of invalid fragments: "Research goal make sequence generation less"; "Transformer decoder has six layers and".
- Keep headers readable: normally 5-35 words. Do not truncate a sentence just
  to fit a graph node; the UI can show full text in the detail panel.
- Preserve the atom's meaning and type. Do not add claims not present in the source excerpt.
- Prefer a clear noun phrase or short sentence over copied surrounding prose.
- Drop atoms that are just equation-neighbor fragments, citations, captions, section transitions, or incomplete clauses.
- Drop atoms that require too much context to state concisely and faithfully.
- Return every atom_id exactly once. No prose. No markdown.

Header examples:
- KEEP source "We use scaled dot-product attention to avoid large dot products
  pushing softmax into regions with small gradients."
  -> "Scaled dot-product attention stabilizes softmax gradients"
- KEEP source "The decoder is auto-regressive, masking future positions during
  training."
  -> "Decoder self-attention masks future positions"
- KEEP source "Sinusoidal encodings may allow the model to extrapolate to
  sequence lengths longer than those seen during training."
  -> "Sinusoidal positional encodings support length extrapolation"
- KEEP source "Our algorithm assumes the graph is connected."
  -> "Algorithm assumes connected input graphs"
- DROP source "Transformer decoder has six layers and"
  reason: dangling fragment, not a complete concept.
- DROP source "Research goal make sequence generation less"
  reason: ungrammatical clipped motivation, not a reviewable atom.
- DROP source "where $d_k$ is the dimension of the keys"
  reason: local notation explanation, not a standalone claim.
- DROP source "The rest of this section is organized as follows"
  reason: section transition.
"""

_CRITIC_SYSTEM_PROMPT = (
    "You are a strict critic for source-grounded review-DAG atom candidates. "
    "You remove fragments, duplicates, background-only statements, overly broad "
    "summary nodes, and candidates that are not faithful to their source quote. "
    "You may rewrite headers, but you never invent claims. Output JSON only."
)

_CRITIC_PROMPT_TMPL = """Review these atom candidates before they become final ResearchAtom objects.

Candidates:
{candidates_json}

Return a JSON object:
{{
  "decisions": [
    {{
      "candidate_id": "cand_001",
      "action": "keep|drop|rewrite|split|merge",
      "new_text": "<required for rewrite; complete clean English atom statement with no raw LaTeX>",
      "drop_reason": "<required for drop>",
      "merge_with": null,
      "reviewability": "reviewable|learning_only|background|drop",
      "checkability": "symbolic|numeric|citation|proof_only|conceptual|not_checkable"
    }}
  ],
  "warnings": []
}}

Rules:
- Return exactly one decision for every candidate_id.
- Drop dangling fragments, equation-neighbor snippets, captions, section
  transitions, generic background, and claims that are too broad to review.
- Rewrite only when the source quote clearly supports the new text.
- `new_text` must be complete clean English and must not contain raw LaTeX
  macros. Translate notation into words; do not copy formula fragments into
  display text.
- Mark definitions/examples/reader-helpful concepts as `learning_only` unless
  they are explicit assumptions or load-bearing review claims.
- Keep reviewable candidates specific: one claim/concept only.
- Do not optimize for the smallest possible graph. Preserve grounded central
  paper content even when it is conceptual or reader-facing.
- If two candidates are duplicates, keep the better grounded candidate and
  set `action=merge` with `merge_with` pointing at the kept candidate.
- Prefer dropping over keeping a questionable review-DAG node.
- Return ONLY the JSON object. No prose. No markdown.
"""

_QUOTE_REPAIR_SYSTEM_PROMPT = (
    "You repair atom candidate source quotes by returning shorter exact quotes "
    "from the provided section text. Do not paraphrase. Output JSON only."
)

_QUOTE_REPAIR_PROMPT_TMPL = """Repair low-confidence source quotes for these candidates.

Section text:
\"\"\"
{sections_text}
\"\"\"

Candidates:
{candidates_json}

Return a JSON object:
{{
  "quotes": [
    {{
      "candidate_id": "cand_001",
      "source_quote": "<shorter exact quote copied verbatim from section text>"
    }}
  ],
  "warnings": []
}}

Rules:
- Return one quote entry for every candidate_id.
- The replacement `source_quote` must appear verbatim in the section text.
- Prefer the shortest quote that still grounds the candidate.
- If no exact quote exists, return an empty string for that candidate.
- Return ONLY the JSON object. No prose. No markdown.
"""

_DANGLING_HEADER_ENDINGS = {
    "a",
    "an",
    "the",
    "at",
    "am",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "can",
    "could",
    "should",
    "would",
    "may",
    "might",
    "must",
    "will",
    "shall",
    "do",
    "does",
    "did",
    "has",
    "have",
    "had",
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
_MAIN_DAG_MIN_SPAN_CONFIDENCE = 0.70
_REPAIRABLE_SPAN_MIN_CONFIDENCE = 0.40


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
        paper = context.parsed_paper
        if paper is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"atoms": [], "warnings": []},
                confidence=0.0,
                error="parsed_paper missing from context",
            )

        deterministic = self._extract_environment_candidates(paper)
        warnings: list[str] = []
        batch_count = len(_section_batches(paper, self._max_section_chars))
        await self._emit_progress(
            _candidates_to_research_atoms(paper, deterministic),
            {
                "stage": "Extracting deterministic atoms",
                "batches_completed": 0,
                "batches_total": batch_count,
            },
        )

        try:
            llm_candidates, llm_warnings = await self._extract_with_llm(paper, deterministic)
            warnings.extend(llm_warnings)
        except Exception as exc:
            logger.exception("LLM atom extraction failed")
            warnings.append(f"llm_extraction_failed: {exc}")
            llm_candidates = []

        candidates = _merge_candidate_lists(deterministic, llm_candidates)
        candidates, resolve_warnings = _resolve_candidate_spans(paper, candidates)
        warnings.extend(resolve_warnings)
        if _repairable_span_candidates(candidates):
            try:
                candidates, repair_warnings = await self._repair_candidate_quotes_with_llm(
                    paper,
                    candidates,
                )
                warnings.extend(repair_warnings)
            except Exception as exc:
                logger.exception("LLM atom quote repair failed")
                warnings.append(f"llm_atom_quote_repair_failed: {exc}")
        candidates, grounding_warnings = _filter_grounded_candidates(candidates)
        warnings.extend(grounding_warnings)

        if candidates:
            try:
                candidates, critic_warnings = await self._critic_repair_candidates(candidates)
                warnings.extend(critic_warnings)
            except Exception as exc:
                logger.exception("LLM atom critic failed")
                warnings.append(f"llm_atom_critic_failed: {exc}")
                candidates = _local_candidate_filter(candidates, warnings)

        candidates = _dedupe_candidates(candidates, warnings)
        atoms = _candidates_to_research_atoms(paper, candidates)

        if self._normalize_headers and atoms:
            try:
                atoms, normalization_warnings = await self._normalize_headers_with_llm(atoms)
                warnings.extend(normalization_warnings)
                await self._emit_progress(
                    atoms,
                    {
                        "stage": "Normalizing atom headers",
                        "batches_completed": 1,
                        "batches_total": 1,
                    },
                )
            except Exception as exc:
                logger.exception("LLM atom header normalization failed")
                warnings.append(f"llm_header_normalization_failed: {exc}")
        atoms, final_header_warnings = _finalize_atom_headers(atoms)
        warnings.extend(final_header_warnings)
        result = AtomExtractionResult(
            paper_id=paper.paper_id,
            atoms=atoms,
            warnings=warnings,
        )

        confidence = 0.85 if atoms else 0.2
        return AgentResult(
            agent_id=self.agent_id,
            status="success" if atoms else "inconclusive",
            output=result.model_dump(),
            confidence=confidence,
        )

    # --------------------------------------------------------------- pass A

    def _extract_environment_candidates(self, paper: ParsedPaper) -> list[AtomCandidate]:
        candidates: list[AtomCandidate] = []
        assembled = paper.assembled_tex or ""
        if not assembled:
            return candidates

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
            candidate_id = f"cand_env_{counter:03d}"
            importance = _DEFAULT_IMPORTANCE.get(atom_type, AtomImportance.MEDIUM)
            reviewability = _default_reviewability(atom_type, importance)
            checkability = _default_checkability(atom_type)
            span = SourceSpan(
                paper_id=paper.paper_id,
                section_id=section_id,
                tex_start=tex_start,
                tex_end=tex_end,
                raw_excerpt=cleaned[:1000],
                match_confidence=1.0,
            )

            candidates.append(
                AtomCandidate(
                    candidate_id=candidate_id,
                    paper_id=paper.paper_id,
                    atom_type=atom_type,
                    source_quote=cleaned[:2000],
                    text=cleaned[:2000],
                    section_heading=section_heading,
                    importance=importance,
                    reviewability=reviewability,
                    checkability=checkability,
                    confidence=0.95,
                    role_in_paper=f"{atom_type.value} from \\begin{{{raw_env}}} environment"
                    + (f" (label {label})" if label else ""),
                    source_span=span,
                )
            )

        return candidates

    # --------------------------------------------------------------- pass B

    async def _extract_with_llm(
        self,
        paper: ParsedPaper,
        seen: list[AtomCandidate],
    ) -> tuple[list[AtomCandidate], list[str]]:
        batches = _section_batches(paper, self._max_section_chars)
        if not batches:
            return [], ["llm_skipped: empty section text"]

        client = self._get_client()
        candidates: list[AtomCandidate] = []
        warnings: list[str] = []
        counter = 0

        for batch_idx, sections_text in enumerate(batches, start=1):
            seen_block = _format_seen_block([*seen, *candidates]) or "(none)"
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
                max_tokens=7000,
            )
            raw = response.choices[0].message.content or ""
            data, parse_warning = _loads_json_object(raw)
            if data is None:
                warnings.append(f"llm_json_parse_failed_batch_{batch_idx}: {parse_warning}")
                continue
            if parse_warning:
                warnings.append(f"llm_json_repaired_batch_{batch_idx}: {parse_warning}")

            entries = _candidate_entries_from_response(data)
            if not isinstance(entries, list):
                warnings.append(f"llm_response_missing_candidates_array_batch_{batch_idx}")
                continue

            batch_warnings = data.get("warnings") if isinstance(data, dict) else None
            if isinstance(batch_warnings, list):
                warnings.extend(str(w) for w in batch_warnings if str(w).strip())

            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                candidate = _candidate_from_llm_entry(entry, paper, counter)
                if candidate is None:
                    continue
                candidates.append(candidate)
                counter += 1

            await self._emit_progress(
                _candidates_to_research_atoms(
                    paper,
                    _dedupe_candidates(
                        _merge_candidate_lists(seen, candidates),
                        warnings=[],
                    ),
                ),
                {
                    "stage": f"Extracting atom candidates ({batch_idx}/{len(batches)})",
                    "batches_completed": batch_idx,
                    "batches_total": len(batches),
                },
            )

        return candidates, warnings

    async def _critic_repair_candidates(
        self,
        candidates: list[AtomCandidate],
    ) -> tuple[list[AtomCandidate], list[str]]:
        client = self._get_client()
        warnings: list[str] = []
        decisions: dict[str, dict[str, Any]] = {}

        for batch_idx, batch in enumerate(_candidate_batches(candidates, _MAX_HEADER_BATCH_ATOMS), start=1):
            payload = [
                {
                    "candidate_id": candidate.candidate_id,
                    "atom_type": candidate.atom_type.value,
                    "section_heading": candidate.section_heading,
                    "source_quote": candidate.source_quote[:900],
                    "text": candidate.text[:600],
                    "reviewability": candidate.reviewability.value,
                    "checkability": candidate.checkability.value,
                    "claim_scope": candidate.claim_scope,
                    "why_this_is_an_atom": candidate.why_this_is_an_atom,
                    "confidence": candidate.confidence,
                    "span_confidence": (
                        candidate.source_span.match_confidence
                        if candidate.source_span is not None
                        else None
                    ),
                }
                for candidate in batch
            ]
            prompt = _CRITIC_PROMPT_TMPL.format(
                candidates_json=json.dumps(payload, ensure_ascii=False, indent=2)
            )
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _CRITIC_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=7000,
            )
            raw = response.choices[0].message.content or ""
            data, parse_warning = _loads_json_object(raw)
            if data is None:
                warnings.append(f"llm_critic_json_parse_failed_batch_{batch_idx}: {parse_warning}")
                continue
            if parse_warning:
                warnings.append(f"llm_critic_json_repaired_batch_{batch_idx}: {parse_warning}")

            entries = data.get("decisions") if isinstance(data, dict) else None
            if not isinstance(entries, list):
                warnings.append(f"llm_critic_response_missing_decisions_batch_{batch_idx}")
                continue

            batch_warnings = data.get("warnings") if isinstance(data, dict) else None
            if isinstance(batch_warnings, list):
                warnings.extend(str(w) for w in batch_warnings if str(w).strip())

            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                candidate_id = str(entry.get("candidate_id") or "").strip()
                if candidate_id:
                    decisions[candidate_id] = entry

        if not decisions:
            warnings.append("llm_critic_returned_no_decisions")
            return _local_candidate_filter(candidates, warnings), warnings

        cleaned: list[AtomCandidate] = []
        kept_ids: set[str] = set()
        for candidate in candidates:
            decision = decisions.get(candidate.candidate_id)
            if decision is None:
                warnings.append(f"llm_critic_missing_decision: {candidate.candidate_id}")
                if _locally_keep_candidate(candidate):
                    cleaned.append(candidate)
                    kept_ids.add(candidate.candidate_id)
                continue

            action = str(decision.get("action") or "keep").strip().lower()
            if action in {"drop", "dropped"}:
                reason = str(decision.get("drop_reason") or "").strip()
                warnings.append(f"critic_dropped_candidate: {candidate.candidate_id} {reason}".strip())
                continue
            if action == "merge":
                target = str(decision.get("merge_with") or "").strip()
                if target and target in kept_ids:
                    warnings.append(f"critic_merged_candidate: {candidate.candidate_id} -> {target}")
                    continue
                # If the merge target is not already kept, keep this candidate
                # and let deterministic dedupe make the final call.

            update: dict[str, Any] = {}
            reviewability = _coerce_reviewability(decision.get("reviewability"))
            checkability = _coerce_checkability(decision.get("checkability"))
            if reviewability is not None:
                update["reviewability"] = reviewability
            if checkability is not None:
                update["checkability"] = checkability

            new_text = _compact_header(str(decision.get("new_text") or ""))
            if action in {"rewrite", "split"} and _valid_atom_header(new_text):
                update["text"] = new_text
                update["normalized_text"] = new_text

            updated = candidate.model_copy(update=update) if update else candidate
            if _locally_keep_candidate(updated):
                cleaned.append(updated)
                kept_ids.add(updated.candidate_id)
            else:
                warnings.append(f"critic_local_drop_after_decision: {candidate.candidate_id}")

        return cleaned, warnings

    async def _repair_candidate_quotes_with_llm(
        self,
        paper: ParsedPaper,
        candidates: list[AtomCandidate],
    ) -> tuple[list[AtomCandidate], list[str]]:
        repairable = _repairable_span_candidates(candidates)
        if not repairable:
            return candidates, []

        client = self._get_client()
        warnings: list[str] = []
        payload = [
            {
                "candidate_id": candidate.candidate_id,
                "atom_type": candidate.atom_type.value,
                "section_heading": candidate.section_heading,
                "current_source_quote": candidate.source_quote[:800],
                "text": candidate.text[:500],
                "span_confidence": (
                    candidate.source_span.match_confidence
                    if candidate.source_span is not None
                    else 0.0
                ),
            }
            for candidate in repairable
        ]
        prompt = _QUOTE_REPAIR_PROMPT_TMPL.format(
            sections_text=_sections_text_for_candidates(paper, repairable),
            candidates_json=json.dumps(payload, ensure_ascii=False, indent=2),
        )
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _QUOTE_REPAIR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=2500,
        )
        raw = response.choices[0].message.content or ""
        data, parse_warning = _loads_json_object(raw)
        if data is None:
            return candidates, [f"llm_quote_repair_json_parse_failed: {parse_warning}"]
        if parse_warning:
            warnings.append(f"llm_quote_repair_json_repaired: {parse_warning}")

        quote_entries = data.get("quotes") if isinstance(data, dict) else None
        if not isinstance(quote_entries, list):
            return candidates, ["llm_quote_repair_missing_quotes_array"]

        batch_warnings = data.get("warnings") if isinstance(data, dict) else None
        if isinstance(batch_warnings, list):
            warnings.extend(str(w) for w in batch_warnings if str(w).strip())

        quote_by_id: dict[str, str] = {}
        for entry in quote_entries:
            if not isinstance(entry, dict):
                continue
            candidate_id = str(entry.get("candidate_id") or "").strip()
            quote = str(entry.get("source_quote") or "").strip()
            if candidate_id:
                quote_by_id[candidate_id] = quote

        repaired: list[AtomCandidate] = []
        repairable_ids = {candidate.candidate_id for candidate in repairable}
        for candidate in candidates:
            if candidate.candidate_id not in repairable_ids:
                repaired.append(candidate)
                continue
            old_conf = candidate.source_span.match_confidence if candidate.source_span else 0.0
            quote = quote_by_id.get(candidate.candidate_id, "")
            if not quote:
                repaired.append(candidate)
                continue
            span = resolve_span(paper, quote, candidate.section_heading)
            if span.match_confidence > old_conf:
                warnings.append(
                    f"repaired_span_quote: {candidate.candidate_id} "
                    f"old={old_conf:.2f} new={span.match_confidence:.2f}"
                )
                repaired.append(
                    candidate.model_copy(
                        update={
                            "source_quote": quote,
                            "source_span": span,
                            "section_heading": candidate.section_heading
                            or _section_heading_for_id(paper, span.section_id),
                        }
                    )
                )
            else:
                repaired.append(candidate)

        return repaired, warnings

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
                messages=[
                    {"role": "system", "content": _HEADER_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=4500,
            )
            raw = response.choices[0].message.content or ""
            data, parse_warning = _loads_json_object(raw)
            if data is None:
                warnings.append(f"llm_header_json_parse_failed_batch_{batch_idx}: {parse_warning}")
                continue
            if parse_warning:
                warnings.append(f"llm_header_json_repaired_batch_{batch_idx}: {parse_warning}")

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


def _format_seen_block(seen: list[AtomCandidate]) -> str:
    if not seen:
        return ""
    lines: list[str] = []
    for candidate in seen[:30]:
        snippet = candidate.text[:140].replace("\n", " ")
        lines.append(
            f"- {candidate.atom_type.value} ({candidate.section_heading or '?'}): {snippet}"
        )
    if len(seen) > 30:
        lines.append(f"- ... ({len(seen) - 30} more candidates)")
    return "\n".join(lines)


def _candidate_entries_from_response(data: Any) -> Optional[list[Any]]:
    if not isinstance(data, dict):
        return None
    entries = data.get("candidates")
    if isinstance(entries, list):
        return entries
    # Tolerate the older mocked shape in offline tests.
    entries = data.get("atoms")
    return entries if isinstance(entries, list) else None


def _loads_json_object(raw: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    try:
        data = json.loads(raw)
        return (data if isinstance(data, dict) else None), None
    except json.JSONDecodeError as first_exc:
        repaired = _repair_json_backslashes(raw)
        if repaired == raw:
            return None, str(first_exc)
        try:
            data = json.loads(repaired)
        except json.JSONDecodeError as second_exc:
            if repair_json is None:
                return None, f"{first_exc}; repair_failed={second_exc}"
            try:
                repair_output = repair_json(raw)
                data = json.loads(repair_output)
            except Exception as repair_exc:  # noqa: BLE001
                return None, f"{first_exc}; repair_failed={second_exc}; json_repair_failed={repair_exc}"
        if not isinstance(data, dict):
            return None, "json root was not an object"
        return data, str(first_exc)


def _repair_json_backslashes(raw: str) -> str:
    # Model outputs that include LaTeX often contain JSON-invalid escapes such
    # as `\dmodel` or malformed `\u` fragments. Preserve the literal backslash
    # by escaping only sequences JSON cannot legally decode.
    text = re.sub(r"\\u(?![0-9a-fA-F]{4})", r"\\\\u", raw)
    text = re.sub(r"\\(?![\"\\/bfnrtu])", r"\\\\", text)
    return text


def _candidate_from_llm_entry(
    entry: dict[str, Any],
    paper: ParsedPaper,
    index: int,
) -> Optional[AtomCandidate]:
    atom_type = _coerce_atom_type(entry.get("atom_type"))
    if atom_type is None:
        return None

    source_quote = (entry.get("source_quote") or "").strip()
    text = (entry.get("text") or source_quote).strip()
    if not source_quote and not text:
        return None
    if not source_quote:
        source_quote = text

    importance = _coerce_importance(entry.get("importance"))
    confidence = _coerce_confidence(entry.get("confidence"), default=0.6)
    reviewability = _coerce_reviewability(entry.get("reviewability")) or _default_reviewability(
        atom_type,
        importance,
    )
    checkability = _coerce_checkability(entry.get("checkability")) or _default_checkability(
        atom_type,
    )

    candidate_id = f"cand_llm_{index + 1:03d}"
    return AtomCandidate(
        candidate_id=candidate_id,
        paper_id=paper.paper_id,
        atom_type=atom_type,
        source_quote=source_quote[:2000],
        text=text[:2000],
        normalized_text=(entry.get("normalized_text") or None),
        section_heading=(entry.get("section_heading") or None),
        importance=importance,
        reviewability=reviewability,
        checkability=checkability,
        claim_scope=(entry.get("claim_scope") or None),
        why_this_is_an_atom=(entry.get("why_this_is_an_atom") or None),
        role_in_paper=(entry.get("role_in_paper") or None),
        assumptions=_coerce_str_list(entry.get("assumptions")),
        conclusions=_coerce_str_list(entry.get("conclusions")),
        key_terms=_coerce_str_list(entry.get("key_terms")),
        symbols=_coerce_str_list(entry.get("symbols")),
        dependency_hints=_coerce_str_list(entry.get("dependency_hints")),
        equation_refs=_coerce_str_list(entry.get("equation_refs")),
        citation_refs=_coerce_str_list(entry.get("citation_refs")),
        confidence=confidence,
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


def _coerce_reviewability(value: Any) -> Optional[AtomReviewability]:
    if isinstance(value, AtomReviewability):
        return value
    if isinstance(value, str):
        key = value.strip().lower().replace(" ", "_").replace("-", "_")
        try:
            return AtomReviewability(key)
        except ValueError:
            synonyms = {
                "reader_only": AtomReviewability.LEARNING_ONLY,
                "learning": AtomReviewability.LEARNING_ONLY,
                "teaching": AtomReviewability.LEARNING_ONLY,
                "not_reviewable": AtomReviewability.LEARNING_ONLY,
                "ignore": AtomReviewability.DROP,
            }
            return synonyms.get(key)
    return None


def _coerce_checkability(value: Any) -> Optional[AtomCheckability]:
    if isinstance(value, AtomCheckability):
        return value
    if isinstance(value, str):
        key = value.strip().lower().replace(" ", "_").replace("-", "_")
        try:
            return AtomCheckability(key)
        except ValueError:
            synonyms = {
                "proof": AtomCheckability.PROOF_ONLY,
                "math": AtomCheckability.SYMBOLIC,
                "empirical": AtomCheckability.NUMERIC,
                "citation_context": AtomCheckability.CITATION,
                "uncheckable": AtomCheckability.NOT_CHECKABLE,
            }
            return synonyms.get(key)
    return None


def _default_reviewability(
    atom_type: ResearchAtomType,
    importance: AtomImportance,
) -> AtomReviewability:
    if atom_type in {
        ResearchAtomType.DEFINITION,
        ResearchAtomType.EXAMPLE,
        ResearchAtomType.COUNTEREXAMPLE,
        ResearchAtomType.PROOF_STEP,
        ResearchAtomType.TECHNIQUE,
        ResearchAtomType.RELATED_WORK_CLAIM,
    }:
        return AtomReviewability.LEARNING_ONLY
    if importance == AtomImportance.LOW:
        return AtomReviewability.LEARNING_ONLY
    return AtomReviewability.REVIEWABLE


def _default_checkability(atom_type: ResearchAtomType) -> AtomCheckability:
    if atom_type in {
        ResearchAtomType.THEOREM,
        ResearchAtomType.LEMMA,
        ResearchAtomType.COROLLARY,
        ResearchAtomType.PROPOSITION,
        ResearchAtomType.PROOF_STEP,
    }:
        return AtomCheckability.PROOF_ONLY
    if atom_type in {ResearchAtomType.BOUND, ResearchAtomType.ASSERTION}:
        return AtomCheckability.CONCEPTUAL
    if atom_type == ResearchAtomType.RELATED_WORK_CLAIM:
        return AtomCheckability.CITATION
    if atom_type in {ResearchAtomType.ALGORITHM, ResearchAtomType.CONSTRUCTION}:
        return AtomCheckability.CONCEPTUAL
    return AtomCheckability.NOT_CHECKABLE


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
    return text.strip(" -:;,.")


def _valid_atom_header(value: str) -> bool:
    text = _compact_header(value)
    if not text:
        return False
    words = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text)
    if len(words) < 3:
        return False
    if len(text) > 500:
        return False
    if _contains_raw_latex(text):
        return False
    last = words[-1].lower()
    if last in _DANGLING_HEADER_ENDINGS:
        return False
    if re.search(r"(?:\bat\b|\bto\b|\band\b|\bby\b)\s*$", text, flags=re.IGNORECASE):
        return False
    if text.count("$") % 2 == 1:
        return False
    if _ends_with_symbol_like_fragment(words[-1]):
        return False
    if _looks_like_unfinished_clause(text):
        return False
    return True


def _locally_keepable_header(value: str) -> bool:
    text = _compact_header(value)
    if _valid_atom_header(text):
        return True
    words = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text)
    return (
        len(words) >= 6
        and (words[-1].lower() not in _DANGLING_HEADER_ENDINGS)
        and not _contains_raw_latex(text)
        and not _ends_with_symbol_like_fragment(words[-1])
        and not _looks_like_unfinished_clause(text)
    )


def _finalize_atom_headers(atoms: list[ResearchAtom]) -> tuple[list[ResearchAtom], list[str]]:
    cleaned: list[ResearchAtom] = []
    warnings: list[str] = []
    for atom in atoms:
        header = _compact_header(atom.text)
        if _valid_atom_header(header):
            cleaned.append(atom.model_copy(update={"text": header}))
            continue
        repaired = _header_from_source_excerpt(atom)
        if repaired and _valid_atom_header(repaired):
            warnings.append(f"final_header_repaired: {atom.atom_id}")
            cleaned.append(
                atom.model_copy(
                    update={
                        "text": repaired,
                        "normalized_text": repaired,
                    }
                )
            )
            continue
        warnings.append(f"final_header_dropped: {atom.atom_id} {header[:80]}")
    return _renumber_atoms(cleaned), warnings


def _header_from_source_excerpt(atom: ResearchAtom) -> str:
    excerpt = re.sub(r"\s+", " ", atom.source_span.raw_excerpt or "").strip()
    if not excerpt:
        return ""
    if _math_heavy_excerpt(excerpt):
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", excerpt)
    for sentence in sentences:
        header = _compact_header(_strip_inline_tex_noise(sentence))
        if 24 <= len(header) <= 180:
            return header
    return _compact_header(_strip_inline_tex_noise(excerpt))


def _strip_inline_tex_noise(value: str) -> str:
    text = str(value or "")
    replacements = {
        r"\mathbb{R}": "real numbers",
        r"\mathbb{N}": "natural numbers",
        r"\mathbb{Z}": "integers",
        r"\mathcal{N}": "normal distribution",
        r"\in": " in ",
        r"\geq": " is at least ",
        r"\ge": " is at least ",
        r"\leq": " is at most ",
        r"\le": " is at most ",
        r"\to": " to ",
        r"\rightarrow": " to ",
        r"\sim": " is distributed as ",
    }
    for needle, replacement in replacements.items():
        text = text.replace(needle, replacement)
    text = text.replace("$", " ")
    text = re.sub(r"\\[A-Za-z@]+\*?", "", text)
    text = text.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", text).strip()


def _math_heavy_excerpt(value: str) -> bool:
    text = value.strip()
    if text.startswith("$") and text.endswith("$"):
        return True
    math_chars = sum(1 for ch in text if ch in "\\{}_^=|")
    return len(text) > 0 and (math_chars / max(len(text), 1)) > 0.12


def _contains_raw_latex(value: str) -> bool:
    text = str(value or "")
    if "$" in text:
        return True
    if re.search(r"\\[A-Za-z@]+", text):
        return True
    if re.search(r"\b(?:mathcal|mathrm|mathbf|frac|sqrt|qPhi|pT|pA|bphi|bT|bz|bx)\b", text):
        return True
    return False


def _ends_with_symbol_like_fragment(word: str) -> bool:
    if len(word) <= 2:
        return False
    if re.search(r"[a-z][A-Z]", word):
        return True
    if re.fullmatch(r"[A-Za-z]+(?:Phi|Theta|Sigma|phi|theta|sigma|T|X|Z)", word):
        return True
    return False


def _looks_like_unfinished_clause(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:because|since|where|when|if|given|with respect to|over|for|under)\s*$",
            text,
            flags=re.IGNORECASE,
        )
    )


def _candidate_batches(
    candidates: list[AtomCandidate],
    batch_size: int,
) -> list[list[AtomCandidate]]:
    size = max(1, batch_size)
    return [candidates[idx : idx + size] for idx in range(0, len(candidates), size)]


def _merge_candidate_lists(
    deterministic: list[AtomCandidate],
    llm_candidates: list[AtomCandidate],
) -> list[AtomCandidate]:
    """Drop LLM candidates that overlap deterministic TeX environment spans."""
    merged: list[AtomCandidate] = list(deterministic)

    det_ranges: list[tuple[int, int]] = []
    for candidate in deterministic:
        if candidate.source_span is None:
            continue
        s = candidate.source_span.tex_start
        e = candidate.source_span.tex_end
        if s is not None and e is not None:
            det_ranges.append((s, e))

    for candidate in llm_candidates:
        span = candidate.source_span
        s = span.tex_start if span is not None else None
        e = span.tex_end if span is not None else None
        overlap = False
        if s is not None and e is not None:
            for ds, de in det_ranges:
                if not (e < ds or s > de):
                    overlap = True
                    break
        if overlap:
            continue

        # Also drop near-duplicate text bodies.
        if any(_text_overlap(candidate.text, d.text) for d in deterministic):
            continue

        merged.append(candidate)

    return _renumber_candidates(merged)


def _resolve_candidate_spans(
    paper: ParsedPaper,
    candidates: list[AtomCandidate],
) -> tuple[list[AtomCandidate], list[str]]:
    resolved: list[AtomCandidate] = []
    warnings: list[str] = []

    for candidate in candidates:
        span = candidate.source_span or resolve_span(
            paper,
            candidate.source_quote,
            candidate.section_heading,
        )
        resolved.append(
            candidate.model_copy(
                update={
                    "source_span": span,
                    "section_heading": candidate.section_heading
                    or _section_heading_for_id(paper, span.section_id),
                }
            )
        )
        if _REPAIRABLE_SPAN_MIN_CONFIDENCE <= span.match_confidence < _MAIN_DAG_MIN_SPAN_CONFIDENCE:
            warnings.append(
                f"span_needs_quote_repair: {candidate.candidate_id} confidence={span.match_confidence:.2f}"
            )

    return resolved, warnings


def _repairable_span_candidates(candidates: list[AtomCandidate]) -> list[AtomCandidate]:
    return [
        candidate
        for candidate in candidates
        if candidate.source_span is not None
        and _REPAIRABLE_SPAN_MIN_CONFIDENCE
        <= candidate.source_span.match_confidence
        < _MAIN_DAG_MIN_SPAN_CONFIDENCE
    ]


def _filter_grounded_candidates(
    candidates: list[AtomCandidate],
) -> tuple[list[AtomCandidate], list[str]]:
    grounded: list[AtomCandidate] = []
    warnings: list[str] = []

    for candidate in candidates:
        span = candidate.source_span
        confidence = span.match_confidence if span is not None else 0.0
        if confidence >= _MAIN_DAG_MIN_SPAN_CONFIDENCE:
            grounded.append(candidate)
        else:
            warnings.append(
                f"dropped_low_confidence_span: {candidate.candidate_id} confidence={confidence:.2f}"
            )

    return grounded, warnings


def _ground_candidates(
    paper: ParsedPaper,
    candidates: list[AtomCandidate],
) -> tuple[list[AtomCandidate], list[str]]:
    resolved, resolve_warnings = _resolve_candidate_spans(paper, candidates)
    grounded, grounding_warnings = _filter_grounded_candidates(resolved)
    return grounded, [*resolve_warnings, *grounding_warnings]


def _sections_text_for_candidates(
    paper: ParsedPaper,
    candidates: list[AtomCandidate],
) -> str:
    section_ids = {
        candidate.source_span.section_id
        for candidate in candidates
        if candidate.source_span is not None and candidate.source_span.section_id
    }
    chunks: list[str] = []
    for section in paper.sections:
        if section_ids and section.section_id not in section_ids:
            continue
        if not section.content.strip():
            continue
        chunks.append(f"## {section.heading} [{section.section_id}]\n{section.content.strip()}")
    return "\n\n".join(chunks)[:18000]


def _local_candidate_filter(
    candidates: list[AtomCandidate],
    warnings: list[str],
) -> list[AtomCandidate]:
    kept: list[AtomCandidate] = []
    for candidate in candidates:
        if _locally_keep_candidate(candidate):
            kept.append(candidate)
        else:
            warnings.append(f"local_candidate_filter_dropped: {candidate.candidate_id}")
    return kept


def _locally_keep_candidate(candidate: AtomCandidate) -> bool:
    if candidate.reviewability in {
        AtomReviewability.DROP,
        AtomReviewability.BACKGROUND,
    }:
        return False
    if candidate.source_span is None:
        return False
    if candidate.source_span.match_confidence < _MAIN_DAG_MIN_SPAN_CONFIDENCE:
        return False
    text = _compact_header(candidate.text)
    if _valid_atom_header(text):
        return True
    words = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text)
    return len(words) >= 6 and (words[-1].lower() not in _DANGLING_HEADER_ENDINGS)


def _dedupe_candidates(
    candidates: list[AtomCandidate],
    warnings: list[str],
) -> list[AtomCandidate]:
    deduped: list[AtomCandidate] = []
    for candidate in candidates:
        duplicate_of: Optional[AtomCandidate] = None
        for existing in deduped:
            if _candidate_duplicate(candidate, existing):
                duplicate_of = existing
                break
        if duplicate_of is not None:
            warnings.append(
                f"deduped_candidate: {candidate.candidate_id} -> {duplicate_of.candidate_id}"
            )
            continue
        deduped.append(candidate)
    return _renumber_candidates(deduped)


def _candidate_duplicate(a: AtomCandidate, b: AtomCandidate) -> bool:
    if a.atom_type == b.atom_type and _text_overlap(a.text, b.text):
        return True
    if a.source_quote and b.source_quote and _text_overlap(a.source_quote, b.source_quote):
        return True
    return False


def _renumber_candidates(candidates: list[AtomCandidate]) -> list[AtomCandidate]:
    renumbered: list[AtomCandidate] = []
    for idx, candidate in enumerate(candidates, start=1):
        prefix = "cand_env" if candidate.candidate_id.startswith("cand_env") else "cand_llm"
        renumbered.append(
            candidate.model_copy(update={"candidate_id": f"{prefix}_{idx:03d}"})
        )
    return renumbered


def _candidates_to_research_atoms(
    paper: ParsedPaper,
    candidates: list[AtomCandidate],
) -> list[ResearchAtom]:
    atoms: list[ResearchAtom] = []
    for idx, candidate in enumerate(candidates, start=1):
        span = candidate.source_span or resolve_span(
            paper,
            candidate.source_quote,
            candidate.section_heading,
        )
        atoms.append(
            ResearchAtom(
                atom_id=f"atom_{idx:03d}",
                paper_id=paper.paper_id,
                atom_type=candidate.atom_type,
                text=_compact_header(candidate.text) or candidate.text[:2000],
                normalized_text=candidate.normalized_text,
                section_id=span.section_id,
                section_heading=candidate.section_heading
                or _section_heading_for_id(paper, span.section_id),
                source_span=span,
                extraction_confidence=candidate.confidence,
                importance=candidate.importance,
                reviewability=candidate.reviewability,
                checkability=candidate.checkability,
                claim_scope=candidate.claim_scope,
                why_this_is_an_atom=candidate.why_this_is_an_atom,
                role_in_paper=candidate.role_in_paper,
                assumptions=candidate.assumptions,
                conclusions=candidate.conclusions,
                key_terms=candidate.key_terms,
                symbols=candidate.symbols,
                dependency_hints=candidate.dependency_hints,
                equation_refs=candidate.equation_refs,
                citation_refs=candidate.citation_refs,
            )
        )
    return atoms


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
