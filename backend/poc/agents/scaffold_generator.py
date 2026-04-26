import ast
import json
import logging

from openai import AsyncOpenAI

from backend.config import settings
from backend.models import ClaimUnit, PoCSpec
from backend.agents.base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)


class ScaffoldGeneratorAgent(BaseAgent):
    agent_id = "scaffold_generator"

    _client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def run(self, context: AgentContext) -> AgentResult:
        claim: ClaimUnit | None = context.extra.get("claim")
        if claim is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"scaffold_files": {}},
                confidence=0.0,
                error="No claim provided in context.extra['claim']",
            )

        poc_spec: dict = context.extra.get("poc_spec", {})
        paper_metadata: dict = context.extra.get("paper_metadata", {})

        try:
            scaffold_files = await self._generate_all_files(claim, poc_spec, paper_metadata)
        except Exception as exc:
            logger.error("ScaffoldGeneratorAgent failed for %s: %s", claim.claim_id, exc)
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=claim.claim_id,
                status="error",
                output={"scaffold_files": {}},
                confidence=0.0,
                error=str(exc),
            )

        # Syntax-check generated Python files; attempt one correction pass on failure
        syntax_errors = self._check_syntax(scaffold_files)
        if syntax_errors:
            for fname, err in syntax_errors.items():
                try:
                    scaffold_files[fname] = await self._fix_syntax(scaffold_files[fname], fname, err)
                except Exception as exc:
                    logger.warning("Syntax fix LLM call failed for %s: %s", fname, exc)

            still_broken = self._check_syntax(scaffold_files)
            if still_broken:
                return AgentResult(
                    agent_id=self.agent_id,
                    claim_id=claim.claim_id,
                    status="inconclusive",
                    output={"scaffold_files": scaffold_files, "syntax_errors": still_broken},
                    confidence=0.3,
                    error=f"Syntax errors remain after correction attempt: {still_broken}",
                )

        updated_spec = dict(poc_spec)
        updated_spec["scaffold_files"] = scaffold_files
        updated_spec["readme"] = scaffold_files.get("README.md", "")

        return AgentResult(
            agent_id=self.agent_id,
            claim_id=claim.claim_id,
            status="success",
            output={"scaffold_files": scaffold_files, "poc_spec": updated_spec},
            confidence=0.8,
        )

    # ── File generation ────────────────────────────────────────────────────────

    async def _generate_all_files(
        self, claim: ClaimUnit, poc_spec: dict, paper_metadata: dict
    ) -> dict:
        title = paper_metadata.get("title", "Unknown Paper")
        abstract = paper_metadata.get("abstract", "")
        sections = paper_metadata.get("sections", [])
        relevant_sections = "\n\n".join(
            f"## {s.get('title', '')}\n{s.get('content', '')[:1000]}" for s in sections[:5]
        )
        success_criteria_json = json.dumps(poc_spec.get("success_criteria", []), indent=2)

        impl_py = await self._gen_implementation(
            claim, title, abstract, relevant_sections, success_criteria_json
        )
        test_py = await self._gen_test_harness(success_criteria_json, impl_py)
        logger_py = self._gen_results_logger()
        req_txt = await self._gen_requirements(impl_py, test_py)
        readme_md = await self._gen_readme(claim, title, success_criteria_json)

        return {
            "implementation.py": impl_py,
            "test_harness.py": test_py,
            "results_logger.py": logger_py,
            "requirements.txt": req_txt,
            "README.md": readme_md,
        }

    async def _gen_implementation(
        self,
        claim: ClaimUnit,
        title: str,
        abstract: str,
        relevant_sections: str,
        success_criteria_json: str,
    ) -> str:
        system = (
            "You are implementing a research paper's method in Python. Generate clean, runnable code "
            "that implements the algorithm/method described in the claim and surrounding paper context.\n"
            "Requirements:\n"
            f"- Add a comment at the top: # Implements claim {claim.claim_id}: {claim.text[:100]}\n"
            "- Include detailed inline comments referencing specific paper sections "
            "(e.g. # See Section 3.2: Algorithm 1)\n"
            "- Use only standard Python + numpy + torch/sklearn as appropriate — no obscure dependencies\n"
            "- Include a main() function that runs a minimal demonstration\n"
            "- If the full method is too complex, implement the core component that tests the specific claim\n"
            "Return ONLY the Python code, no explanation."
        )
        user = (
            f"Claim: {claim.text}\n\n"
            f"Paper: {title}\nAbstract: {abstract[:500]}\n\n"
            f"Relevant sections:\n{relevant_sections}\n\n"
            f"Success criteria:\n{success_criteria_json}"
        )
        return await self._llm_call(system, user, max_tokens=2000)

    async def _gen_test_harness(self, success_criteria_json: str, impl_code: str) -> str:
        system = (
            "Generate a pytest test file that verifies the success criteria for this claim.\n"
            "Requirements:\n"
            "- Import from implementation.py\n"
            "- One test function per success criterion: def test_{metric_name}():\n"
            "- Each test function must call the implementation, measure the metric, and assert the criterion\n"
            "- Use the exact numeric thresholds and tolerances provided\n"
            "- Add a comment before each assert: # Paper reports: {paper_reported_value}\n"
            "- Include a results collection dict that accumulates all metrics for the logger\n"
            "- At the end of all tests, call save_results() from results_logger.py\n"
            "Return ONLY the pytest code."
        )
        user = f"Success criteria:\n{success_criteria_json}\n\nimplementation.py content:\n{impl_code}"
        return await self._llm_call(system, user, max_tokens=2000)

    def _gen_results_logger(self) -> str:
        return (
            "import json\n"
            "import platform\n"
            "from datetime import datetime, timezone\n"
            "\n"
            "\n"
            "def save_results(results: dict, output_path: str = \"poc_results.json\") -> None:\n"
            "    \"\"\"Write experiment results as JSON to output_path.\"\"\"\n"
            "    payload = {\n"
            "        \"claim_id\": results.get(\"claim_id\", \"\"),\n"
            "        \"timestamp\": datetime.now(timezone.utc).isoformat(),\n"
            "        \"metrics\": {k: v for k, v in results.items() if k != \"claim_id\"},\n"
            "        \"system_info\": {\n"
            "            \"python\": platform.python_version(),\n"
            "            \"platform\": platform.platform(),\n"
            "            \"processor\": platform.processor(),\n"
            "        },\n"
            "    }\n"
            "    with open(output_path, \"w\", encoding=\"utf-8\") as f:\n"
            "        json.dump(payload, f, indent=2)\n"
        )

    async def _gen_requirements(self, impl_code: str, test_code: str) -> str:
        system = (
            "Scan the provided Python files for import statements and generate a minimal requirements.txt. "
            "Include only third-party packages (not stdlib). One package per line, no version pinning "
            "unless critical. Return ONLY the requirements.txt content, nothing else."
        )
        user = f"implementation.py:\n{impl_code}\n\ntest_harness.py:\n{test_code}"
        return await self._llm_call(system, user, max_tokens=300)

    async def _gen_readme(self, claim: ClaimUnit, title: str, success_criteria_json: str) -> str:
        system = (
            "Write a clear README for this proof-of-concept scaffold. Include: what claim this tests, "
            "setup instructions (pip install -r requirements.txt), how to run (pytest test_harness.py -v), "
            "how to interpret results, and what the success criteria are. Be concise — max 40 lines."
        )
        user = (
            f"Claim ID: {claim.claim_id}\nClaim: {claim.text}\n\n"
            f"Paper: {title}\n\nSuccess criteria:\n{success_criteria_json}"
        )
        return await self._llm_call(system, user, max_tokens=800)

    # ── Helpers ────────────────────────────────────────────────────────────────

    async def _llm_call(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        response = await self._client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def _check_syntax(self, scaffold_files: dict) -> dict:
        errors = {}
        for fname in ("implementation.py", "test_harness.py"):
            code = scaffold_files.get(fname, "")
            try:
                ast.parse(code)
            except SyntaxError as exc:
                errors[fname] = str(exc)
        return errors

    async def _fix_syntax(self, code: str, filename: str, error: str) -> str:
        system = (
            "You are a Python syntax fixer. The code below has a syntax error. "
            "Fix it and return ONLY the corrected Python code with no explanation."
        )
        user = f"File: {filename}\nSyntax error: {error}\n\nCode:\n{code}"
        response = await self._client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=3000,
        )
        return response.choices[0].message.content or code
