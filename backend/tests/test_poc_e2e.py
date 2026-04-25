"""
PoC Mode test suite — covers Prompts 7.1 through 7.4.

Sections
--------
1. ClaimFilterAgent        — classify testable vs theoretical
2. MetricExtractorAgent    — extract quantitative success criteria
3. ScaffoldGeneratorAgent  — generate runnable Python scaffolds
4. ResultsAnalyzerAgent    — evaluate experiment results against thresholds
5. ReproducibilityReportAgent — produce markdown + gap analysis
6. PoCOrchestrator         — full agent pipeline wired together
7. PoC API endpoints       — every HTTP route
8. End-to-end flow         — submit → orchestrate → upload results → report

No real OpenAI calls are made; all LLM clients are patched.
Run from backend/ with:  pytest tests/test_poc_e2e.py -v
"""

import ast
import io
import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from agents.base import AgentContext, AgentResult
from agents.claim_extractor import ClaimExtractorAgent
from poc.agents.claim_filter import ClaimFilterAgent
from agents.dag_builder import DAGBuilderAgent
from poc.agents.metric_extractor import MetricExtractorAgent
from agents.parser import ParserAgent
from poc.agents.reproducibility_report import ReproducibilityReportAgent
from poc.agents.results_analyzer import ResultsAnalyzerAgent
from poc.agents.scaffold_generator import ScaffoldGeneratorAgent
from core.dag import DAG
from core.event_bus import event_bus
from core.job_store import job_store
from poc.orchestrator import PoCOrchestrator
from main import app
from models import (
    ClaimTestability,
    ClaimUnit,
    DAGEventType,
    ExperimentResult,
    MetricCriterion,
    PoCSpec,
    ReproducibilityReport,
    ReproductionStatus,
)

client = TestClient(app, raise_server_exceptions=True)

# ...existing code...
