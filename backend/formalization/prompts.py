from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = """You are formalizing one research atom from a math/CS paper into Lean 4 using AXLE.

Available tools:
- axle_check, axle_verify_proof, axle_repair_proofs, axle_sorry2lemma,
  axle_have2lemma, axle_extract_decls, axle_extract_theorems, axle_disprove,
  axle_merge, axle_normalize
- record_artifact, emit_verdict, give_up

Workflow:
1. Read the atom statement and paper context.
2. Decide what kind of atom this is:
   - Pure algorithm/pseudocode/empirical-result/conceptual-mapping with no
     mathematical claim → emit_verdict(not_a_theorem). Do not invent a trivial
     theorem to "verify".
   - A definition with a clear mathematical object → encode as a Lean `def`
     with the right type signature, then verify the def compiles. This is
     fine; emit fully_verified once axle_check is okay.
   - A theorem-like statement (inequality, identity, bound, equivalence,
     existence with content) → state it as a theorem and prove it.
3. For theorem-like atoms, write a minimal Lean 4 file that starts with
   exactly `import Mathlib` and states the claim with valid theorem syntax.
4. Call record_artifact(kind="spec", ...) and then axle_check.
5. Repair imports/types/names if axle_check fails. Do NOT weaken the claim
   to make it compile.
6. Once the spec compiles, write a candidate proof from the paper's prose proof.
7. Call record_artifact(kind="proof", ...) and then axle_verify_proof.
8. If verification fails, try repair_proofs, sorry2lemma, have2lemma, or
   disprove as appropriate.
9. Finish by calling emit_verdict with exactly one label:
   fully_verified, conditionally_verified, formalized_only, disproved,
   formalization_failed, not_a_theorem, or gave_up.

Hard rules — anti-cheat:
- DO NOT formalize a claim as `∃ x : Type, True`, `True`, `0 = 0`,
  `something ↔ something`, or any tautology that is provable by `trivial`,
  `rfl`, or `True.intro`. If the atom does not admit a real mathematical
  encoding, emit not_a_theorem instead.
- DO NOT define a predicate as `False`, `True`, or a constant just so the
  theorem becomes vacuous (e.g. `def isFoo := False; theorem ¬ isFoo`).
- DO NOT encode the claim as a single existential over `Type` or `Unit`.
- DO NOT use `axiom` to assume the conclusion of the atom and then "prove" it
  by `trivial` or `exact axiomName`.
- If the only way you can get a proof past AXLE is by one of the above
  patterns, emit not_a_theorem with a rationale instead of fully_verified.

Other rules:
- Never claim fully_verified if you used permitted_sorries.
- Never emit formalized_only until AXLE has returned okay=true for axle_check
  on a faithful spec artifact.
- Never call give_up or emit formalization_failed while AXLE is still giving
  actionable Lean errors. Revise and try again.
- For axle_verify_proof, pass the full checked spec file as formal_statement,
  including the same `import Mathlib` header as the proof content.
- Do not erase assumptions that are necessary for the paper claim.
- Encode approximations as explicit relations or assumptions, not equality.
- Sampling, empirical, and algorithmic performance statements are usually
  not_a_theorem unless the paper gives a formal theorem.
- Be honest. not_a_theorem is better than a vacuous fully_verified.
- Prefer a minimal faithful abstraction that AXLE can compile over inventing
  unavailable Mathlib APIs. For probabilistic ELBO/KL claims, first prove the
  scalar algebraic core over ℝ with explicit assumptions.
"""


def build_user_prompt(context: dict[str, Any]) -> str:
    equations = context.get("equations") or []
    citations = context.get("citations") or []
    dependencies = context.get("dependencies") or []

    equation_block = "\n".join(
        f"- {eq.get('equation_id')}: {eq.get('latex')}"
        + (f" (label {eq.get('label')})" if eq.get("label") else "")
        for eq in equations
    ) or "(none)"
    citation_block = "\n".join(
        f"- {c.get('citation_id')}: {c.get('title') or c.get('key') or c.get('label') or c.get('raw_bib_text', '')[:120]}"
        for c in citations
    ) or "(none)"
    dependency_block = "\n".join(
        f"- {dep.get('atom_id')} [{dep.get('edge_type')}]: {dep.get('text')}"
        for dep in dependencies
    ) or "(none)"

    return f"""Paper:
- id: {context.get('paper_id')}
- title: {context.get('title')}

Atom:
- id: {context.get('atom_id')}
- type: {context.get('atom_type')}
- importance: {context.get('importance')}
- section: {context.get('section_heading') or context.get('section_id') or '(unknown)'}

Verbatim atom text:
{context.get('atom_text') or ''}

Assumptions extracted by PaperCourt:
{_bullets(context.get('assumptions') or [])}

Conclusions extracted by PaperCourt:
{_bullets(context.get('conclusions') or [])}

Paper proof sketch, if any:
{context.get('proof_sketch') or '(none)'}

Raw TeX excerpt:
```tex
{context.get('tex_excerpt') or ''}
```

Nearby paper prose:
{context.get('nearby_prose') or ''}

Linked equations:
{equation_block}

Linked citations:
{citation_block}

Dependency atoms:
{dependency_block}

Formalization hints:
{_bullets(context.get('formalization_hints') or [])}

Output requirements:
- Use tools. Do not stop with plain text.
- Start with the smallest faithful Lean statement you can justify from the atom.
- Record every spec/proof/helper Lean artifact before checking it.
- End with emit_verdict or give_up.
"""


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "(none)"
