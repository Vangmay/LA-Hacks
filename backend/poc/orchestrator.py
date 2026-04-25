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


class PoCOrchestrator:

    async def run(self, job_id: str, **kwargs) -> None:
        try:
            await self._run(job_id)
        except Exception as exc:
            logger.exception("PoC orchestrator failed for %s", job_id)
            job_store.update(job_id, status="error", error=str(exc))

    async def _run(self, job_id: str) -> None:
        job_store.set_status(job_id, "processing")
        job = job_store.get(job_id)
        pdf_path: str = job.get("pdf_path", "")

        if not event_bus.channel_exists(job_id):
            event_bus.create_channel(job_id)

        # ── 1. Parse PDF ──────────────────────────────────────────────────────
        parser_result = await ParserAgent().run(
            AgentContext(job_id=job_id, extra={"pdf_path": pdf_path})
        )
        paper_metadata: dict = parser_result.output
        job_store.update(job_id, paper_metadata=paper_metadata)

        # ── 2. Extract claims ─────────────────────────────────────────────────
        ext_result = await ClaimExtractorAgent().run(
            AgentContext(job_id=job_id, extra={"parser_output": paper_metadata})
        )
        raw_claims: list = ext_result.output.get("claims", [])
        claim_units = [ClaimUnit.model_validate(c) for c in raw_claims]
        job_store.update(job_id, claims={c.claim_id: c.model_dump() for c in claim_units})

        # ── 3. Build DAG ──────────────────────────────────────────────────────
        dag_result = await DAGBuilderAgent().run(
            AgentContext(job_id=job_id, extra={"claims": raw_claims})
        )
        dag = DAG()
        for c in claim_units:
            dag.add_node(c.claim_id)
        for edge in dag_result.output.get("edges", []):
            dag.add_edge(edge["from"], edge["to"])
        job_store.update(job_id, dag=dag)

        # ── 4. Filter claims ──────────────────────────────────────────────────
        filter_result = await ClaimFilterAgent().run(
            AgentContext(job_id=job_id, extra={"claims": claim_units})
        )
        testable_ids: set = set(filter_result.output.get("testable", []))
        classifications: dict = filter_result.output.get("classifications", {})

        for claim in claim_units:
            testability = "testable" if claim.claim_id in testable_ids else "theoretical"
            await event_bus.publish(job_id, DAGEvent(
                event_id=str(uuid.uuid4()),
                job_id=job_id,
                event_type=DAGEventType.NODE_CLASSIFIED,
                claim_id=claim.claim_id,
                payload={
                    "testability": testability,
                    "reason": classifications.get(claim.claim_id, {}).get("reason", ""),
                },
                timestamp=datetime.utcnow(),
            ))

        testable_claims = [c for c in claim_units if c.claim_id in testable_ids]

        # ── 5. Extract metrics in parallel ────────────────────────────────────
        metric_results = await asyncio.gather(
            *[
                MetricExtractorAgent().run(
                    AgentContext(job_id=job_id, claim=c, extra={"paper_metadata": paper_metadata})
                )
                for c in testable_claims
            ],
            return_exceptions=True,
        )

        poc_specs: dict = {}
        for claim, result in zip(testable_claims, metric_results):
            if isinstance(result, Exception):
                logger.warning("MetricExtractorAgent failed for %s: %s", claim.claim_id, result)
                continue
            if result.status in ("success", "inconclusive"):
                poc_specs[claim.claim_id] = result.output

        # ── 6. Generate scaffolds in parallel (max 5 concurrent) ─────────────
        semaphore = asyncio.Semaphore(settings.max_parallel_claims)

        async def _scaffold_one(claim: ClaimUnit, spec: dict) -> tuple:
            async with semaphore:
                result = await ScaffoldGeneratorAgent().run(
                    AgentContext(
                        job_id=job_id,
                        claim=claim,
                        extra={"poc_spec": spec, "paper_metadata": paper_metadata},
                    )
                )
                return claim.claim_id, result

        scaffold_results = await asyncio.gather(
            *[
                _scaffold_one(claim, poc_specs[claim.claim_id])
                for claim in testable_claims
                if claim.claim_id in poc_specs
            ],
            return_exceptions=True,
        )

        for item in scaffold_results:
            if isinstance(item, Exception):
                logger.warning("ScaffoldGeneratorAgent raised: %s", item)
                continue
            claim_id, result = item
            if result.status in ("success", "inconclusive") and "poc_spec" in result.output:
                poc_specs[claim_id] = result.output["poc_spec"]

            await event_bus.publish(job_id, DAGEvent(
                event_id=str(uuid.uuid4()),
                job_id=job_id,
                event_type=DAGEventType.SCAFFOLD_GENERATED,
                claim_id=claim_id,
                payload={"status": result.status},
                timestamp=datetime.utcnow(),
            ))

        job_store.update(job_id, poc_specs=poc_specs)

        # ── 7. Package zip ────────────────────────────────────────────────────
        zip_path = await self._build_zip(job_id, poc_specs, paper_metadata)
        job_store.update(job_id, zip_path=zip_path)

        await event_bus.publish(job_id, DAGEvent(
            event_id=str(uuid.uuid4()),
            job_id=job_id,
            event_type=DAGEventType.POC_READY,
            payload={"zip_path": zip_path, "testable_count": len(testable_ids)},
            timestamp=datetime.utcnow(),
        ))

        job_store.set_status(job_id, "complete")

    async def _build_zip(self, job_id: str, poc_specs: dict, paper_metadata: dict) -> str:
        _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = str(_OUTPUTS_DIR / f"{job_id}_scaffold.zip")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("poc_scaffold/README.md", self._root_readme(poc_specs, paper_metadata))
            for claim_id, spec in poc_specs.items():
                scaffold_files = spec.get("scaffold_files", {})
                for filename in _SCAFFOLD_FILES:
                    content = scaffold_files.get(filename, f"# {filename} not generated\n")
                    zf.writestr(f"poc_scaffold/{claim_id}/{filename}", content)

        with open(zip_path, "wb") as f:
            f.write(buf.getvalue())

        return zip_path

    def _root_readme(self, poc_specs: dict, paper_metadata: dict) -> str:
        title = paper_metadata.get("title", "Unknown Paper")
        entries = "\n".join(f"- `poc_scaffold/{cid}/`" for cid in poc_specs)
        return (
            f"# PoC Scaffold — {title}\n\n"
            "This archive contains proof-of-concept scaffolds for each testable claim.\n\n"
            "## Claims included\n\n"
            f"{entries or '_(none)_'}\n\n"
            "## Running a scaffold\n\n"
            "```bash\n"
            "cd poc_scaffold/<claim_id>\n"
            "pip install -r requirements.txt\n"
            "pytest test_harness.py -v\n"
            "```\n\n"
            "## Uploading results\n\n"
            "After running tests, upload `poc_results.json`:\n"
            "`POST /poc/{session_id}/results`\n"
        )
