from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from formalization.axle_client import AxleClientWrapper, get_axle_client, normalize_axle_error
from formalization.config import formalization_settings
from formalization.models import ToolCallRecord


AXLE_TOOL_NAMES = {
    "axle_check",
    "axle_verify_proof",
    "axle_repair_proofs",
    "axle_sorry2lemma",
    "axle_have2lemma",
    "axle_extract_decls",
    "axle_extract_theorems",
    "axle_disprove",
    "axle_merge",
    "axle_normalize",
}

META_TOOL_NAMES = {"record_artifact", "emit_verdict", "give_up"}

_AXLE_METHOD_BY_TOOL = {
    "axle_check": "check",
    "axle_verify_proof": "verify_proof",
    "axle_repair_proofs": "repair_proofs",
    "axle_sorry2lemma": "sorry2lemma",
    "axle_have2lemma": "have2lemma",
    "axle_extract_decls": "extract_decls",
    "axle_extract_theorems": "extract_theorems",
    "axle_disprove": "disprove",
    "axle_merge": "merge",
    "axle_normalize": "normalize",
}


@dataclass
class ToolDispatchResult:
    record: ToolCallRecord
    full_result: Optional[dict[str, Any]] = None
    meta: Optional[dict[str, Any]] = None


def _json_schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _tool(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": _json_schema(properties, required),
        },
    }


def build_tool_schemas() -> list[dict[str, Any]]:
    content_prop = {"type": "string", "description": "Full Lean 4 source file."}
    names_prop = {
        "type": "array",
        "items": {"type": "string"},
        "description": "Optional declaration names to target.",
    }
    indices_prop = {
        "type": "array",
        "items": {"type": "integer"},
        "description": "Optional declaration indices to target.",
    }
    bool_prop = {"type": "boolean"}
    return [
        _tool(
            "axle_check",
            "Check that a Lean 4 file compiles. Use after writing or editing a spec/proof.",
            {
                "content": content_prop,
                "mathlib_options": bool_prop,
                "ignore_imports": bool_prop,
            },
            ["content"],
        ),
        _tool(
            "axle_verify_proof",
            (
                "Verify that a candidate proof proves the formal statement without unpermitted "
                "sorries. formal_statement should be the full checked spec file with imports."
            ),
            {
                "formal_statement": {"type": "string"},
                "content": content_prop,
                "permitted_sorries": {"type": "array", "items": {"type": "string"}},
                "mathlib_options": bool_prop,
                "use_def_eq": bool_prop,
                "ignore_imports": bool_prop,
            },
            ["formal_statement", "content"],
        ),
        _tool(
            "axle_repair_proofs",
            "Ask AXLE to repair failing proofs after check/verify reports proof errors.",
            {
                "content": content_prop,
                "names": names_prop,
                "indices": indices_prop,
                "repairs": {"type": "array", "items": {"type": "string"}},
                "terminal_tactics": {"type": "array", "items": {"type": "string"}},
                "ignore_imports": bool_prop,
            },
            ["content"],
        ),
        _tool(
            "axle_sorry2lemma",
            "Extract sorry blocks or errors into helper lemma declarations.",
            {
                "content": content_prop,
                "names": names_prop,
                "indices": indices_prop,
                "extract_sorries": bool_prop,
                "extract_errors": bool_prop,
                "include_whole_context": bool_prop,
                "reconstruct_callsite": bool_prop,
                "verbosity": {"type": "integer"},
                "ignore_imports": bool_prop,
            },
            ["content"],
        ),
        _tool(
            "axle_have2lemma",
            "Extract large `have` blocks into helper lemma declarations.",
            {
                "content": content_prop,
                "names": names_prop,
                "indices": indices_prop,
                "include_have_body": bool_prop,
                "include_whole_context": bool_prop,
                "reconstruct_callsite": bool_prop,
                "verbosity": {"type": "integer"},
                "ignore_imports": bool_prop,
            },
            ["content"],
        ),
        _tool(
            "axle_extract_decls",
            "Extract declarations and dependencies from a Lean file.",
            {"content": content_prop, "ignore_imports": bool_prop},
            ["content"],
        ),
        _tool(
            "axle_extract_theorems",
            "Extract theorem declarations from a Lean file.",
            {"content": content_prop, "ignore_imports": bool_prop},
            ["content"],
        ),
        _tool(
            "axle_disprove",
            "Try to disprove theorem statements using counterexample search.",
            {
                "content": content_prop,
                "names": names_prop,
                "indices": indices_prop,
                "terminal_tactics": {"type": "array", "items": {"type": "string"}},
                "ignore_imports": bool_prop,
            },
            ["content"],
        ),
        _tool(
            "axle_merge",
            "Merge multiple Lean documents, resolving declaration conflicts where possible.",
            {
                "documents": {"type": "array", "items": {"type": "string"}},
                "use_def_eq": bool_prop,
                "include_alts_as_comments": bool_prop,
                "ignore_imports": bool_prop,
            },
            ["documents"],
        ),
        _tool(
            "axle_normalize",
            "Normalize Lean source by removing duplicates, sections, and other mechanical noise.",
            {
                "content": content_prop,
                "normalizations": {"type": "array", "items": {"type": "string"}},
                "failsafe": bool_prop,
                "ignore_imports": bool_prop,
            },
            ["content"],
        ),
        _tool(
            "record_artifact",
            "Record an important Lean artifact before or after AXLE checks.",
            {
                "kind": {"type": "string", "enum": ["spec", "proof", "helper_lemma"]},
                "lean_code": {"type": "string"},
                "axle_check_okay": {"type": ["boolean", "null"]},
                "axle_verify_okay": {"type": ["boolean", "null"]},
            },
            ["kind", "lean_code"],
        ),
        _tool(
            "emit_verdict",
            "Terminate the atom loop with an honest formalization verdict.",
            {
                "label": {
                    "type": "string",
                    "enum": [
                        "fully_verified",
                        "conditionally_verified",
                        "formalized_only",
                        "disproved",
                        "formalization_failed",
                        "not_a_theorem",
                        "gave_up",
                    ],
                },
                "rationale": {"type": "string"},
                "used_assumptions": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
            ["label", "rationale", "confidence"],
        ),
        _tool(
            "give_up",
            "Terminate when progress is blocked after serious repair attempts.",
            {"reason": {"type": "string"}},
            ["reason"],
        ),
    ]


class FormalizationToolbox:
    def __init__(self, client: Optional[AxleClientWrapper] = None) -> None:
        self.client = client or get_axle_client()
        self.schemas = build_tool_schemas()

    async def dispatch(
        self,
        name: str,
        args: dict[str, Any],
        *,
        call_id: Optional[str] = None,
    ) -> ToolDispatchResult:
        call_id = call_id or str(uuid.uuid4())
        started_at = datetime.utcnow()
        record = ToolCallRecord(
            call_id=call_id,
            tool_name=name,
            arguments=args,
            started_at=started_at,
        )

        try:
            if name in AXLE_TOOL_NAMES:
                full_result = await self._dispatch_axle(name, args)
                summary = summarize_result(full_result)
                record.completed_at = datetime.utcnow()
                record.status = "success"
                record.result_summary = summary
                return ToolDispatchResult(record=record, full_result=full_result)
            if name in META_TOOL_NAMES:
                summary = self._dispatch_meta(name, args)
                record.completed_at = datetime.utcnow()
                record.status = "success"
                record.result_summary = summary
                return ToolDispatchResult(record=record, full_result=summary, meta={"name": name, "args": args})
            raise ValueError(f"unknown tool: {name}")
        except Exception as exc:  # noqa: BLE001
            record.completed_at = datetime.utcnow()
            record.status = "error"
            record.error = json.dumps(normalize_axle_error(exc)) if name in AXLE_TOOL_NAMES else str(exc)
            record.result_summary = {"error": record.error}
            return ToolDispatchResult(record=record, full_result=record.result_summary)

    async def _dispatch_axle(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        method_name = _AXLE_METHOD_BY_TOOL[name]
        clean_args = dict(args)
        clean_args.pop("environment", None)
        clean_args.pop("timeout_seconds", None)
        clean_args["environment"] = formalization_settings.formalization_lean_environment
        clean_args["timeout_seconds"] = formalization_settings.axle_timeout_seconds
        if isinstance(clean_args.get("content"), str):
            clean_args["content"] = normalize_lean_imports(clean_args["content"])
        if isinstance(clean_args.get("formal_statement"), str):
            clean_args["formal_statement"] = normalize_lean_imports(clean_args["formal_statement"])
        if isinstance(clean_args.get("documents"), list):
            clean_args["documents"] = [
                normalize_lean_imports(document) if isinstance(document, str) else document
                for document in clean_args["documents"]
            ]
        if name in {"axle_check", "axle_verify_proof"}:
            clean_args.setdefault("mathlib_options", True)
        if name == "axle_verify_proof":
            clean_args.setdefault("use_def_eq", True)
            # Default to no permitted sorries — AXLE will return okay=false on
            # any sorry in the proof. Caller can override by passing the list.
            clean_args.setdefault("permitted_sorries", [])
            clean_args = _align_verify_imports(clean_args)
        if name == "axle_repair_proofs":
            clean_args.pop("names", None)
            clean_args.pop("indices", None)
            clean_args["repairs"] = [
                repair
                for repair in (clean_args.get("repairs") or [])
                if repair
                in {
                    "apply_terminal_tactics",
                    "insert_sorries",
                    "remove_extraneous_tactics",
                    "replace_unsafe_tactics",
                }
            ] or None
            clean_args.setdefault("terminal_tactics", ["grind"])
        if name in {"axle_sorry2lemma", "axle_have2lemma"}:
            clean_args.pop("names", None)
            clean_args.pop("indices", None)
        if name == "axle_normalize":
            allowed_normalizations = {
                "remove_sections",
                "expand_decl_names",
                "remove_duplicates",
                "split_open_in_commands",
                "normalize_module_comments",
                "normalize_doc_comments",
            }
            requested = clean_args.get("normalizations")
            if isinstance(requested, list):
                clean_args["normalizations"] = [
                    item for item in requested if item in allowed_normalizations
                ] or ["remove_sections", "remove_duplicates", "split_open_in_commands"]
            clean_args.setdefault(
                "normalizations",
                ["remove_sections", "remove_duplicates", "split_open_in_commands"],
            )
            clean_args.setdefault("failsafe", True)
        return await self.client.call(method_name, **clean_args)

    def _dispatch_meta(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "record_artifact":
            return {
                "kind": args.get("kind"),
                "lean_code_chars": len(args.get("lean_code") or ""),
                "axle_check_okay": args.get("axle_check_okay"),
                "axle_verify_okay": args.get("axle_verify_okay"),
            }
        if name == "emit_verdict":
            return {
                "label": args.get("label"),
                "confidence": args.get("confidence"),
                "assumptions": len(args.get("used_assumptions") or []),
            }
        if name == "give_up":
            return {"reason": args.get("reason")}
        raise ValueError(f"unknown meta tool: {name}")


def summarize_result(result: dict[str, Any], *, max_errors: int = 3) -> dict[str, Any]:
    lean_messages = result.get("lean_messages") or {}
    tool_messages = result.get("tool_messages") or {}
    failed = result.get("failed_declarations") or []
    documents = result.get("documents") or {}
    summary = {
        "okay": result.get("okay"),
        "content_chars": len(result.get("content") or ""),
        "failed_declarations": failed[:10] if isinstance(failed, list) else failed,
        "lean_errors": len(lean_messages.get("errors") or []),
        "lean_warnings": len(lean_messages.get("warnings") or []),
        "lean_infos": len(lean_messages.get("infos") or []),
        "tool_errors": len(tool_messages.get("errors") or []),
        "first_errors": (lean_messages.get("errors") or [])[:max_errors],
        "timings": result.get("timings") or {},
    }
    if documents:
        summary["documents"] = list(documents.keys())[:20]
    if "results" in result:
        summary["results"] = result.get("results")
        summary["disproved_theorems"] = result.get("disproved_theorems") or []
    if "lemma_names" in result:
        summary["lemma_names"] = result.get("lemma_names") or []
    return summary


_IMPORT_RE = re.compile(r"^\s*import\s+\S+\s*$", re.MULTILINE)


def normalize_lean_imports(content: str) -> str:
    """Prefer a single `import Mathlib` header for AXLE's mathlib environment."""
    lines = content.splitlines()
    import_lines: list[str] = []
    body_start = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("import "):
            import_lines.append(stripped)
            body_start = index + 1
            continue
        body_start = index
        break

    if not import_lines:
        return content
    if any(line == "import Mathlib" for line in import_lines):
        return content
    if any(line.startswith("import Mathlib") for line in import_lines):
        body = "\n".join(lines[body_start:]).lstrip("\n")
        return "import Mathlib\n\n" + body
    return content


def _align_verify_imports(args: dict[str, Any]) -> dict[str, Any]:
    content = args.get("content")
    formal_statement = args.get("formal_statement")
    if not isinstance(content, str) or not isinstance(formal_statement, str):
        return args
    content_imports = _IMPORT_RE.findall(content)
    statement_imports = _IMPORT_RE.findall(formal_statement)
    if content_imports and not statement_imports:
        args["formal_statement"] = "\n".join(content_imports) + "\n\n" + formal_statement.lstrip()
    elif content_imports != statement_imports:
        args.setdefault("ignore_imports", True)
    return args
