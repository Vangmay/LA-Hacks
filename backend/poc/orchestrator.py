import asyncio
import io
import logging
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from agents.base import AgentContext
from agents.claim_extractor import ClaimExtractorAgent
from agents.dag_builder import DAGBuilderAgent
from agents.parser import ParserAgent
from poc.agents.claim_filter import ClaimFilterAgent
from poc.agents.metric_extractor import MetricExtractorAgent
from poc.agents.scaffold_generator import ScaffoldGeneratorAgent
from config import settings
from core.dag import DAG
from core.event_bus import event_bus
from core.job_store import job_store
from models import ClaimUnit, DAGEvent, DAGEventType

logger = logging.getLogger(__name__)

_SCAFFOLD_FILES = (
    "implementation.py",
    "test_harness.py",
    "results_logger.py",
    "requirements.txt",
    "README.md",
)

# backend/outputs/poc/  (file is at backend/poc/orchestrator.py → parents[1] = backend/)
_OUTPUTS_DIR = Path(__file__).resolve().parents[1] / "outputs" / "poc"

# ...existing code...
