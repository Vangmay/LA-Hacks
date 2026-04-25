"""Attach `EquationBlock` objects to atoms.

Heuristics, in order:
1. Same section as the atom.
2. Equation TeX span overlaps or is within N chars of atom TeX span.
3. Equation latex appears verbatim inside atom text.
4. Atom references the equation by `\\label{...}` or its number.

Equation objects (not ids) are attached so downstream sympy can read
`equation.latex` directly.
"""
from __future__ import annotations

import re
from typing import Optional

from models import EquationBlock, ParsedPaper, ResearchAtom

_NEAR_WINDOW = 1500  # TeX chars

_REF_RE = re.compile(r"\b(?:eq(?:uation)?|equation)\s*\.?\s*\(?([\w:.\-]+)\)?", re.IGNORECASE)


def link_equations_to_atoms(
    paper: ParsedPaper,
    atoms: list[ResearchAtom],
) -> list[ResearchAtom]:
    """Mutate atoms in place by populating `atom.equations`. Returns the list."""
    for atom in atoms:
        atom.equations = _link_one(paper, atom)
    return atoms


def _link_one(paper: ParsedPaper, atom: ResearchAtom) -> list[EquationBlock]:
    selected: list[EquationBlock] = []
    seen_ids: set[str] = set()

    atom_tex_start = atom.source_span.tex_start
    atom_tex_end = atom.source_span.tex_end

    for eq in paper.equations:
        if eq.equation_id in seen_ids:
            continue

        if _matches_atom(atom, eq, atom_tex_start, atom_tex_end):
            selected.append(eq)
            seen_ids.add(eq.equation_id)

    if selected:
        return selected

    # LLM atoms often resolve to raw-text spans but not TeX offsets. In that
    # case, attach equations only when the atom's section has a small,
    # unambiguous equation set. This improves source grounding without dumping
    # every equation from long technical sections onto each atom.
    if atom_tex_start is None and atom.section_id:
        section_equations = [
            eq for eq in paper.equations if eq.section_id == atom.section_id
        ]
        if 0 < len(section_equations) <= 3:
            return section_equations

    return selected


def _matches_atom(
    atom: ResearchAtom,
    eq: EquationBlock,
    atom_tex_start: Optional[int],
    atom_tex_end: Optional[int],
) -> bool:
    # Direct latex inclusion.
    eq_latex = eq.latex.strip()
    if eq_latex and len(eq_latex) >= 6 and eq_latex in atom.text:
        return True

    # Label or numeric reference.
    if eq.label:
        if eq.label in atom.text:
            return True

    for match in _REF_RE.finditer(atom.text):
        ref = match.group(1)
        if eq.label and (ref == eq.label or ref.endswith(eq.label)):
            return True

    # TeX-span proximity within the same section.
    if (
        atom_tex_start is not None
        and atom_tex_end is not None
        and eq.source_span is not None
        and eq.source_span.tex_start is not None
        and eq.source_span.tex_end is not None
    ):
        if eq.section_id and atom.section_id and eq.section_id != atom.section_id:
            return False
        eq_start = eq.source_span.tex_start
        eq_end = eq.source_span.tex_end
        # overlap or within proximity window
        if eq_end < atom_tex_start - _NEAR_WINDOW:
            return False
        if eq_start > atom_tex_end + _NEAR_WINDOW:
            return False
        if atom_tex_start - _NEAR_WINDOW <= eq_start <= atom_tex_end + _NEAR_WINDOW:
            return True

    return False
