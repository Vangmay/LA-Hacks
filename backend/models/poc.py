from pydantic import BaseModel
from typing import List, Literal, Optional
from enum import Enum


class ClaimTestability(str, Enum):
    TESTABLE    = "testable"
    THEORETICAL = "theoretical"


class ReproductionStatus(str, Enum):
    REPRODUCED = "REPRODUCED"
    PARTIAL    = "PARTIAL"
    FAILED     = "FAILED"
    PENDING    = "PENDING"


class MetricCriterion(BaseModel):
    metric_name: str
    paper_reported_value: str
    numeric_threshold: Optional[float]
    tolerance: float = 0.02
    comparison: Literal["gte", "lte", "eq", "within_tolerance"]
    experimental_conditions: dict


class PoCSpec(BaseModel):
    spec_id: str
    claim_id: str
    testability: ClaimTestability
    success_criteria: List[MetricCriterion]
    failure_criteria: List[MetricCriterion]
    scaffold_files: dict
    readme: str


class ExperimentResult(BaseModel):
    claim_id: str
    metric_name: str
    achieved_value: float
    status: ReproductionStatus
    delta: Optional[float] = None
    error_message: Optional[str] = None


class GapAnalysisEntry(BaseModel):
    claim_id: str
    explanation: str
    likelihood: Literal["high", "medium", "low"]
    suggested_fix: str


class ReproducibilityReport(BaseModel):
    session_id: str
    paper_title: str
    total_testable_claims: int
    reproduced: int
    partial: int
    failed: int
    reproduction_rate: float
    results: List[ExperimentResult]
    gap_analyses: List[GapAnalysisEntry]
    what_to_try_next: List[str]
    markdown_report: str
