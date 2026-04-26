from __future__ import annotations

import re
from pathlib import Path

from formalization.models import FormalizationArtifact, FormalizationRun


_OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "outputs" / "formalizations"
_SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def _safe_segment(value: str) -> str:
    cleaned = _SAFE_SEGMENT_RE.sub("_", value).strip("._")
    return cleaned or "unknown"


def write_artifact(run_id: str, atom_id: str, artifact: FormalizationArtifact) -> str:
    directory = _OUTPUT_ROOT / _safe_segment(run_id) / _safe_segment(atom_id)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{_safe_segment(artifact.kind)}_{artifact.iteration:02d}_{_safe_segment(artifact.artifact_id)}.lean"
    path = directory / filename
    path.write_text(artifact.lean_code, encoding="utf-8")
    return str(path)


def merged_lean(run: FormalizationRun) -> str:
    chunks: list[str] = []
    for atom_id in run.selected_atom_ids:
        atom = run.atom_formalizations.get(atom_id)
        if not atom:
            continue
        for artifact in atom.artifacts:
            chunks.append(
                "\n".join(
                    [
                        f"-- run: {run.run_id}",
                        f"-- atom: {atom_id}",
                        f"-- artifact: {artifact.kind} iteration {artifact.iteration}",
                        artifact.lean_code.rstrip(),
                        "",
                    ]
                )
            )
    return "\n\n".join(chunks).strip() + ("\n" if chunks else "")
