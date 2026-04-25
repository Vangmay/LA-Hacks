"""Attach `CitationEntry` objects to atoms.

Pulls `\\cite{key}` keys and bare `[12]` labels out of the atom span (and a
small surrounding TeX window), then resolves to bibliography entries by
key match. Anything we can't resolve still becomes a placeholder
`CitationEntry` so the atom faithfully records that it cited *something*.
"""
from __future__ import annotations

import re
from typing import Optional

from models import CitationEntry, ParsedPaper, ResearchAtom

_CITE_KEY_RE = re.compile(
    r"\\(?:cite|citep|citet|citealp|nocite)(?:\[[^\]]*\])*\{([^{}]+)\}"
)
_BRACKET_LABEL_RE = re.compile(r"\[(\d+)\]")
_NEAR_WINDOW = 800


def link_citations_to_atoms(
    paper: ParsedPaper,
    atoms: list[ResearchAtom],
) -> list[ResearchAtom]:
    """Mutate atoms in place to populate `atom.citations`. Returns the list."""
    bib_by_key: dict[str, CitationEntry] = {
        entry.key: entry for entry in paper.bibliography if entry.key
    }
    bib_by_label: dict[str, CitationEntry] = {
        entry.label: entry for entry in paper.bibliography if entry.label
    }

    assembled = paper.assembled_tex or ""

    for atom in atoms:
        atom.citations = _collect(
            atom=atom,
            assembled=assembled,
            paper=paper,
            bib_by_key=bib_by_key,
            bib_by_label=bib_by_label,
        )
    return atoms


def _collect(
    atom: ResearchAtom,
    assembled: str,
    paper: ParsedPaper,
    bib_by_key: dict[str, CitationEntry],
    bib_by_label: dict[str, CitationEntry],
) -> list[CitationEntry]:
    keys: list[str] = []
    seen_keys: set[str] = set()

    def add(key: str) -> None:
        clean = key.strip()
        if not clean or clean in seen_keys:
            return
        seen_keys.add(clean)
        keys.append(clean)

    for sub in _CITE_KEY_RE.findall(atom.text or ""):
        for k in sub.split(","):
            add(k)

    tex_window = _tex_window(assembled, atom.source_span.tex_start, atom.source_span.tex_end)
    if tex_window:
        for sub in _CITE_KEY_RE.findall(tex_window):
            for k in sub.split(","):
                add(k)
    elif atom.section_id:
        section_window = _section_tex_window(assembled, paper, atom.section_id)
        for sub in _CITE_KEY_RE.findall(section_window):
            for k in sub.split(","):
                add(k)

    labels: list[str] = []
    seen_labels: set[str] = set()
    for label in _BRACKET_LABEL_RE.findall(atom.text or ""):
        if label not in seen_labels:
            labels.append(label)
            seen_labels.add(label)

    citations: list[CitationEntry] = []
    for idx, key in enumerate(keys[:8], start=1):
        if key in bib_by_key:
            citations.append(bib_by_key[key])
        else:
            citations.append(
                CitationEntry(
                    citation_id=f"{atom.atom_id}_cite_{idx:03d}",
                    key=key,
                    raw_bib_text="",
                )
            )

    for idx, label in enumerate(labels, start=1):
        if label in bib_by_label:
            citations.append(bib_by_label[label])
            continue
        # Don't double-count if already added by key.
        if any(c.label == label for c in citations):
            continue
        citations.append(
            CitationEntry(
                citation_id=f"{atom.atom_id}_label_{idx:03d}",
                label=label,
                raw_bib_text="",
            )
        )

    return citations


def _tex_window(assembled: str, start: Optional[int], end: Optional[int]) -> str:
    if not assembled or start is None or end is None:
        return ""
    lo = max(0, start - _NEAR_WINDOW)
    hi = min(len(assembled), end + _NEAR_WINDOW)
    return assembled[lo:hi]


def _section_tex_window(assembled: str, paper: ParsedPaper, section_id: str) -> str:
    if not assembled:
        return ""
    for section in paper.sections:
        if section.section_id != section_id:
            continue
        start = section.source_span.tex_start
        end = section.source_span.tex_end
        if start is None or end is None:
            return ""
        return assembled[start:end]
    return ""
