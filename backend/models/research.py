from pydantic import BaseModel
from typing import List, Literal, Optional

from .verification import VerificationResult
from .report import ReviewReport


class Hypothesis(BaseModel):
    hypothesis_id: str
    text: str
    source_gap: str
    proof_approach: Optional[Literal["induction", "construction", "contradiction", "numeric"]] = None
    verification_result: Optional[VerificationResult] = None
    status: Literal["proposed", "approved", "rejected", "proven", "disproven", "inconclusive"]
    user_approved: bool


class KnowledgeNode(BaseModel):
    node_id: str
    claim_text: str
    source_paper: str
    related_nodes: List[str]
    contradicting_nodes: List[str]


class ResearchSession(BaseModel):
    session_id: str
    query: str
    retrieved_papers: List[str]
    knowledge_graph: List[KnowledgeNode]
    detected_gaps: List[str]
    hypotheses: List[Hypothesis]
    iteration_count: int
    working_memory: dict
    research_note: Optional[str] = None
    self_review_verdict: Optional[ReviewReport] = None
