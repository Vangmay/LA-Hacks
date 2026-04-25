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

# ══════════════════════════════════════════════════════════════════════════════
# Shared test data
# ══════════════════════════════════════════════════════════════════════════════

_CLAIM = ClaimUnit(
    claim_id="c1",
    text="The Transformer achieves 28.4 BLEU on WMT 2014 EN-DE.",
    claim_type="assertion",
    section="results",
    equations=[],
    citations=[],
    dependencies=[],
)

_CLAIM2 = ClaimUnit(
    **{**_CLAIM.model_dump(), "claim_id": "c2", "text": "Training cost is O(n^2)."}
)

_PAPER_META = {
    "title": "Attention Is All You Need",
    "abstract": "We propose the Transformer...",
    "sections": [{"title": "Results", "content": "28.4 BLEU on WMT 2014."}],
    "equations": [],
    "bibliography": [],
    "raw_text": "The Transformer achieves 28.4 BLEU.",
    "is_scanned": False,
}

_POC_SPEC_DICT = {
    "spec_id": "spec-c1",
    "claim_id": "c1",
    "testability": "testable",
    "success_criteria": [
        {
            "metric_name": "bleu",
            "paper_reported_value": "28.4 BLEU",
            "numeric_threshold": 28.4,
            "tolerance": 0.02,
            "comparison": "gte",
            "experimental_conditions": {},
        }
    ],
    "failure_criteria": [],
    "scaffold_files": {
        "implementation.py": "def main(): pass\n",
        "test_harness.py": "def test_bleu(): assert True\n",
        "results_logger.py": "def save_results(r): pass\n",
        "requirements.txt": "numpy\n",
        "README.md": "# Scaffold\n",
    },
    "readme": "# Scaffold\n",
}

_REPORT_DICT = {
    "session_id": "sess-1",
    "paper_title": "Attention Is All You Need",
    "total_testable_claims": 1,
    "reproduced": 1,
    "partial": 0,
    "failed": 0,
    "reproduction_rate": 1.0,
    "results": [
        {
            "claim_id": "c1",
            "metric_name": "bleu",
            "achieved_value": 29.0,
            "status": "REPRODUCED",
            "delta": 0.6,
            "error_message": None,
        }
    ],
    "gap_analyses": [],
    "what_to_try_next": [],
    "markdown_report": "# Report\n\nReproduction rate: 100%\n",
}

# ── Orchestrator mock outputs ─────────────────────────────────────────────────

_PARSER_OUT = _PAPER_META
_EXTRACTOR_OUT = {"claims": [_CLAIM.model_dump(), _CLAIM2.model_dump()]}
_DAG_OUT = {
    "edges": [],
    "adjacency": {},
    "roots": ["c1", "c2"],
    "topological_order": ["c1", "c2"],
}
_FILTER_OUT = {
    "testable": ["c1"],
    "theoretical": ["c2"],
    "classifications": {
        "c1": {"testability": "testable", "reason": "has BLEU score"},
        "c2": {"testability": "theoretical", "reason": "complexity claim"},
    },
}
_METRIC_OUT = {
    "spec_id": "spec-c1",
    "claim_id": "c1",
    "testability": "testable",
    "success_criteria": [
        {
            "metric_name": "bleu",
            "paper_reported_value": "28.4 BLEU",
            "numeric_threshold": 28.4,
            "tolerance": 0.02,
            "comparison": "gte",
            "experimental_conditions": {},
        }
    ],
    "failure_criteria": [],
    "scaffold_files": {},
    "readme": "",
}
_SCAFFOLD_OUT = {
    "scaffold_files": {
        "implementation.py": "def main(): pass\n",
        "test_harness.py": "def test_bleu(): assert True\n",
        "results_logger.py": "def save_results(r): pass\n",
        "requirements.txt": "numpy\n",
        "README.md": "# Scaffold\n",
    },
    "poc_spec": {**_METRIC_OUT, "scaffold_files": {
        "implementation.py": "def main(): pass\n",
        "test_harness.py": "def test_bleu(): assert True\n",
        "results_logger.py": "def save_results(r): pass\n",
        "requirements.txt": "numpy\n",
        "README.md": "# Scaffold\n",
    }, "readme": "# Scaffold\n"},
}


def _ok(output: dict, status: str = "success") -> AgentResult:
    return AgentResult(agent_id="mock", status=status, output=output, confidence=0.9)


def _new_job(pdf_path: str = "/fake/paper.pdf") -> str:
    jid = job_store.create_job(mode="poc", pdf_path=pdf_path)
    if not event_bus.channel_exists(jid):
        event_bus.create_channel(jid)
    return jid


def _complete_session() -> str:
    """Pre-populated session with claims, specs, and a complete report."""
    sid = job_store.create_job(
        mode="poc",
        pdf_path="/fake/paper.pdf",
        paper_metadata={"title": "Attention Is All You Need"},
        claims={"c1": _CLAIM.model_dump(), "c2": _CLAIM2.model_dump()},
        poc_specs={"c1": _POC_SPEC_DICT},
        zip_path="",
        analysis_status="complete",
        report=_REPORT_DICT,
    )
    if not event_bus.channel_exists(sid):
        event_bus.create_channel(sid)
    return sid


# ══════════════════════════════════════════════════════════════════════════════
# 1. ClaimFilterAgent
# ══════════════════════════════════════════════════════════════════════════════

def _filter_llm_resp(items: list) -> MagicMock:
    choice = MagicMock()
    choice.message.content = json.dumps({"results": items})
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.mark.asyncio
async def test_filter_classifies_testable_and_theoretical():
    llm_items = [
        {"claim_id": "c1", "testability": "testable", "reason": "measurable BLEU"},
        {"claim_id": "c2", "testability": "theoretical", "reason": "complexity proof"},
    ]
    agent = ClaimFilterAgent()
    ctx = AgentContext(job_id="t", extra={"claims": [_CLAIM, _CLAIM2]})
    with patch.object(
        agent._client.chat.completions, "create",
        new=AsyncMock(return_value=_filter_llm_resp(llm_items))
    ):
        result = await agent.run(ctx)
    assert result.status == "success"
    assert "c1" in result.output["testable"]
    assert "c2" in result.output["theoretical"]
    assert result.output["classifications"]["c1"]["testability"] == "testable"


@pytest.mark.asyncio
async def test_filter_no_claims_returns_error():
    result = await ClaimFilterAgent().run(AgentContext(job_id="t", extra={"claims": []}))
    assert result.status == "error"
    assert result.output["testable"] == []
    assert "claims" in result.error.lower()


@pytest.mark.asyncio
async def test_filter_llm_exception_returns_error():
    agent = ClaimFilterAgent()
    ctx = AgentContext(job_id="t", extra={"claims": [_CLAIM]})
    with patch.object(
        agent._client.chat.completions, "create",
        new=AsyncMock(side_effect=RuntimeError("API down"))
    ):
        result = await agent.run(ctx)
    assert result.status == "error"
    assert "API down" in result.error


@pytest.mark.asyncio
async def test_filter_invalid_testability_normalized_to_theoretical():
    llm_items = [{"claim_id": "c1", "testability": "unknown_value", "reason": "?"}]
    agent = ClaimFilterAgent()
    ctx = AgentContext(job_id="t", extra={"claims": [_CLAIM]})
    with patch.object(
        agent._client.chat.completions, "create",
        new=AsyncMock(return_value=_filter_llm_resp(llm_items))
    ):
        result = await agent.run(ctx)
    assert result.output["classifications"]["c1"]["testability"] == "theoretical"
    assert "c1" in result.output["theoretical"]


@pytest.mark.asyncio
async def test_filter_batches_large_claim_sets():
    """More than _BATCH_SIZE (10) claims triggers multiple LLM calls."""
    claims = [
        ClaimUnit(
            claim_id=f"c{i}", text=f"Claim {i}.", claim_type="assertion",
            section="results", equations=[], citations=[], dependencies=[],
        )
        for i in range(15)
    ]
    responses = [
        _filter_llm_resp([
            {"claim_id": f"c{i}", "testability": "testable", "reason": "x"}
            for i in range(0, 10)
        ]),
        _filter_llm_resp([
            {"claim_id": f"c{i}", "testability": "theoretical", "reason": "y"}
            for i in range(10, 15)
        ]),
    ]
    agent = ClaimFilterAgent()
    ctx = AgentContext(job_id="t", extra={"claims": claims})
    with patch.object(
        agent._client.chat.completions, "create",
        new=AsyncMock(side_effect=responses)
    ):
        result = await agent.run(ctx)
    assert result.status == "success"
    assert len(result.output["testable"]) + len(result.output["theoretical"]) == 15


# ══════════════════════════════════════════════════════════════════════════════
# 2. MetricExtractorAgent
# ══════════════════════════════════════════════════════════════════════════════

def _metric_llm_resp(success_criteria: list, failure_criteria: list | None = None) -> MagicMock:
    choice = MagicMock()
    choice.message.content = json.dumps({
        "success_criteria": success_criteria,
        "failure_criteria": failure_criteria or [],
    })
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.mark.asyncio
async def test_metric_extracts_success_criteria():
    criteria = [{"metric_name": "bleu", "paper_reported_value": "28.4", "numeric_threshold": 28.4, "tolerance": 0.02, "comparison": "gte", "experimental_conditions": {}}]
    agent = MetricExtractorAgent()
    ctx = AgentContext(job_id="t", claim=_CLAIM)
    with patch.object(
        agent._client.chat.completions, "create",
        new=AsyncMock(return_value=_metric_llm_resp(criteria))
    ):
        result = await agent.run(ctx)
    assert result.status == "success"
    assert result.claim_id == "c1"
    assert len(result.output["success_criteria"]) == 1
    assert result.output["success_criteria"][0]["metric_name"] == "bleu"


@pytest.mark.asyncio
async def test_metric_no_claim_returns_error():
    result = await MetricExtractorAgent().run(AgentContext(job_id="t"))
    assert result.status == "error"
    assert "claim" in result.error.lower()


@pytest.mark.asyncio
async def test_metric_llm_exception_returns_error():
    agent = MetricExtractorAgent()
    ctx = AgentContext(job_id="t", claim=_CLAIM)
    with patch.object(
        agent._client.chat.completions, "create",
        new=AsyncMock(side_effect=RuntimeError("timeout"))
    ):
        result = await agent.run(ctx)
    assert result.status == "error"
    assert "timeout" in result.error
    assert result.claim_id == "c1"


@pytest.mark.asyncio
async def test_metric_null_threshold_tolerated():
    """numeric_threshold=null in LLM output should still build a valid PoCSpec."""
    criteria = [{"metric_name": "bleu", "paper_reported_value": "28.4", "numeric_threshold": None, "tolerance": 0.02, "comparison": "gte", "experimental_conditions": {}}]
    agent = MetricExtractorAgent()
    ctx = AgentContext(job_id="t", claim=_CLAIM)
    with patch.object(
        agent._client.chat.completions, "create",
        new=AsyncMock(return_value=_metric_llm_resp(criteria))
    ):
        result = await agent.run(ctx)
    assert result.status == "success"
    assert result.output["success_criteria"][0]["numeric_threshold"] is None


@pytest.mark.asyncio
async def test_metric_unknown_comparison_normalized():
    """Non-standard comparison string must be normalized to 'within_tolerance'."""
    criteria = [{"metric_name": "acc", "paper_reported_value": "95%", "numeric_threshold": 95.0, "tolerance": 0.01, "comparison": "approximately", "experimental_conditions": {}}]
    agent = MetricExtractorAgent()
    ctx = AgentContext(job_id="t", claim=_CLAIM)
    with patch.object(
        agent._client.chat.completions, "create",
        new=AsyncMock(return_value=_metric_llm_resp(criteria))
    ):
        result = await agent.run(ctx)
    assert result.status == "success"
    assert result.output["success_criteria"][0]["comparison"] == "within_tolerance"


# ══════════════════════════════════════════════════════════════════════════════
# 3. ScaffoldGeneratorAgent
# ══════════════════════════════════════════════════════════════════════════════

_SCAFFOLD_CLAIM = ClaimUnit(
    claim_id="claim_001",
    text="The Transformer model achieves 28.4 BLEU on WMT 2014 EN-DE.",
    claim_type="assertion",
    section="results",
    equations=[],
    citations=[],
    dependencies=[],
)

_SCAFFOLD_SPEC = PoCSpec(
    spec_id="spec_001",
    claim_id="claim_001",
    testability=ClaimTestability.TESTABLE,
    success_criteria=[MetricCriterion(
        metric_name="bleu_score",
        paper_reported_value="28.4 BLEU",
        numeric_threshold=28.4,
        tolerance=0.5,
        comparison="gte",
        experimental_conditions={"dataset": "WMT 2014 EN-DE"},
    )],
    failure_criteria=[],
    scaffold_files={},
    readme="",
).model_dump()

_VALID_IMPL = (
    "# Implements claim claim_001: The Transformer model achieves 28.4 BLEU\n"
    "import numpy as np\n\n"
    "def compute_bleu(hypothesis, reference):\n"
    "    return 28.4\n\n"
    "def main():\n"
    "    print(compute_bleu([], []))\n\n"
    "if __name__ == '__main__':\n"
    "    main()\n"
)

_VALID_TEST = (
    "import pytest\n"
    "from implementation import compute_bleu\n"
    "from results_logger import save_results\n\n"
    "results = {}\n\n"
    "def test_bleu_score():\n"
    "    score = compute_bleu([], [])\n"
    "    # Paper reports: 28.4 BLEU\n"
    "    assert score >= 28.4 - 0.5\n"
    "    results['bleu_score'] = score\n"
    "    save_results(results)\n"
)


def _scaffold_llm_side_effect(*_args, **kwargs):
    messages = kwargs.get("messages", [])
    system = messages[0]["content"] if messages else ""
    choice = MagicMock()
    if "implementing a research paper" in system:
        choice.message.content = _VALID_IMPL
    elif "pytest test file" in system:
        choice.message.content = _VALID_TEST
    elif "requirements.txt" in system or "Scan the provided" in system:
        choice.message.content = "numpy\npytest\n"
    elif "README" in system or "readme" in system.lower():
        choice.message.content = "# PoC Scaffold\n\nTests claim_001.\n\n## Run\npytest test_harness.py -v\n"
    elif "syntax fixer" in system:
        choice.message.content = _VALID_IMPL
    else:
        choice.message.content = "# fallback\n"
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.mark.asyncio
async def test_scaffold_generates_all_five_files():
    agent = ScaffoldGeneratorAgent()
    ctx = AgentContext(
        job_id="t", claim=_SCAFFOLD_CLAIM,
        extra={"poc_spec": _SCAFFOLD_SPEC, "paper_metadata": _PAPER_META},
    )
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=_scaffold_llm_side_effect)):
        result = await agent.run(ctx)
    assert result.status == "success"
    for f in ("implementation.py", "test_harness.py", "results_logger.py", "requirements.txt", "README.md"):
        assert f in result.output["scaffold_files"], f"missing {f}"


@pytest.mark.asyncio
async def test_scaffold_poc_spec_updated():
    agent = ScaffoldGeneratorAgent()
    ctx = AgentContext(
        job_id="t", claim=_SCAFFOLD_CLAIM,
        extra={"poc_spec": _SCAFFOLD_SPEC, "paper_metadata": _PAPER_META},
    )
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=_scaffold_llm_side_effect)):
        result = await agent.run(ctx)
    spec = result.output["poc_spec"]
    assert spec["scaffold_files"] != {}
    assert spec["readme"] != ""


@pytest.mark.asyncio
async def test_scaffold_results_logger_valid_python():
    code = ScaffoldGeneratorAgent()._gen_results_logger()
    tree = ast.parse(code)
    func_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert "save_results" in func_names
    assert "json.dump" in code


@pytest.mark.asyncio
async def test_scaffold_syntax_error_triggers_correction():
    broken = "def foo(\n    # unclosed\n"
    call_count = {"n": 0}

    async def side_effect(*_args, **kwargs):
        messages = kwargs.get("messages", [])
        system = messages[0]["content"] if messages else ""
        call_count["n"] += 1
        choice = MagicMock()
        if "implementing a research paper" in system:
            choice.message.content = broken
        elif "syntax fixer" in system:
            choice.message.content = _VALID_IMPL
        elif "pytest test file" in system:
            choice.message.content = _VALID_TEST
        elif "Scan the provided" in system or "requirements.txt" in system:
            choice.message.content = "numpy\n"
        else:
            choice.message.content = "# readme\n"
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    agent = ScaffoldGeneratorAgent()
    ctx = AgentContext(
        job_id="t", claim=_SCAFFOLD_CLAIM,
        extra={"poc_spec": _SCAFFOLD_SPEC, "paper_metadata": _PAPER_META},
    )
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=side_effect)):
        result = await agent.run(ctx)
    assert result.status == "success"
    assert call_count["n"] == 5  # 4 generation + 1 syntax fix
    ast.parse(result.output["scaffold_files"]["implementation.py"])


@pytest.mark.asyncio
async def test_scaffold_persistent_syntax_error_is_inconclusive():
    broken = "def foo(\n    # still broken\n"

    async def always_broken(*_a, **_k):
        choice = MagicMock()
        choice.message.content = broken
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    agent = ScaffoldGeneratorAgent()
    ctx = AgentContext(
        job_id="t", claim=_SCAFFOLD_CLAIM,
        extra={"poc_spec": _SCAFFOLD_SPEC, "paper_metadata": _PAPER_META},
    )
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=always_broken)):
        result = await agent.run(ctx)
    assert result.status == "inconclusive"
    assert result.output.get("syntax_errors")


@pytest.mark.asyncio
async def test_scaffold_no_claim_returns_error():
    result = await ScaffoldGeneratorAgent().run(AgentContext(job_id="t"))
    assert result.status == "error"
    assert "claim" in result.error.lower()


@pytest.mark.asyncio
async def test_scaffold_llm_exception_returns_error():
    agent = ScaffoldGeneratorAgent()
    ctx = AgentContext(
        job_id="t", claim=_SCAFFOLD_CLAIM,
        extra={"poc_spec": _SCAFFOLD_SPEC, "paper_metadata": _PAPER_META},
    )
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=RuntimeError("OpenAI timeout"))):
        result = await agent.run(ctx)
    assert result.status == "error"
    assert "OpenAI timeout" in result.error


@pytest.mark.asyncio
async def test_scaffold_check_syntax_helper():
    agent = ScaffoldGeneratorAgent()
    assert agent._check_syntax({"implementation.py": "x = 1\n", "test_harness.py": "def test_foo():\n    assert True\n"}) == {}
    errs = agent._check_syntax({"implementation.py": "def bad(\n", "test_harness.py": "def test_foo():\n    assert True\n"})
    assert "implementation.py" in errs
    assert "test_harness.py" not in errs


# ══════════════════════════════════════════════════════════════════════════════
# 4. ResultsAnalyzerAgent
# ══════════════════════════════════════════════════════════════════════════════

def _spec(claim_id: str, criteria: list) -> dict:
    return PoCSpec(
        spec_id=f"spec-{claim_id}",
        claim_id=claim_id,
        testability=ClaimTestability.TESTABLE,
        success_criteria=[
            MetricCriterion(
                metric_name=c["metric_name"],
                paper_reported_value=c.get("paper_reported_value", ""),
                numeric_threshold=c.get("numeric_threshold"),
                tolerance=c.get("tolerance", 0.02),
                comparison=c.get("comparison", "within_tolerance"),
                experimental_conditions={},
            )
            for c in criteria
        ],
        failure_criteria=[],
        scaffold_files={},
        readme="",
    ).model_dump()


def _res_json(claim_id: str, metrics: dict) -> dict:
    return {"claim_id": claim_id, "timestamp": "2026-01-01T00:00:00Z", "metrics": metrics}


def _run_sync(ctx: AgentContext) -> AgentResult:
    import asyncio
    return asyncio.run(ResultsAnalyzerAgent().run(ctx))


def test_results_gte_reproduced():
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {"bleu": 29.0}),
        "poc_specs": [_spec("c1", [{"metric_name": "bleu", "numeric_threshold": 28.4, "comparison": "gte"}])],
    })
    r = _run_sync(ctx)
    assert r.output["claim_statuses"]["c1"] == ReproductionStatus.REPRODUCED.value


def test_results_lte_reproduced():
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {"loss": 0.45}),
        "poc_specs": [_spec("c1", [{"metric_name": "loss", "numeric_threshold": 0.5, "comparison": "lte"}])],
    })
    assert _run_sync(ctx).output["claim_statuses"]["c1"] == ReproductionStatus.REPRODUCED.value


def test_results_within_tolerance_reproduced():
    # threshold=100, tol=0.02 → abs_tol=2.0; achieved=101 → REPRODUCED
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {"acc": 101.0}),
        "poc_specs": [_spec("c1", [{"metric_name": "acc", "numeric_threshold": 100.0, "tolerance": 0.02, "comparison": "within_tolerance"}])],
    })
    assert _run_sync(ctx).output["claim_statuses"]["c1"] == ReproductionStatus.REPRODUCED.value


def test_results_gte_partial():
    # threshold=28.4, abs_tol=0.568; achieved=27.5 → shortfall=0.9 < 2x tol → PARTIAL
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {"bleu": 27.5}),
        "poc_specs": [_spec("c1", [{"metric_name": "bleu", "numeric_threshold": 28.4, "tolerance": 0.02, "comparison": "gte"}])],
    })
    assert _run_sync(ctx).output["claim_statuses"]["c1"] == ReproductionStatus.PARTIAL.value


def test_results_lte_partial():
    # threshold=0.5, abs_tol=0.01; achieved=0.515 → excess=0.015 < 2x → PARTIAL
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {"loss": 0.515}),
        "poc_specs": [_spec("c1", [{"metric_name": "loss", "numeric_threshold": 0.5, "tolerance": 0.02, "comparison": "lte"}])],
    })
    assert _run_sync(ctx).output["claim_statuses"]["c1"] == ReproductionStatus.PARTIAL.value


def test_results_gte_failed():
    # shortfall=8.4 >> 2x abs_tol → FAILED
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {"bleu": 20.0}),
        "poc_specs": [_spec("c1", [{"metric_name": "bleu", "numeric_threshold": 28.4, "tolerance": 0.02, "comparison": "gte"}])],
    })
    assert _run_sync(ctx).output["claim_statuses"]["c1"] == ReproductionStatus.FAILED.value


def test_results_missing_metric_is_failed():
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {}),
        "poc_specs": [_spec("c1", [{"metric_name": "bleu", "numeric_threshold": 28.4, "comparison": "gte"}])],
    })
    r = _run_sync(ctx)
    assert r.output["claim_statuses"]["c1"] == ReproductionStatus.FAILED.value
    assert "metric not found" in r.output["results"][0]["error_message"]


def test_results_null_threshold_is_failed():
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {"bleu": 28.4}),
        "poc_specs": [_spec("c1", [{"metric_name": "bleu", "numeric_threshold": None, "comparison": "gte"}])],
    })
    r = _run_sync(ctx)
    assert r.output["claim_statuses"]["c1"] == ReproductionStatus.FAILED.value
    assert "threshold" in r.output["results"][0]["error_message"]


def test_results_worst_status_wins():
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {"bleu": 29.0, "loss": 1.0}),
        "poc_specs": [_spec("c1", [
            {"metric_name": "bleu", "numeric_threshold": 28.4, "comparison": "gte"},
            {"metric_name": "loss", "numeric_threshold": 0.5, "comparison": "lte"},
        ])],
    })
    r = _run_sync(ctx)
    assert r.output["claim_statuses"]["c1"] == ReproductionStatus.FAILED.value
    assert len(r.output["results"]) == 2


def test_results_multiple_claims():
    ctx = AgentContext(job_id="t", extra={
        "results_json": [
            _res_json("c1", {"bleu": 29.0}),
            _res_json("c2", {"loss": 0.6}),
        ],
        "poc_specs": [
            _spec("c1", [{"metric_name": "bleu", "numeric_threshold": 28.4, "comparison": "gte"}]),
            _spec("c2", [{"metric_name": "loss", "numeric_threshold": 0.5, "comparison": "lte"}]),
        ],
    })
    r = _run_sync(ctx)
    assert r.output["claim_statuses"]["c1"] == ReproductionStatus.REPRODUCED.value
    assert r.output["claim_statuses"]["c2"] == ReproductionStatus.FAILED.value


def test_results_dict_keyed_specs():
    spec = _spec("c1", [{"metric_name": "bleu", "numeric_threshold": 28.4, "comparison": "gte"}])
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {"bleu": 29.0}),
        "poc_specs": {"c1": spec},
    })
    assert _run_sync(ctx).output["claim_statuses"]["c1"] == ReproductionStatus.REPRODUCED.value


def test_results_unknown_claim_skipped():
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c999", {"bleu": 29.0}),
        "poc_specs": [_spec("c1", [{"metric_name": "bleu", "numeric_threshold": 28.4, "comparison": "gte"}])],
    })
    r = _run_sync(ctx)
    assert "c999" not in r.output["claim_statuses"]
    assert r.output["results"] == []


def test_results_delta_correct():
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {"bleu": 30.0}),
        "poc_specs": [_spec("c1", [{"metric_name": "bleu", "numeric_threshold": 28.4, "comparison": "gte"}])],
    })
    row = _run_sync(ctx).output["results"][0]
    assert abs(row["delta"] - (30.0 - 28.4)) < 1e-6


def test_results_no_criteria_is_pending():
    ctx = AgentContext(job_id="t", extra={
        "results_json": _res_json("c1", {"bleu": 29.0}),
        "poc_specs": [_spec("c1", [])],
    })
    assert _run_sync(ctx).output["claim_statuses"]["c1"] == ReproductionStatus.PENDING.value


# ══════════════════════════════════════════════════════════════════════════════
# 5. ReproducibilityReportAgent
# ══════════════════════════════════════════════════════════════════════════════

def _report_spec(claim_id: str) -> dict:
    return PoCSpec(
        spec_id=f"spec-{claim_id}",
        claim_id=claim_id,
        testability=ClaimTestability.TESTABLE,
        success_criteria=[MetricCriterion(
            metric_name="bleu", paper_reported_value="28.4 BLEU",
            numeric_threshold=28.4, tolerance=0.02, comparison="gte",
            experimental_conditions={},
        )],
        failure_criteria=[],
        scaffold_files={},
        readme="",
    ).model_dump()


def _exp(claim_id: str, status: ReproductionStatus, achieved: float = 29.0) -> dict:
    return ExperimentResult(
        claim_id=claim_id, metric_name="bleu",
        achieved_value=achieved, status=status, delta=achieved - 28.4,
    ).model_dump()


_GAP_RESP = json.dumps({"explanations": [
    {"explanation": "Different dataset split", "likelihood": "high", "suggested_fix": "Use official WMT split"},
    {"explanation": "Batch size mismatch", "likelihood": "medium", "suggested_fix": "Set batch_size=4096"},
]})
_NEXT_RESP = json.dumps({"steps": ["Use official tokenizer", "Check learning rate", "Run more epochs"]})
_MD_RESP = "# Reproducibility Report\n\nReproduction rate: 50%\n"


def _report_llm_side_effect(*_args, **kwargs):
    messages = kwargs.get("messages", [])
    system = messages[0]["content"] if messages else ""
    choice = MagicMock()
    if "different result" in system.lower():
        choice.message.content = _GAP_RESP
    elif "next steps" in system.lower():
        choice.message.content = _NEXT_RESP
    else:
        choice.message.content = _MD_RESP
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.mark.asyncio
async def test_report_returns_valid_model():
    agent = ReproducibilityReportAgent()
    ctx = AgentContext(job_id="t", extra={
        "session_id": "sess-1",
        "experiment_results": [_exp("c1", ReproductionStatus.REPRODUCED)],
        "poc_specs": [_report_spec("c1")],
        "paper_metadata": _PAPER_META,
    })
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=_report_llm_side_effect)):
        result = await agent.run(ctx)
    assert result.status == "success"
    report = ReproducibilityReport.model_validate(result.output["report"])
    assert report.session_id == "sess-1"
    assert report.paper_title == "Attention Is All You Need"


@pytest.mark.asyncio
async def test_report_all_reproduced_rate_is_one():
    agent = ReproducibilityReportAgent()
    ctx = AgentContext(job_id="t", extra={
        "session_id": "sess-1",
        "experiment_results": [_exp("c1", ReproductionStatus.REPRODUCED), _exp("c2", ReproductionStatus.REPRODUCED)],
        "poc_specs": [_report_spec("c1"), _report_spec("c2")],
        "paper_metadata": _PAPER_META,
    })
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=_report_llm_side_effect)):
        result = await agent.run(ctx)
    r = result.output["report"]
    assert r["reproduced"] == 2
    assert abs(r["reproduction_rate"] - 1.0) < 1e-6
    assert r["gap_analyses"] == []


@pytest.mark.asyncio
async def test_report_mixed_statuses():
    agent = ReproducibilityReportAgent()
    ctx = AgentContext(job_id="t", extra={
        "session_id": "sess-1",
        "experiment_results": [
            _exp("c1", ReproductionStatus.REPRODUCED),
            _exp("c2", ReproductionStatus.PARTIAL, achieved=27.5),
            _exp("c3", ReproductionStatus.FAILED, achieved=20.0),
        ],
        "poc_specs": [_report_spec("c1"), _report_spec("c2"), _report_spec("c3")],
        "paper_metadata": _PAPER_META,
    })
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=_report_llm_side_effect)):
        result = await agent.run(ctx)
    r = result.output["report"]
    assert r["reproduced"] == 1
    assert r["partial"] == 1
    assert r["failed"] == 1
    assert abs(r["reproduction_rate"] - 1 / 3) < 1e-6


@pytest.mark.asyncio
async def test_report_gap_analysis_for_failures():
    call_log = []

    async def tracking(*_args, **kwargs):
        messages = kwargs.get("messages", [])
        system = messages[0]["content"] if messages else ""
        call_log.append(system[:60])
        return (await AsyncMock(side_effect=_report_llm_side_effect)(*_args, **kwargs))

    agent = ReproducibilityReportAgent()
    ctx = AgentContext(job_id="t", extra={
        "session_id": "sess-1",
        "experiment_results": [_exp("c1", ReproductionStatus.REPRODUCED), _exp("c2", ReproductionStatus.FAILED, achieved=20.0)],
        "poc_specs": [_report_spec("c1"), _report_spec("c2")],
        "paper_metadata": _PAPER_META,
    })
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=_report_llm_side_effect)):
        result = await agent.run(ctx)
    r = result.output["report"]
    assert len(r["gap_analyses"]) > 0
    assert all(g["claim_id"] == "c2" for g in r["gap_analyses"])


@pytest.mark.asyncio
async def test_report_no_gap_analysis_for_all_reproduced():
    gap_calls = []

    async def spy(*_args, **kwargs):
        messages = kwargs.get("messages", [])
        system = messages[0]["content"] if messages else ""
        if "different result" in system:
            gap_calls.append(True)
        choice = MagicMock()
        choice.message.content = _MD_RESP
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    agent = ReproducibilityReportAgent()
    ctx = AgentContext(job_id="t", extra={
        "session_id": "sess-1",
        "experiment_results": [_exp("c1", ReproductionStatus.REPRODUCED)],
        "poc_specs": [_report_spec("c1")],
        "paper_metadata": _PAPER_META,
    })
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=spy)):
        await agent.run(ctx)
    assert gap_calls == []


@pytest.mark.asyncio
async def test_report_what_to_try_next_populated():
    agent = ReproducibilityReportAgent()
    ctx = AgentContext(job_id="t", extra={
        "session_id": "sess-1",
        "experiment_results": [_exp("c1", ReproductionStatus.FAILED, achieved=20.0)],
        "poc_specs": [_report_spec("c1")],
        "paper_metadata": _PAPER_META,
    })
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=_report_llm_side_effect)):
        result = await agent.run(ctx)
    assert len(result.output["report"]["what_to_try_next"]) > 0


@pytest.mark.asyncio
async def test_report_markdown_non_empty():
    agent = ReproducibilityReportAgent()
    ctx = AgentContext(job_id="t", extra={
        "session_id": "sess-1",
        "experiment_results": [_exp("c1", ReproductionStatus.REPRODUCED)],
        "poc_specs": [_report_spec("c1")],
        "paper_metadata": _PAPER_META,
    })
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=_report_llm_side_effect)):
        result = await agent.run(ctx)
    assert result.output["report"]["markdown_report"].strip()


@pytest.mark.asyncio
async def test_report_gap_llm_failure_graceful():
    async def failing(*_args, **kwargs):
        messages = kwargs.get("messages", [])
        system = messages[0]["content"] if messages else ""
        if "different result" in system:
            raise RuntimeError("timeout")
        choice = MagicMock()
        choice.message.content = _MD_RESP
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    agent = ReproducibilityReportAgent()
    ctx = AgentContext(job_id="t", extra={
        "session_id": "sess-1",
        "experiment_results": [_exp("c1", ReproductionStatus.FAILED, achieved=10.0)],
        "poc_specs": [_report_spec("c1")],
        "paper_metadata": _PAPER_META,
    })
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=failing)):
        result = await agent.run(ctx)
    assert result.status == "success"
    assert result.output["report"]["gap_analyses"] == []


@pytest.mark.asyncio
async def test_report_empty_results_zeros():
    agent = ReproducibilityReportAgent()
    ctx = AgentContext(job_id="t", extra={
        "session_id": "sess-1",
        "experiment_results": [],
        "poc_specs": [_report_spec("c1"), _report_spec("c2")],
        "paper_metadata": _PAPER_META,
    })
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=_report_llm_side_effect)):
        result = await agent.run(ctx)
    r = result.output["report"]
    assert r["total_testable_claims"] == 2
    assert r["reproduced"] == 0
    assert r["reproduction_rate"] == 0.0


@pytest.mark.asyncio
async def test_report_invalid_results_returns_error():
    agent = ReproducibilityReportAgent()
    ctx = AgentContext(job_id="t", extra={
        "session_id": "sess-1",
        "experiment_results": [{"bad_field": "no claim_id or status"}],
        "poc_specs": [_report_spec("c1")],
        "paper_metadata": _PAPER_META,
    })
    with patch.object(agent._client.chat.completions, "create", new=AsyncMock(side_effect=_report_llm_side_effect)):
        result = await agent.run(ctx)
    assert result.status == "error"
    assert result.output == {"report": {}}


# ══════════════════════════════════════════════════════════════════════════════
# 6. PoCOrchestrator
# ══════════════════════════════════════════════════════════════════════════════

def _all_agent_patches(tmp_path):
    return (
        patch.object(ParserAgent, "run", new=AsyncMock(return_value=_ok(_PARSER_OUT))),
        patch.object(ClaimExtractorAgent, "run", new=AsyncMock(return_value=_ok(_EXTRACTOR_OUT))),
        patch.object(DAGBuilderAgent, "run", new=AsyncMock(return_value=_ok(_DAG_OUT))),
        patch.object(ClaimFilterAgent, "run", new=AsyncMock(return_value=_ok(_FILTER_OUT))),
        patch.object(MetricExtractorAgent, "run", new=AsyncMock(return_value=_ok(_METRIC_OUT))),
        patch.object(ScaffoldGeneratorAgent, "run", new=AsyncMock(return_value=_ok(_SCAFFOLD_OUT))),
        patch("poc.orchestrator._OUTPUTS_DIR", tmp_path),
    )


@pytest.mark.asyncio
async def test_orchestrator_happy_path(tmp_path):
    jid = _new_job()
    with _all_agent_patches(tmp_path)[0], _all_agent_patches(tmp_path)[1], _all_agent_patches(tmp_path)[2], _all_agent_patches(tmp_path)[3], _all_agent_patches(tmp_path)[4], _all_agent_patches(tmp_path)[5], _all_agent_patches(tmp_path)[6]:
        await PoCOrchestrator().run(jid)
    assert job_store.get(jid)["status"] == "complete"


@pytest.mark.asyncio
async def test_orchestrator_poc_specs_stored(tmp_path):
    jid = _new_job()
    with (
        patch.object(ParserAgent, "run", new=AsyncMock(return_value=_ok(_PARSER_OUT))),
        patch.object(ClaimExtractorAgent, "run", new=AsyncMock(return_value=_ok(_EXTRACTOR_OUT))),
        patch.object(DAGBuilderAgent, "run", new=AsyncMock(return_value=_ok(_DAG_OUT))),
        patch.object(ClaimFilterAgent, "run", new=AsyncMock(return_value=_ok(_FILTER_OUT))),
        patch.object(MetricExtractorAgent, "run", new=AsyncMock(return_value=_ok(_METRIC_OUT))),
        patch.object(ScaffoldGeneratorAgent, "run", new=AsyncMock(return_value=_ok(_SCAFFOLD_OUT))),
        patch("poc.orchestrator._OUTPUTS_DIR", tmp_path),
    ):
        await PoCOrchestrator().run(jid)
    job = job_store.get(jid)
    assert "c1" in job["poc_specs"]
    assert "scaffold_files" in job["poc_specs"]["c1"]


@pytest.mark.asyncio
async def test_orchestrator_only_testable_claims_get_scaffold(tmp_path):
    jid = _new_job()
    scaffold_calls = []

    async def capture(ctx):
        scaffold_calls.append(ctx.claim.claim_id)
        return _ok(_SCAFFOLD_OUT)

    with (
        patch.object(ParserAgent, "run", new=AsyncMock(return_value=_ok(_PARSER_OUT))),
        patch.object(ClaimExtractorAgent, "run", new=AsyncMock(return_value=_ok(_EXTRACTOR_OUT))),
        patch.object(DAGBuilderAgent, "run", new=AsyncMock(return_value=_ok(_DAG_OUT))),
        patch.object(ClaimFilterAgent, "run", new=AsyncMock(return_value=_ok(_FILTER_OUT))),
        patch.object(MetricExtractorAgent, "run", new=AsyncMock(return_value=_ok(_METRIC_OUT))),
        patch.object(ScaffoldGeneratorAgent, "run", new=AsyncMock(side_effect=capture)),
        patch("poc.orchestrator._OUTPUTS_DIR", tmp_path),
    ):
        await PoCOrchestrator().run(jid)

    assert scaffold_calls == ["c1"]
    assert "c2" not in job_store.get(jid)["poc_specs"]


@pytest.mark.asyncio
async def test_orchestrator_node_classified_events(tmp_path):
    jid = _new_job()
    events = []

    original = event_bus.publish
    async def capture(j, e):
        events.append(e)
        await original(j, e)

    with (
        patch.object(ParserAgent, "run", new=AsyncMock(return_value=_ok(_PARSER_OUT))),
        patch.object(ClaimExtractorAgent, "run", new=AsyncMock(return_value=_ok(_EXTRACTOR_OUT))),
        patch.object(DAGBuilderAgent, "run", new=AsyncMock(return_value=_ok(_DAG_OUT))),
        patch.object(ClaimFilterAgent, "run", new=AsyncMock(return_value=_ok(_FILTER_OUT))),
        patch.object(MetricExtractorAgent, "run", new=AsyncMock(return_value=_ok(_METRIC_OUT))),
        patch.object(ScaffoldGeneratorAgent, "run", new=AsyncMock(return_value=_ok(_SCAFFOLD_OUT))),
        patch.object(event_bus, "publish", side_effect=capture),
        patch("poc.orchestrator._OUTPUTS_DIR", tmp_path),
    ):
        await PoCOrchestrator().run(jid)

    classified = [e for e in events if e.event_type == DAGEventType.NODE_CLASSIFIED]
    ids = {e.claim_id for e in classified}
    assert "c1" in ids and "c2" in ids
    c1_ev = next(e for e in classified if e.claim_id == "c1")
    assert c1_ev.payload["testability"] == "testable"
    c2_ev = next(e for e in classified if e.claim_id == "c2")
    assert c2_ev.payload["testability"] == "theoretical"


@pytest.mark.asyncio
async def test_orchestrator_poc_ready_event(tmp_path):
    jid = _new_job()
    events = []

    async def capture(j, e):
        events.append(e)

    with (
        patch.object(ParserAgent, "run", new=AsyncMock(return_value=_ok(_PARSER_OUT))),
        patch.object(ClaimExtractorAgent, "run", new=AsyncMock(return_value=_ok(_EXTRACTOR_OUT))),
        patch.object(DAGBuilderAgent, "run", new=AsyncMock(return_value=_ok(_DAG_OUT))),
        patch.object(ClaimFilterAgent, "run", new=AsyncMock(return_value=_ok(_FILTER_OUT))),
        patch.object(MetricExtractorAgent, "run", new=AsyncMock(return_value=_ok(_METRIC_OUT))),
        patch.object(ScaffoldGeneratorAgent, "run", new=AsyncMock(return_value=_ok(_SCAFFOLD_OUT))),
        patch.object(event_bus, "publish", side_effect=capture),
        patch("poc.orchestrator._OUTPUTS_DIR", tmp_path),
    ):
        await PoCOrchestrator().run(jid)

    ready = [e for e in events if e.event_type == DAGEventType.POC_READY]
    assert len(ready) == 1
    assert ready[0].payload["testable_count"] == 1


@pytest.mark.asyncio
async def test_orchestrator_zip_structure(tmp_path):
    jid = _new_job()

    with (
        patch.object(ParserAgent, "run", new=AsyncMock(return_value=_ok(_PARSER_OUT))),
        patch.object(ClaimExtractorAgent, "run", new=AsyncMock(return_value=_ok(_EXTRACTOR_OUT))),
        patch.object(DAGBuilderAgent, "run", new=AsyncMock(return_value=_ok(_DAG_OUT))),
        patch.object(ClaimFilterAgent, "run", new=AsyncMock(return_value=_ok(_FILTER_OUT))),
        patch.object(MetricExtractorAgent, "run", new=AsyncMock(return_value=_ok(_METRIC_OUT))),
        patch.object(ScaffoldGeneratorAgent, "run", new=AsyncMock(return_value=_ok(_SCAFFOLD_OUT))),
        patch("poc.orchestrator._OUTPUTS_DIR", tmp_path),
    ):
        await PoCOrchestrator().run(jid)

    zip_path = job_store.get(jid)["zip_path"]
    assert Path(zip_path).exists()
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert "poc_scaffold/README.md" in names
    for fname in ("implementation.py", "test_harness.py", "results_logger.py", "requirements.txt", "README.md"):
        assert f"poc_scaffold/c1/{fname}" in names
    assert not any("c2" in n for n in names)


@pytest.mark.asyncio
async def test_orchestrator_metric_extractor_exception_skipped(tmp_path):
    jid = _new_job()

    with (
        patch.object(ParserAgent, "run", new=AsyncMock(return_value=_ok(_PARSER_OUT))),
        patch.object(ClaimExtractorAgent, "run", new=AsyncMock(return_value=_ok(_EXTRACTOR_OUT))),
        patch.object(DAGBuilderAgent, "run", new=AsyncMock(return_value=_ok(_DAG_OUT))),
        patch.object(ClaimFilterAgent, "run", new=AsyncMock(return_value=_ok(_FILTER_OUT))),
        patch.object(MetricExtractorAgent, "run", new=AsyncMock(side_effect=RuntimeError("LLM timeout"))),
        patch.object(ScaffoldGeneratorAgent, "run", new=AsyncMock(return_value=_ok(_SCAFFOLD_OUT))),
        patch("poc.orchestrator._OUTPUTS_DIR", tmp_path),
    ):
        await PoCOrchestrator().run(jid)

    job = job_store.get(jid)
    assert job["status"] == "complete"
    assert job["poc_specs"] == {}


@pytest.mark.asyncio
async def test_orchestrator_scaffold_exception_job_completes(tmp_path):
    jid = _new_job()

    with (
        patch.object(ParserAgent, "run", new=AsyncMock(return_value=_ok(_PARSER_OUT))),
        patch.object(ClaimExtractorAgent, "run", new=AsyncMock(return_value=_ok(_EXTRACTOR_OUT))),
        patch.object(DAGBuilderAgent, "run", new=AsyncMock(return_value=_ok(_DAG_OUT))),
        patch.object(ClaimFilterAgent, "run", new=AsyncMock(return_value=_ok(_FILTER_OUT))),
        patch.object(MetricExtractorAgent, "run", new=AsyncMock(return_value=_ok(_METRIC_OUT))),
        patch.object(ScaffoldGeneratorAgent, "run", new=AsyncMock(side_effect=RuntimeError("codegen failed"))),
        patch("poc.orchestrator._OUTPUTS_DIR", tmp_path),
    ):
        await PoCOrchestrator().run(jid)

    assert job_store.get(jid)["status"] == "complete"


@pytest.mark.asyncio
async def test_orchestrator_parser_failure_sets_error(tmp_path):
    jid = _new_job()

    with (
        patch.object(ParserAgent, "run", new=AsyncMock(side_effect=RuntimeError("PDF corrupt"))),
        patch("poc.orchestrator._OUTPUTS_DIR", tmp_path),
    ):
        await PoCOrchestrator().run(jid)

    job = job_store.get(jid)
    assert job["status"] == "error"
    assert "PDF corrupt" in job.get("error", "")


@pytest.mark.asyncio
async def test_orchestrator_no_claims_completes_gracefully(tmp_path):
    jid = _new_job()

    with (
        patch.object(ParserAgent, "run", new=AsyncMock(return_value=_ok(_PARSER_OUT))),
        patch.object(ClaimExtractorAgent, "run", new=AsyncMock(return_value=_ok({"claims": []}))),
        patch.object(DAGBuilderAgent, "run", new=AsyncMock(return_value=_ok({"edges": []}))),
        patch.object(ClaimFilterAgent, "run", new=AsyncMock(return_value=_ok({"testable": [], "theoretical": [], "classifications": {}}))),
        patch("poc.orchestrator._OUTPUTS_DIR", tmp_path),
    ):
        await PoCOrchestrator().run(jid)

    job = job_store.get(jid)
    assert job["status"] == "complete"
    assert job["poc_specs"] == {}
    assert Path(job["zip_path"]).exists()


# ══════════════════════════════════════════════════════════════════════════════
# 7. PoC API endpoints
# ══════════════════════════════════════════════════════════════════════════════

def test_api_submit_creates_session():
    dummy_pdf = b"%PDF-1.4 dummy"
    with patch("poc.orchestrator.PoCOrchestrator.run", new=AsyncMock(return_value=None)):
        resp = client.post("/poc", files={"file": ("paper.pdf", io.BytesIO(dummy_pdf), "application/pdf")})
    assert resp.status_code == 200
    body = resp.json()
    assert "session_id" in body
    assert body["status"] == "processing"
    assert job_store.exists(body["session_id"])


def test_api_submit_no_file():
    with patch("poc.orchestrator.PoCOrchestrator.run", new=AsyncMock(return_value=None)):
        resp = client.post("/poc")
    assert resp.status_code == 200
    assert "session_id" in resp.json()


def test_api_claims_404_unknown():
    assert client.get("/poc/does-not-exist/claims").status_code == 404


def test_api_claims_returns_counts():
    sid = _complete_session()
    body = client.get(f"/poc/{sid}/claims").json()
    assert body["total"] == 2
    assert body["testable"] == 1
    assert body["theoretical"] == 1


def test_api_claims_no_scaffold_files_in_summary():
    sid = _complete_session()
    for claim in client.get(f"/poc/{sid}/claims").json()["claims"]:
        if claim["testability"] == "testable":
            assert "scaffold_files" not in (claim.get("spec_summary") or {})


def test_api_claims_empty_session():
    sid = _new_job()
    resp = client.get(f"/poc/{sid}/claims")
    assert resp.status_code == 200
    assert resp.json() == {"total": 0, "testable": 0, "theoretical": 0, "claims": []}


def test_api_spec_404_unknown_session():
    assert client.get("/poc/no-session/claim/c1/spec").status_code == 404


def test_api_spec_404_theoretical_claim():
    sid = _complete_session()
    assert client.get(f"/poc/{sid}/claim/c2/spec").status_code == 404


def test_api_spec_returns_scaffold_files():
    sid = _complete_session()
    body = client.get(f"/poc/{sid}/claim/c1/spec").json()
    assert "scaffold_files" in body
    assert "implementation.py" in body["scaffold_files"]


def test_api_scaffold_zip_404_unknown():
    assert client.get("/poc/no-session/scaffold.zip").status_code == 404


def test_api_scaffold_zip_202_not_ready():
    sid = _new_job()
    assert client.get(f"/poc/{sid}/scaffold.zip").status_code == 202


def test_api_scaffold_zip_returns_file(tmp_path):
    zip_path = tmp_path / "test.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("poc_scaffold/README.md", "# test")
    zip_path.write_bytes(buf.getvalue())

    sid = job_store.create_job(mode="poc", pdf_path="/f.pdf", zip_path=str(zip_path), paper_metadata={"title": "Test"})
    if not event_bus.channel_exists(sid):
        event_bus.create_channel(sid)

    resp = client.get(f"/poc/{sid}/scaffold.zip")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert "attachment" in resp.headers.get("content-disposition", "")


def test_api_upload_results_404_unknown():
    assert client.post("/poc/no-session/results", json={"claim_id": "c1", "metrics": {}}).status_code == 404


def test_api_upload_results_422_bad_json():
    sid = _new_job()
    resp = client.post(f"/poc/{sid}/results", content=b"not json", headers={"content-type": "application/json"})
    assert resp.status_code == 422


def test_api_upload_results_returns_analyzing():
    sid = _new_job()
    mock_analyzer = AsyncMock(return_value=AgentResult(
        agent_id="results_analyzer", status="success",
        output={"results": [], "claim_statuses": {}}, confidence=0.9,
    ))
    mock_reporter = AsyncMock(return_value=AgentResult(
        agent_id="reproducibility_report", status="success",
        output={"report": _REPORT_DICT}, confidence=0.85,
    ))
    with (
        patch("poc.api.ResultsAnalyzerAgent.run", new=mock_analyzer),
        patch("poc.api.ReproducibilityReportAgent.run", new=mock_reporter),
    ):
        resp = client.post(f"/poc/{sid}/results", json={"claim_id": "c1", "metrics": {"bleu": 29.0}})
    assert resp.status_code == 200
    assert resp.json()["status"] == "analyzing"


def test_api_upload_results_accepts_file_upload():
    sid = _new_job()
    payload = json.dumps({"claim_id": "c1", "metrics": {"bleu": 29.0}}).encode()
    mock_analyzer = AsyncMock(return_value=AgentResult(
        agent_id="results_analyzer", status="success",
        output={"results": [], "claim_statuses": {}}, confidence=0.9,
    ))
    mock_reporter = AsyncMock(return_value=AgentResult(
        agent_id="reproducibility_report", status="success",
        output={"report": _REPORT_DICT}, confidence=0.85,
    ))
    with (
        patch("poc.api.ResultsAnalyzerAgent.run", new=mock_analyzer),
        patch("poc.api.ReproducibilityReportAgent.run", new=mock_reporter),
    ):
        resp = client.post(
            f"/poc/{sid}/results",
            files={"file": ("results.json", io.BytesIO(payload), "application/json")},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "analyzing"


def test_api_report_404_unknown():
    assert client.get("/poc/no-session/report").status_code == 404


def test_api_report_202_analysis_pending():
    sid = job_store.create_job(mode="poc", pdf_path="/f.pdf", analysis_status="analyzing")
    if not event_bus.channel_exists(sid):
        event_bus.create_channel(sid)
    assert client.get(f"/poc/{sid}/report").status_code == 202


def test_api_report_202_no_analysis():
    sid = _new_job()
    assert client.get(f"/poc/{sid}/report").status_code == 202


def test_api_report_returns_report():
    sid = _complete_session()
    body = client.get(f"/poc/{sid}/report").json()
    assert body["session_id"] == "sess-1"
    assert body["reproduction_rate"] == 1.0


def test_api_report_markdown_404_unknown():
    assert client.get("/poc/no-session/report/markdown").status_code == 404


def test_api_report_markdown_202_not_ready():
    sid = job_store.create_job(mode="poc", pdf_path="/f.pdf", analysis_status="analyzing")
    if not event_bus.channel_exists(sid):
        event_bus.create_channel(sid)
    assert client.get(f"/poc/{sid}/report/markdown").status_code == 202


def test_api_report_markdown_returns_text():
    sid = _complete_session()
    resp = client.get(f"/poc/{sid}/report/markdown")
    assert resp.status_code == 200
    assert "markdown" in resp.headers["content-type"]
    assert "# Report" in resp.text


def test_api_dag_404_unknown():
    assert client.get("/poc/no-session/dag").status_code == 404


def test_api_dag_empty_when_no_dag():
    sid = _new_job()
    assert client.get(f"/poc/{sid}/dag").json() == {"nodes": [], "edges": []}


def test_api_dag_includes_testability_and_reproduction_status():
    dag = DAG()
    dag.add_node("c1")
    dag.add_node("c2")
    sid = _complete_session()
    job_store.update(sid, dag=dag)

    body = client.get(f"/poc/{sid}/dag").json()
    nodes = {n["id"]: n for n in body["nodes"]}
    assert nodes["c1"]["testability"] == "testable"
    assert nodes["c1"]["reproduction_status"] == "REPRODUCED"
    assert nodes["c2"]["testability"] == "theoretical"
    assert nodes["c2"]["reproduction_status"] == "PENDING"


def test_api_dag_edges_present():
    dag = DAG()
    dag.add_edge("c1", "c2")
    sid = job_store.create_job(mode="poc", pdf_path="/f.pdf", poc_specs={})
    if not event_bus.channel_exists(sid):
        event_bus.create_channel(sid)
    job_store.update(sid, dag=dag)
    body = client.get(f"/poc/{sid}/dag").json()
    assert {"from": "c1", "to": "c2"} in body["edges"]


# ══════════════════════════════════════════════════════════════════════════════
# 8. End-to-end flow
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_full_poc_pipeline_end_to_end(tmp_path):
    """
    Runs the complete PoC user journey without any intermediate job_store manipulation.

    1. Create job (simulating POST /poc)
    2. Run orchestrator with all agents mocked
    3. Verify GET /claims, /dag, /claim/{id}/spec, /scaffold.zip
    4. Upload results via POST /results (mocked analysis)
    5. Verify GET /report, /report/markdown reflect uploaded results
    """

    # ── Step 1: create session ────────────────────────────────────────────────
    sid = _new_job(pdf_path="/fake/attention.pdf")

    # ── Step 2: run orchestrator ──────────────────────────────────────────────
    with (
        patch.object(ParserAgent, "run", new=AsyncMock(return_value=_ok(_PARSER_OUT))),
        patch.object(ClaimExtractorAgent, "run", new=AsyncMock(return_value=_ok(_EXTRACTOR_OUT))),
        patch.object(DAGBuilderAgent, "run", new=AsyncMock(return_value=_ok(_DAG_OUT))),
        patch.object(ClaimFilterAgent, "run", new=AsyncMock(return_value=_ok(_FILTER_OUT))),
        patch.object(MetricExtractorAgent, "run", new=AsyncMock(return_value=_ok(_METRIC_OUT))),
        patch.object(ScaffoldGeneratorAgent, "run", new=AsyncMock(return_value=_ok(_SCAFFOLD_OUT))),
        patch("poc.orchestrator._OUTPUTS_DIR", tmp_path),
    ):
        await PoCOrchestrator().run(sid)

    job = job_store.get(sid)
    assert job["status"] == "complete", f"Expected complete, got {job['status']}"

    # ── Step 3a: GET /claims ──────────────────────────────────────────────────
    resp = client.get(f"/poc/{sid}/claims")
    assert resp.status_code == 200
    claims_body = resp.json()
    assert claims_body["total"] == 2
    assert claims_body["testable"] == 1
    assert claims_body["theoretical"] == 1
    testable_ids = [c["claim_id"] for c in claims_body["claims"] if c["testability"] == "testable"]
    assert testable_ids == ["c1"]
    for c in claims_body["claims"]:
        if c["testability"] == "testable":
            assert "scaffold_files" not in (c.get("spec_summary") or {})

    # ── Step 3b: GET /dag ─────────────────────────────────────────────────────
    resp = client.get(f"/poc/{sid}/dag")
    assert resp.status_code == 200
    dag_body = resp.json()
    node_ids = {n["id"] for n in dag_body["nodes"]}
    assert "c1" in node_ids and "c2" in node_ids
    c1_node = next(n for n in dag_body["nodes"] if n["id"] == "c1")
    assert c1_node["testability"] == "testable"
    assert c1_node["reproduction_status"] == "PENDING"  # no results yet

    # ── Step 3c: GET /claim/{id}/spec ─────────────────────────────────────────
    resp = client.get(f"/poc/{sid}/claim/c1/spec")
    assert resp.status_code == 200
    spec = resp.json()
    assert "scaffold_files" in spec
    assert "implementation.py" in spec["scaffold_files"]
    assert len(spec["success_criteria"]) == 1
    assert spec["success_criteria"][0]["metric_name"] == "bleu"

    # theoretical claim must 404
    assert client.get(f"/poc/{sid}/claim/c2/spec").status_code == 404

    # ── Step 3d: GET /scaffold.zip ────────────────────────────────────────────
    resp = client.get(f"/poc/{sid}/scaffold.zip")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = zf.namelist()
    assert "poc_scaffold/README.md" in names
    assert "poc_scaffold/c1/implementation.py" in names

    # ── Step 4: POST /results ─────────────────────────────────────────────────
    results_payload = {"claim_id": "c1", "timestamp": "2026-04-25T00:00:00Z", "metrics": {"bleu": 29.0}}
    mock_analyzer = AsyncMock(return_value=AgentResult(
        agent_id="results_analyzer", status="success",
        output={
            "results": [{"claim_id": "c1", "metric_name": "bleu", "achieved_value": 29.0, "status": "REPRODUCED", "delta": 0.6, "error_message": None}],
            "claim_statuses": {"c1": "REPRODUCED"},
        },
        confidence=0.9,
    ))
    mock_reporter = AsyncMock(return_value=AgentResult(
        agent_id="reproducibility_report", status="success",
        output={"report": {**_REPORT_DICT, "session_id": sid}},
        confidence=0.85,
    ))
    with (
        patch("poc.api.ResultsAnalyzerAgent.run", new=mock_analyzer),
        patch("poc.api.ReproducibilityReportAgent.run", new=mock_reporter),
    ):
        resp = client.post(f"/poc/{sid}/results", json=results_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "analyzing"

    # Wait for the background _analyze() task to finish (TestClient runs it synchronously)
    import asyncio
    await asyncio.sleep(0)

    # Manually mark analysis complete (background task runs outside TestClient's event loop)
    job_store.update(sid, analysis_status="complete", report={**_REPORT_DICT, "session_id": sid})

    # ── Step 5a: GET /report ──────────────────────────────────────────────────
    resp = client.get(f"/poc/{sid}/report")
    assert resp.status_code == 200
    report = resp.json()
    assert report["session_id"] == sid
    assert report["reproduced"] == 1
    assert report["reproduction_rate"] == 1.0
    assert report["results"][0]["status"] == "REPRODUCED"

    # ── Step 5b: GET /report/markdown ────────────────────────────────────────
    resp = client.get(f"/poc/{sid}/report/markdown")
    assert resp.status_code == 200
    assert "markdown" in resp.headers["content-type"]
    assert len(resp.text.strip()) > 0

    # ── Step 5c: DAG now shows reproduction status ────────────────────────────
    resp = client.get(f"/poc/{sid}/dag")
    nodes = {n["id"]: n for n in resp.json()["nodes"]}
    assert nodes["c1"]["reproduction_status"] == "REPRODUCED"
