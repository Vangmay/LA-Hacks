import logging
from typing import Dict, List

from models import ExperimentResult, ReproductionStatus
from agents.base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)

_STATUS_RANK: Dict[ReproductionStatus, int] = {
    ReproductionStatus.REPRODUCED: 0,
    ReproductionStatus.PARTIAL: 1,
    ReproductionStatus.FAILED: 2,
    ReproductionStatus.PENDING: 3,
}

# ...existing code...
