import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from sse_starlette.sse import EventSourceResponse

from agents.base import AgentContext
from poc.agents.reproducibility_report import ReproducibilityReportAgent
from poc.agents.results_analyzer import ResultsAnalyzerAgent
from core.event_bus import event_bus
from core.job_store import job_store
from poc.orchestrator import PoCOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
_orchestrator = PoCOrchestrator()

# ...existing code...
