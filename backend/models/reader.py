from pydantic import BaseModel
from typing import List, Literal, Optional
from enum import Enum


class ComprehensionLevel(str, Enum):
    LAYPERSON     = "layperson"
    UNDERGRADUATE = "undergraduate"
    GRADUATE      = "graduate"
    EXPERT        = "expert"


class ComprehensionStatus(str, Enum):
    UNVISITED   = "unvisited"
    IN_PROGRESS = "in_progress"
    UNDERSTOOD  = "understood"
    FLAGGED     = "flagged"


class Prerequisite(BaseModel):
    concept: str
    description: str
    resource_links: List[str]


class Exercise(BaseModel):
    exercise_id: str
    prompt: str
    exercise_type: Literal["conceptual", "computational", "counterexample_mcq", "proof_fill"]
    answer_key: str
    user_answer: Optional[str] = None
    graded: Optional[bool] = None


class ClaimAnnotation(BaseModel):
    claim_id: str
    level: ComprehensionLevel
    explanation: str
    glossary: dict
    prerequisites: List[Prerequisite]
    exercises: List[Exercise]
    comprehension_status: ComprehensionStatus
