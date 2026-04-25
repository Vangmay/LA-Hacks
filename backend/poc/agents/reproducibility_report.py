import json
import logging
from typing import Dict, List

from openai import AsyncOpenAI

from config import settings
from models import (
    ExperimentResult,
    GapAnalysisEntry,
    ReproducibilityReport,
    ReproductionStatus,
)
from agents.base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)

_STATUS_RANK: Dict[ReproductionStatus, int] = {
    ReproductionStatus.REPRODUCED: 0,
    ReproductionStatus.PARTIAL: 1,
    ReproductionStatus.FAILED: 2,
    ReproductionStatus.PENDING: 3,
}

# ...existing code...
