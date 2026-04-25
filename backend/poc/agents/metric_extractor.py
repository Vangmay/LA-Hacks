import json
import logging
import uuid

from openai import AsyncOpenAI

from config import settings
from models import ClaimUnit, PoCSpec, MetricCriterion, ClaimTestability
from agents.base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Extract all quantitative success and failure criteria from this claim. For each metric:
- metric_name: what is being measured (e.g. 'top-1 accuracy', 'training time', 'memory usage')
- paper_reported_value: exact string from paper (e.g. '94.3% on ImageNet')
- numeric_threshold: the numeric value as a float (null if not extractable)
- tolerance: how much deviation counts as reproduction (default 0.02 = 2% relative)
- comparison: 'gte' if the metric should be >= threshold, 'lte' if <=, 'within_tolerance' if ±tolerance
- experimental_conditions: dict of required conditions stated in paper (dataset, model size, batch size, etc.)
- For each metric, also extract the exact model(s) used (name, version, architecture) and include this as a 'model' field in experimental_conditions. If the model is not specified, set 'model': null or 'model': 'unspecified'.

Return JSON: {"success_criteria": [...], "failure_criteria": [...]}
Failure criteria = negation of success criteria plus any explicit failure conditions stated.
If numeric_threshold cannot be extracted, set it to null."""

# ...existing code...
