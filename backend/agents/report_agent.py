"""Real `ReviewReport` writer.

Builds typed counts and a markdown report that includes, for each
reviewed atom: section, atom type, source excerpt, attached equations
and citations, the check results, the unresolved challenges and any
rebuttals, and the final verdict with reason codes.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import (
    AtomVerdict,
    ParsedPaper,
    ResearchAtom,
    ResearchGraph,
    ReviewReport,
    ReviewSummary,
    VerdictLabel,
    is_reviewable,
)

logger = logging.getLogger(__name__)


def build_review_report(
    *,
    job_id: str,
    paper: ParsedPaper,
    atoms: list[ResearchAtom],
    graph: ResearchGraph,
    verdicts: list[AtomVerdict],
    arxiv_id: Optional[str] = None,
    tex_path: Optional[str] = None,
) -> ReviewReport:
    summary = _summary(atoms, verdicts)
    paper_hash = _paper_hash(tex_path)

    markdown = _markdown(paper, atoms, graph, verdicts, summary)

    return ReviewReport(
        report_id=f"report_{uuid.uuid4().hex[:10]}",
        job_id=job_id,
        paper_id=paper.paper_id,
        paper_title=paper.title or paper.paper_id,
        arxiv_id=arxiv_id,
        paper_hash=paper_hash,
        reviewed_at=datetime.utcnow(),
        summary=summary,
        atoms=atoms,
        graph=graph,
        verdicts=verdicts,
        markdown_report=markdown,
        warnings=list(graph.warnings),
    )


def _summary(atoms: list[ResearchAtom], verdicts: list[AtomVerdict]) -> ReviewSummary:
    by_label: dict[VerdictLabel, int] = {label: 0 for label in VerdictLabel}
    for v in verdicts:
        by_label[v.label] = by_label.get(v.label, 0) + 1

    reviewed = [a for a in atoms if is_reviewable(a)]
    high_risk = [
        v.atom_id
        for v in verdicts
        if v.label in (VerdictLabel.LIKELY_FLAWED, VerdictLabel.REFUTED, VerdictLabel.CONTESTED)
    ]
    cascaded = [v.atom_id for v in verdicts if v.is_cascaded]

    return ReviewSummary(
        total_atoms=len(atoms),
        total_reviewed_atoms=len(reviewed),
        no_objection_found=by_label[VerdictLabel.NO_OBJECTION_FOUND],
        contested=by_label[VerdictLabel.CONTESTED],
        likely_flawed=by_label[VerdictLabel.LIKELY_FLAWED],
        refuted=by_label[VerdictLabel.REFUTED],
        not_checkable=by_label[VerdictLabel.NOT_CHECKABLE],
        high_risk_atom_ids=high_risk,
        cascaded_atom_ids=cascaded,
    )


def _paper_hash(tex_path: Optional[str]) -> str:
    if not tex_path:
        return "0" * 16
    try:
        return hashlib.md5(Path(tex_path).read_bytes()).hexdigest()[:16]
    except OSError:
        return "0" * 16


def _markdown(
    paper: ParsedPaper,
    atoms: list[ResearchAtom],
    graph: ResearchGraph,
    verdicts: list[AtomVerdict],
    summary: ReviewSummary,
) -> str:
    by_atom: dict[str, AtomVerdict] = {v.atom_id: v for v in verdicts}
    atoms_by_id: dict[str, ResearchAtom] = {a.atom_id: a for a in atoms}

    lines: list[str] = []
    lines.append(f"# Review Report — {paper.title or paper.paper_id}")
    lines.append("")
    lines.append(
        f"- Atoms: {summary.total_atoms}  |  Reviewed: {summary.total_reviewed_atoms}"
    )
    lines.append(
        f"- No objection: {summary.no_objection_found}  |  Contested: {summary.contested}  "
        f"|  Likely flawed: {summary.likely_flawed}  |  Refuted: {summary.refuted}  "
        f"|  Not checkable: {summary.not_checkable}"
    )
    if summary.cascaded_atom_ids:
        lines.append(f"- Cascaded: {', '.join(summary.cascaded_atom_ids)}")
    if graph.warnings:
        lines.append("")
        lines.append("**Graph warnings:** " + "; ".join(graph.warnings))
    lines.append("")
    lines.append("## Atoms")

    for atom in atoms:
        verdict = by_atom.get(atom.atom_id)
        label = verdict.label.value if verdict else "(no verdict)"
        lines.append("")
        lines.append(
            f"### {atom.atom_id} · {atom.atom_type.value} · {atom.section_heading or '?'} — **{label}**"
        )
        if verdict:
            lines.append(f"_Confidence_: {verdict.confidence:.2f}")
            if verdict.reason_codes:
                lines.append(
                    "_Reasons_: " + ", ".join(c.value for c in verdict.reason_codes)
                )
            if verdict.is_cascaded and verdict.cascade_source_atom_id:
                lines.append(
                    f"_Cascaded from_: {verdict.cascade_source_atom_id}"
                )

        excerpt = atom.source_span.raw_excerpt.strip()
        if excerpt:
            lines.append("")
            lines.append("**Source excerpt:**")
            lines.append("> " + excerpt[:800].replace("\n", "\n> "))

        if atom.equations:
            lines.append("")
            lines.append("**Equations:**")
            for eq in atom.equations[:6]:
                lines.append(f"- `{eq.equation_id}` ({eq.environment or '?'}): {eq.latex}")

        if atom.citations:
            lines.append("")
            lines.append("**Citations:**")
            for c in atom.citations[:6]:
                key = c.key or c.label or "?"
                meta = c.raw_bib_text[:200]
                lines.append(f"- `{c.citation_id}` key={key}{(' — ' + meta) if meta else ''}")

        deps = sorted(
            edge.target_id
            for edge in graph.edges
            if edge.source_id == atom.atom_id
        )
        if deps:
            lines.append("")
            lines.append(f"**Depends on:** {', '.join(deps)}")

        if verdict:
            if verdict.checks:
                lines.append("")
                lines.append("**Checks:**")
                for check in verdict.checks:
                    lines.append(
                        f"- {check.kind.value}: {check.status.value} — {check.summary}"
                    )
            if verdict.challenges:
                lines.append("")
                lines.append("**Challenges:**")
                for ch in verdict.challenges:
                    lines.append(
                        f"- ({ch.challenge_type.value}, {ch.severity.value}) {ch.challenge_text}"
                    )
                    if ch.falsifiable_test:
                        lines.append(f"  - falsifiable test: {ch.falsifiable_test}")
            if verdict.rebuttals:
                lines.append("")
                lines.append("**Rebuttals:**")
                for rb in verdict.rebuttals:
                    lines.append(
                        f"- ({rb.response_type.value}, conf {rb.confidence:.2f}) {rb.rebuttal_text}"
                    )
            if verdict.rationale:
                lines.append("")
                lines.append(f"_Rationale_: {verdict.rationale}")

    return "\n".join(lines).rstrip() + "\n"
