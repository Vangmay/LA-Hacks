import ast
import json
import logging
import os
import re
from typing import Any

import httpx
from openai import AsyncOpenAI

from agents.base import AgentContext, AgentResult, BaseAgent
from config import settings
from models import ResearchAtom

logger = logging.getLogger(__name__)

_CODE_FENCE_RE = re.compile(
    r"^\s*```(?:python|py|text|txt|markdown|md)?\s*\n(?P<body>.*?)\n```\s*$",
    re.DOTALL | re.IGNORECASE,
)
_ANY_FENCED_BLOCK_RE = re.compile(
    r"```(?:python|py|text|txt|markdown|md)?\s*\n(?P<body>.*?)\n```",
    re.DOTALL | re.IGNORECASE,
)


class ScaffoldGeneratorAgent(BaseAgent):
    agent_id = "scaffold_generator"

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self._client = client or self._make_client()

    async def run(self, context: AgentContext) -> AgentResult:
        atom: ResearchAtom | None = context.atom or context.extra.get("atom")
        if atom is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"scaffold_files": {}},
                confidence=0.0,
                error="No atom provided in context.atom or context.extra['atom']",
            )

        poc_spec: dict = context.extra.get("poc_spec", {})
        paper_metadata: dict = context.extra.get("paper_metadata", {})

        try:
            scaffold_files = await self._generate_all_files(atom, poc_spec, paper_metadata)
        except Exception as exc:
            logger.error("ScaffoldGeneratorAgent failed for %s: %s", atom.atom_id, exc)
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output={"scaffold_files": {}},
                confidence=0.0,
                error=str(exc),
            )

        syntax_errors = self._check_syntax(scaffold_files)
        if syntax_errors:
            for fname, err in syntax_errors.items():
                try:
                    scaffold_files[fname] = await self._fix_syntax(
                        scaffold_files[fname], fname, err
                    )
                except Exception as exc:
                    logger.warning("Syntax fix LLM call failed for %s: %s", fname, exc)

        still_broken = self._check_syntax(scaffold_files)

        updated_spec = dict(poc_spec)
        updated_spec["scaffold_files"] = scaffold_files
        updated_spec["readme"] = scaffold_files.get("README.md", "")

        return AgentResult(
            agent_id=self.agent_id,
            status="inconclusive" if still_broken else "success",
            output={
                "scaffold_files": scaffold_files,
                "poc_spec": updated_spec,
                "syntax_errors": still_broken,
            },
            confidence=0.3 if still_broken else 0.8,
            error=(f"Syntax errors remain: {still_broken}" if still_broken else None),
        )

    # File generation

    async def _generate_all_files(
        self, atom: ResearchAtom, poc_spec: dict, paper_metadata: dict
    ) -> dict:
        title = paper_metadata.get("title", "Unknown Paper")
        abstract = paper_metadata.get("abstract", "")
        relevant_context = self._build_relevant_context(atom, paper_metadata)
        success_criteria_json = _json_dumps(poc_spec.get("success_criteria", []))
        failure_criteria_json = _json_dumps(poc_spec.get("failure_criteria", []))

        impl_py = await self._gen_implementation(
            atom,
            title,
            abstract,
            relevant_context,
            success_criteria_json,
            failure_criteria_json,
        )
        test_py = await self._gen_test_harness(atom, success_criteria_json, impl_py)
        logger_py = self._gen_results_logger()
        req_txt = await self._gen_requirements(impl_py, test_py)
        readme_md = await self._gen_readme(atom, title, success_criteria_json)

        return {
            "implementation.py": impl_py,
            "test_harness.py": test_py,
            "results_logger.py": logger_py,
            "requirements.txt": req_txt,
            "README.md": readme_md,
        }

    async def _gen_implementation(
        self,
        atom: ResearchAtom,
        title: str,
        abstract: str,
        relevant_context: str,
        success_criteria_json: str,
        failure_criteria_json: str,
    ) -> str:
        section_hint = atom.section_heading or "?"
        atom_header = _one_line(atom.text)[:180]
        atom_excerpt = atom.source_span.raw_excerpt.strip()
        system = (
            "You are implementing a research paper's method in Python, but the selected "
            "research atom is the implementation target. Generate clean, runnable code "
            "for that atom only.\n"
            "\n"
            "Non-negotiable scope rules:\n"
            "- The selected atom is authoritative. Do not implement a neighboring example, "
            "a famous method from the same paper, or the whole paper unless the atom itself "
            "requires it.\n"
            "- For algorithm atoms, implement the exact pseudocode/core estimator from the "
            "atom source excerpt: inputs, loop structure, sampling steps, objective calls, "
            "gradient computation, and return value. Use small toy callbacks when the paper "
            "uses abstract functions.\n"
            "- For empirical/result atoms, build the smallest callable surface needed for "
            "the test harness to measure the stated metric. Do not invent fake datasets or "
            "fake pass thresholds.\n"
            "- If some real artifact is missing (dataset, checkpoint, expensive training), "
            "make the missing dependency explicit through parameters, lightweight adapters, "
            "or clear TODO comments. The demo may use toy data, but comments must mark it as "
            "toy data.\n"
            "- Do not substitute a generic tutorial implementation. Example: for a VAE paper, "
            "if the selected atom is stochastic-gradient estimator pseudocode, implement the "
            "estimator loop, not a full VAE class.\n"
            "- Keep the code minimal and inspectable. Prefer functions over a large class "
            "unless the atom itself describes a class/module architecture.\n"
            "\n"
            "Output requirements:\n"
            f"- Add this exact top comment: # Implements {atom.atom_type.value} {atom.atom_id}: {atom_header}\n"
            "- Include inline comments that cite the atom section/source excerpt where useful.\n"
            "- Use only standard Python plus numpy, torch, sklearn, scipy, or pytest-adjacent "
            "utilities when appropriate.\n"
            "- Include a main() function that runs a minimal atom-specific demonstration.\n"
            "- Return ONLY raw Python code. No markdown fences. No prose before or after code."
        )
        user = (
            f"Selected atom ID: {atom.atom_id}\n"
            f"Selected atom type: {atom.atom_type.value}\n"
            f"Selected atom section: {section_hint}\n"
            f"Selected atom text: {atom.text}\n\n"
            f"Selected atom source excerpt:\n\"\"\"\n{atom_excerpt}\n\"\"\"\n\n"
            f"Paper: {title}\n"
            f"Abstract:\n{abstract[:900]}\n\n"
            f"Priority paper context:\n{relevant_context}\n\n"
            f"Success criteria JSON:\n{success_criteria_json}\n\n"
            f"Failure criteria JSON:\n{failure_criteria_json}"
        )
        return await self._llm_call(system, user, max_tokens=6000, strip_fences=True)

    async def _gen_test_harness(
        self, atom: ResearchAtom, success_criteria_json: str, impl_code: str
    ) -> str:
        system = (
            "Generate a pytest test file that verifies the selected atom's scaffold.\n"
            "Requirements:\n"
            "- Import from implementation.py.\n"
            "- Test the selected atom, not a broad paper-level method.\n"
            "- One test function per numeric success criterion when numeric criteria exist: "
            "def test_{metric_name}():\n"
            "- Use the exact numeric thresholds/tolerances provided. Do not invent arbitrary "
            "thresholds such as toy loss cutoffs.\n"
            "- If no numeric success criterion exists, write structural tests tied to the "
            "atom source excerpt, such as output shape, differentiability, gradient presence, "
            "sampling loop count, or deterministic behavior under a fixed seed.\n"
            "- Add a comment before each numeric assert: # Paper reports: {paper_reported_value}\n"
            "- Include a results dict with claim_id set to the atom ID and metric values that "
            "can be saved by results_logger.save_results.\n"
            "- Call save_results(results) from results_logger.py after metrics are collected.\n"
            "- Return ONLY raw Python code. No markdown fences. No prose."
        )
        user = (
            f"Selected atom ID: {atom.atom_id}\n"
            f"Selected atom type: {atom.atom_type.value}\n"
            f"Selected atom text: {atom.text}\n\n"
            f"Selected atom source excerpt:\n\"\"\"\n{atom.source_span.raw_excerpt.strip()}\n\"\"\"\n\n"
            f"Success criteria JSON:\n{success_criteria_json}\n\n"
            f"implementation.py content:\n{impl_code}"
        )
        return await self._llm_call(system, user, max_tokens=5000, strip_fences=True)

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
            "        \"claim_id\": results.get(\"claim_id\", results.get(\"atom_id\", \"\")),\n"
            "        \"timestamp\": datetime.now(timezone.utc).isoformat(),\n"
            "        \"metrics\": {\n"
            "            k: v for k, v in results.items()\n"
            "            if k not in {\"claim_id\", \"atom_id\"}\n"
            "        },\n"
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
            "Scan the provided Python files for import statements and generate a minimal "
            "requirements.txt. Include only third-party packages, not standard library "
            "modules. Use one package per line, no version pinning unless critical. "
            "Return ONLY the requirements.txt content. No markdown fences."
        )
        user = f"implementation.py:\n{impl_code}\n\ntest_harness.py:\n{test_code}"
        return await self._llm_call(system, user, max_tokens=500, strip_fences=True)

    async def _gen_readme(self, atom: ResearchAtom, title: str, success_criteria_json: str) -> str:
        system = (
            "Write a concise README for this proof-of-concept scaffold. It must say what "
            "selected atom this tests, what is implemented, what is intentionally left as "
            "toy/demo code or adapter input, setup instructions (pip install -r "
            "requirements.txt), how to run (pytest test_harness.py -v), how to interpret "
            "results, and the success criteria. Be concise: max 45 lines."
        )
        user = (
            f"Atom ID: {atom.atom_id}\n"
            f"Atom type: {atom.atom_type.value}\n"
            f"Section: {atom.section_heading or '?'}\n"
            f"Atom text: {atom.text}\n"
            f"Atom source excerpt:\n{atom.source_span.raw_excerpt.strip()}\n\n"
            f"Paper: {title}\n\nSuccess criteria:\n{success_criteria_json}"
        )
        return await self._llm_call(system, user, max_tokens=1200, strip_fences=False)

    # Helpers

    async def _llm_call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4000,
        *,
        strip_fences: bool = False,
    ) -> str:
        request_max_tokens = min(max_tokens, max(1, settings.poc_scaffold_max_output_tokens))
        kwargs: dict[str, Any] = {
            "model": self._model_name(),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": request_max_tokens,
        }
        reasoning_effort = settings.poc_scaffold_reasoning_effort.strip()
        if reasoning_effort:
            kwargs["extra_body"] = {"reasoning_effort": reasoning_effort}

        response = await self._client.chat.completions.create(**kwargs)
        content = (response.choices[0].message.content or "").strip()
        if strip_fences:
            return _strip_markdown_fences(content)
        return content

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
            "Fix it and return ONLY raw corrected Python code with no markdown fences "
            "and no explanation."
        )
        user = f"File: {filename}\nSyntax error: {error}\n\nCode:\n{code}"
        return await self._llm_call(system, user, max_tokens=6000, strip_fences=True)

    def _build_relevant_context(self, atom: ResearchAtom, paper_metadata: dict) -> str:
        sections = paper_metadata.get("sections", [])
        if not sections:
            return "(no section context available)"

        selected = _rank_sections_for_atom(atom, sections)
        blocks = []
        for section, priority in selected:
            title = section.get("title") or "Untitled section"
            content = section.get("content") or ""
            limit = 3500 if priority == "selected" else 1600
            blocks.append(f"## {title}\n{content[:limit]}")
        return "\n\n".join(blocks) or "(no relevant section context available)"

    def _make_client(self) -> AsyncOpenAI:
        kwargs: dict[str, Any] = {}
        base_url = (
            settings.poc_scaffold_base_url
            or settings.deepdive_thinking_base_url
            or settings.openai_base_url
        )
        if base_url:
            kwargs["base_url"] = base_url
        return AsyncOpenAI(
            api_key=_resolve_api_key(settings.poc_scaffold_api_key_env) or "missing-api-key",
            http_client=httpx.AsyncClient(
                timeout=settings.poc_scaffold_timeout_seconds,
                follow_redirects=True,
            ),
            **kwargs,
        )

    def _model_name(self) -> str:
        return (
            settings.poc_scaffold_model
            or settings.deepdive_thinking_model
            or settings.openai_model
        )


def _rank_sections_for_atom(atom: ResearchAtom, sections: list[dict]) -> list[tuple[dict, str]]:
    heading = (atom.section_heading or "").strip().lower()
    excerpt = _normalize_for_match(atom.source_span.raw_excerpt)
    excerpt_snippet = excerpt[:220]
    scored: list[tuple[int, int, dict, str]] = []

    for index, section in enumerate(sections):
        title = str(section.get("title") or "")
        content = str(section.get("content") or "")
        norm_title = title.strip().lower()
        norm_content = _normalize_for_match(content)

        score = 0
        priority = "supporting"
        if heading and (heading == norm_title or heading in norm_title or norm_title in heading):
            score += 200
            priority = "selected"
        if excerpt_snippet and excerpt_snippet in norm_content:
            score += 180
            priority = "selected"
        if index < 3:
            score += 30 - index
        if norm_title in {"abstract", "introduction", "method", "methods"}:
            score += 15

        scored.append((score, -index, section, priority))

    scored.sort(reverse=True, key=lambda item: (item[0], item[1]))
    chosen: list[tuple[dict, str]] = []
    seen_titles: set[str] = set()
    for score, _neg_index, section, priority in scored:
        if len(chosen) >= 5:
            break
        title_key = str(section.get("title") or "").strip().lower()
        if title_key in seen_titles:
            continue
        if score <= 0 and chosen:
            continue
        chosen.append((section, priority))
        seen_titles.add(title_key)

    return chosen


def _strip_markdown_fences(content: str) -> str:
    text = content.strip()
    whole = _CODE_FENCE_RE.match(text)
    if whole:
        return whole.group("body").strip() + "\n"
    blocks = _ANY_FENCED_BLOCK_RE.findall(text)
    if len(blocks) == 1:
        return blocks[0].strip() + "\n"
    return text + ("\n" if text else "")


def _json_dumps(value: Any) -> str:
    def default(obj: Any) -> Any:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return str(obj)

    return json.dumps(value, indent=2, default=default)


def _one_line(value: str) -> str:
    return " ".join(value.split())


def _normalize_for_match(value: str) -> str:
    return " ".join(value.lower().split())


def _settings_key_value(env_name: str) -> str:
    normalized = env_name.lower()
    if hasattr(settings, normalized):
        return str(getattr(settings, normalized) or "")
    return ""


def _resolve_api_key(env_name: str) -> str:
    return os.getenv(env_name) or _settings_key_value(env_name)
