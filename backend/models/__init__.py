"""Public model surface for the v0.4 source-grounded pipeline."""
from .source import (
    SourceKind,
    PaperSource,
    SourceSpan,
    PaperSection,
    EquationBlock,
    CitationEntry,
    ParsedPaper,
)
from .atoms import (
    ResearchAtomType,
    AtomImportance,
    AtomReviewability,
    AtomCheckability,
    ResearchAtom,
    AtomExtractionResult,
    REVIEWABLE_ATOM_TYPES,
    is_reviewable,
)
from .atom_candidate import AtomCandidate
from .graph import (
    ResearchGraphEdgeType,
    DEPENDENCY_EDGE_TYPES,
    ResearchGraphEdge,
    ResearchGraph,
)
from .evidence import EvidenceSourceType, Evidence, ToolCallTrace
from .checks import CheckKind, CheckStatus, CheckResult
from .adversarial import (
    ChallengeType,
    Severity,
    Challenge,
    RebuttalType,
    Rebuttal,
)
from .verdict import VerdictLabel, VerdictReasonCode, AtomVerdict
from .report import ReviewSummary, ReviewReport
from .events import GraphNodeKind, GraphNodeStatus, DAGEventType, DAGEvent
from .jobs import JobMode, JobStatus, ReviewJob

# Stub modes still imported by their (unmodified) routers.
from .reader import (
    AtomAnnotation,
    ComprehensionLevel,
    ComprehensionStatus,
    Exercise,
    Prerequisite,
)
from .poc import (
    PoCSpec,
    MetricCriterion,
    ExperimentResult,
    ReproducibilityReport,
    GapAnalysisEntry,
    ClaimTestability,
    ReproductionStatus,
)
from .research import Hypothesis, KnowledgeNode, ResearchSession

__all__ = [
    # source
    "SourceKind",
    "PaperSource",
    "SourceSpan",
    "PaperSection",
    "EquationBlock",
    "CitationEntry",
    "ParsedPaper",
    # atoms
    "ResearchAtomType",
    "AtomImportance",
    "AtomReviewability",
    "AtomCheckability",
    "AtomCandidate",
    "ResearchAtom",
    "AtomExtractionResult",
    "REVIEWABLE_ATOM_TYPES",
    "is_reviewable",
    # graph
    "ResearchGraphEdgeType",
    "DEPENDENCY_EDGE_TYPES",
    "ResearchGraphEdge",
    "ResearchGraph",
    # evidence
    "EvidenceSourceType",
    "Evidence",
    "ToolCallTrace",
    # checks
    "CheckKind",
    "CheckStatus",
    "CheckResult",
    # adversarial
    "ChallengeType",
    "Severity",
    "Challenge",
    "RebuttalType",
    "Rebuttal",
    # verdict / report
    "VerdictLabel",
    "VerdictReasonCode",
    "AtomVerdict",
    "ReviewSummary",
    "ReviewReport",
    # events / jobs
    "GraphNodeKind",
    "GraphNodeStatus",
    "DAGEventType",
    "DAGEvent",
    "JobMode",
    "JobStatus",
    "ReviewJob",
    # stub modes
    "AtomAnnotation",
    "ComprehensionLevel",
    "ComprehensionStatus",
    "Exercise",
    "Prerequisite",
    "PoCSpec",
    "MetricCriterion",
    "ExperimentResult",
    "ReproducibilityReport",
    "GapAnalysisEntry",
    "ClaimTestability",
    "ReproductionStatus",
    "Hypothesis",
    "KnowledgeNode",
    "ResearchSession",
]
