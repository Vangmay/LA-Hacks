import json
import logging
import asyncio
from typing import List

from openai import AsyncOpenAI

from config import settings
from models import ClaimUnit
from agents.base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)

_BATCH_SIZE = 10

_SYSTEM_PROMPT = (
    "Classify each mathematical/algorithmic claim as 'testable' (can be verified by running "
    "an experiment and measuring a metric) or 'theoretical' (requires mathematical proof only). "
    "For testable claims, briefly state what experiment would verify it. "
    "Return a JSON object with a single key 'results' containing an array: "
    "{\"results\": [{\"claim_id\": str, \"testability\": \"testable\"|\"theoretical\", \"reason\": str}]}"
)

# ...existing code...
