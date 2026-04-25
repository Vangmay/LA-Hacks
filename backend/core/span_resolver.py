"""Resolve a `source_quote` to a `SourceSpan` against a `ParsedPaper`.

The strategy is intentionally limited:
1. Exact match in `raw_text`.
2. Whitespace-normalized match in `raw_text`.
3. Prefix match (first 80 chars, trimmed of trailing punctuation).
4. Fall back to a low-confidence span that still keeps the raw excerpt so
   the frontend has something to render.

No LLM, no fuzzy similarity. If we can't anchor a quote we report low
match confidence rather than fabricating a position.
"""
from __future__ import annotations

import re
from typing import Optional

from models import ParsedPaper, SourceSpan

_WS_RE = re.compile(r"\s+")


def resolve_span(
    paper: ParsedPaper,
    source_quote: str,
    section_hint: Optional[str] = None,
) -> SourceSpan:
    quote = (source_quote or "").strip()
    section_id = _section_id_for_hint(paper, section_hint)

    if not quote:
        return SourceSpan(
            paper_id=paper.paper_id,
            section_id=section_id,
            raw_excerpt="",
            match_confidence=0.0,
        )

    raw = paper.raw_text

    pos = raw.find(quote)
    if pos != -1:
        return SourceSpan(
            paper_id=paper.paper_id,
            section_id=section_id or _section_id_for_offset(paper, pos),
            char_start=pos,
            char_end=pos + len(quote),
            raw_excerpt=quote,
            match_confidence=1.0,
        )

    # Whitespace-normalized match.
    norm_quote = _WS_RE.sub(" ", quote).strip()
    norm_raw = _WS_RE.sub(" ", raw)
    pos = norm_raw.find(norm_quote)
    if pos != -1 and norm_quote:
        # Map normalized position back to raw_text position.
        approx = _approximate_raw_position(raw, pos, len(norm_quote))
        return SourceSpan(
            paper_id=paper.paper_id,
            section_id=section_id or _section_id_for_offset(paper, approx),
            char_start=approx,
            char_end=min(len(raw), approx + len(quote)),
            raw_excerpt=quote,
            match_confidence=0.85,
        )

    # Prefix match (first 80 chars, trimmed).
    prefix = quote[:80].rstrip(" .,;:")
    if len(prefix) >= 20:
        pos = raw.find(prefix)
        if pos != -1:
            return SourceSpan(
                paper_id=paper.paper_id,
                section_id=section_id or _section_id_for_offset(paper, pos),
                char_start=pos,
                char_end=pos + len(quote),
                raw_excerpt=quote,
                match_confidence=0.7,
            )

    return SourceSpan(
        paper_id=paper.paper_id,
        section_id=section_id,
        raw_excerpt=quote,
        match_confidence=0.3,
    )


def _section_id_for_hint(paper: ParsedPaper, hint: Optional[str]) -> Optional[str]:
    if not hint:
        return None
    needle = hint.strip().lower()
    for section in paper.sections:
        if section.heading.strip().lower() == needle:
            return section.section_id
    for section in paper.sections:
        if needle in section.heading.lower() or section.heading.lower() in needle:
            return section.section_id
    return None


def _section_id_for_offset(paper: ParsedPaper, offset: int) -> Optional[str]:
    """Pick the section whose heading appears latest before `offset` in raw_text."""
    best: Optional[str] = None
    cursor = 0
    for section in paper.sections:
        heading_pos = paper.raw_text.find(section.heading, cursor)
        if heading_pos == -1 or heading_pos > offset:
            break
        best = section.section_id
        cursor = heading_pos + len(section.heading)
    return best


def _approximate_raw_position(raw: str, normalized_pos: int, span_len: int) -> int:
    """Map an offset in the whitespace-collapsed text back to raw_text."""
    consumed = 0
    raw_pos = 0
    while raw_pos < len(raw) and consumed < normalized_pos:
        if raw[raw_pos] in " \t\r\n\f\v":
            # collapse runs of whitespace into one consumed char
            raw_pos += 1
            while raw_pos < len(raw) and raw[raw_pos] in " \t\r\n\f\v":
                raw_pos += 1
            consumed += 1
        else:
            raw_pos += 1
            consumed += 1
    return min(len(raw) - span_len if span_len > 0 else len(raw), raw_pos)
