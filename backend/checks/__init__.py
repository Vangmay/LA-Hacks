"""Source-grounded checks. Each function takes a `ResearchAtom` (and the
parsed paper when needed), runs a deterministic-ish probe, and returns a
typed `CheckResult` carrying its evidence.
"""
from .algebraic_sanity import run_algebraic_sanity
from .numeric_probe import run_numeric_probe
from .citation_probe import run_citation_probe

__all__ = [
    "run_algebraic_sanity",
    "run_numeric_probe",
    "run_citation_probe",
]
