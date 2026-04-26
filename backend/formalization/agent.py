from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import httpx
from openai import AsyncOpenAI

from config import settings
from formalization.config import formalization_settings
from formalization.event_bus import formalization_event_bus
from formalization.events import FormalizationEvent, FormalizationEventType
from formalization.models import (
    FormalizationArtifact,
    FormalizationLabel,
    FormalizationStatus,
    ToolCallRecord,
)
from formalization.outputs import write_artifact
from formalization.prompts import SYSTEM_PROMPT, build_user_prompt
from formalization.store import formalization_store
from formalization.toolbox import AXLE_TOOL_NAMES, FormalizationToolbox, ToolDispatchResult

logger = logging.getLogger(__name__)


@dataclass
class _LoopState:
    latest_artifact_id: Optional[str] = None
    latest_artifact_kind: Optional[str] = None
    latest_spec: Optional[str] = None
    latest_checked_spec: Optional[str] = None
    latest_proof: Optional[str] = None
    spec_check_ok: bool = False
    proof_check_ok: bool = False
    verify_ok: bool = False
    check_attempts: int = 0
    verify_attempts: int = 0
    last_feedback: str = ""


class FormalizationAgent:
    def __init__(
        self,
        *,
        client: Optional[Any] = None,
        toolbox: Optional[FormalizationToolbox] = None,
    ) -> None:
        self._client = client
        self.toolbox = toolbox or FormalizationToolbox()
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0

    def _get_client(self) -> Any:
        if self._client is None:
            kwargs: dict[str, Any] = {}
            if formalization_settings.formalization_base_url:
                kwargs["base_url"] = formalization_settings.formalization_base_url
            self._client = AsyncOpenAI(
                api_key=_resolve_api_key(formalization_settings.formalization_api_key_env),
                http_client=httpx.AsyncClient(
                    timeout=formalization_settings.formalization_model_timeout_seconds,
                    follow_redirects=True,
                ),
                **kwargs,
            )
        return self._client

    async def run_atom(self, *, run_id: str, atom_id: str, context: dict[str, Any]) -> None:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(context)},
        ]
        formalization_store.append_llm_message(run_id, atom_id, messages[0])
        formalization_store.append_llm_message(run_id, atom_id, messages[1])

        axle_calls = 0
        max_iterations = max(1, formalization_settings.formalization_max_iterations_per_atom)
        max_axle_calls = max(1, formalization_settings.formalization_max_axle_calls_per_atom)
        loop_state = _LoopState()

        for iteration in range(1, max_iterations + 1):
            formalization_store.set_atom_status(run_id, atom_id, FormalizationStatus.LLM_THINKING)
            assistant_message = await self._complete(run_id, atom_id, messages, loop_state, iteration)
            if not assistant_message.get("tool_calls"):
                assistant_message.pop("tool_calls", None)
            messages.append(assistant_message)
            formalization_store.append_llm_message(run_id, atom_id, assistant_message)

            tool_calls = assistant_message.get("tool_calls") or []
            if not tool_calls:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "You must call one tool next. Use an AXLE tool, record_artifact, "
                            "emit_verdict, or give_up."
                        ),
                    }
                )
                continue

            pending_feedback: list[str] = []
            for tool_call in tool_calls:
                name, args, call_id = _parse_tool_call(tool_call)
                args = _normalize_agent_tool_args(name, args, loop_state)
                if name in AXLE_TOOL_NAMES:
                    axle_calls += 1
                    if axle_calls > max_axle_calls:
                        await self._finalize_on_guardrail(run_id, atom_id, loop_state, "axle_call")
                        return

                formalization_store.set_atom_status(run_id, atom_id, FormalizationStatus.AXLE_RUNNING)
                pending = ToolCallRecord(
                    call_id=call_id,
                    tool_name=name,
                    arguments=args,
                    started_at=datetime.utcnow(),
                )
                formalization_store.append_tool_call(run_id, atom_id, pending)
                await _publish(
                    run_id,
                    FormalizationEventType.TOOL_CALL_STARTED,
                    atom_id=atom_id,
                    payload=_tool_event_payload(pending),
                )

                result = await self.toolbox.dispatch(name, args, call_id=call_id)
                formalization_store.update_tool_call(run_id, atom_id, result.record)
                await _publish_tool_result(run_id, atom_id, result)
                messages.append(_tool_message(result))

                if result.meta:
                    done, feedback = await self._handle_meta_tool(
                        run_id=run_id,
                        atom_id=atom_id,
                        iteration=iteration,
                        result=result,
                        loop_state=loop_state,
                    )
                    if feedback:
                        pending_feedback.append(feedback)
                    if done:
                        return
                elif name in AXLE_TOOL_NAMES:
                    feedback = await self._handle_axle_feedback(
                        run_id=run_id,
                        atom_id=atom_id,
                        result=result,
                        loop_state=loop_state,
                    )
                    if feedback:
                        pending_feedback.append(feedback)

            if pending_feedback:
                feedback_text = "\n\n".join(pending_feedback)
                loop_state.last_feedback = feedback_text
                _append_user_feedback(messages, run_id, atom_id, feedback_text)
            messages = _compact_messages(messages, loop_state)

            formalization_store.set_atom_status(run_id, atom_id, FormalizationStatus.LLM_THINKING)

        await self._finalize_on_guardrail(run_id, atom_id, loop_state, "iteration")

    async def _complete(
        self,
        run_id: str,
        atom_id: str,
        messages: list[dict[str, Any]],
        loop_state: _LoopState,
        iteration: int,
    ) -> dict[str, Any]:
        max_continuations = max(0, formalization_settings.formalization_max_continuations)
        for cont_round in range(max_continuations + 1):
            message, finish_reason = await self._invoke_model_once(
                run_id, atom_id, messages, loop_state, iteration
            )
            # If the model emitted a tool call, accept it and let the outer loop dispatch.
            # Continuation only fires when the turn was truncated AND no tool call landed.
            if message.get("tool_calls"):
                return message
            truncated = finish_reason in {"length", "char_budget"}
            if not truncated or cont_round == max_continuations:
                return message
            messages.append(message)
            formalization_store.append_llm_message(run_id, atom_id, message)
            char_budget = formalization_settings.formalization_max_output_chars
            continue_msg = {
                "role": "user",
                "content": (
                    f"Your previous response was truncated (finish_reason={finish_reason}, "
                    f"~{char_budget}-char soft cap). Continue from where you stopped — do not "
                    "restart. End this turn with exactly one tool call: an AXLE tool, "
                    "record_artifact, or emit_verdict."
                ),
            }
            messages.append(continue_msg)
            formalization_store.append_llm_message(run_id, atom_id, continue_msg)
            await _publish(
                run_id,
                FormalizationEventType.LLM_THOUGHT,
                atom_id=atom_id,
                payload={
                    "delta": (
                        f"\n[continuation {cont_round + 1}/{max_continuations}: prior turn "
                        f"truncated ({finish_reason}); asking model to continue and commit to "
                        "a tool call]\n"
                    ),
                    "iteration": iteration,
                    "model_name": formalization_settings.formalization_model,
                },
            )
        return message

    async def _invoke_model_once(
        self,
        run_id: str,
        atom_id: str,
        messages: list[dict[str, Any]],
        loop_state: _LoopState,
        iteration: int,
    ) -> tuple[dict[str, Any], Optional[str]]:
        max_attempts = max(1, formalization_settings.formalization_model_max_retries)
        response: Any = None
        for attempt in range(1, max_attempts + 1):
            try:
                formalization_store.increment_llm_call_count(run_id, atom_id)
                await self._pace_model()
                response = await self._get_client().chat.completions.create(
                    **_chat_kwargs(messages=messages, tools=self.toolbox.schemas)
                )
                break
            except Exception as exc:  # noqa: BLE001
                retryable = exc.__class__.__name__ in {"RateLimitError", "APITimeoutError", "APIConnectionError"}
                if not retryable or attempt >= max_attempts:
                    raise
                if "Request too large" in str(exc):
                    messages[:] = _compact_messages(messages, loop_state, force=True)
                    continue
                delay = _rate_limit_delay_seconds(exc, attempt)
                await _publish(
                    run_id,
                    FormalizationEventType.LLM_THOUGHT,
                    atom_id=atom_id,
                    payload={
                        "delta": f"Formalization model rate limited; retrying in {delay:.1f}s (attempt {attempt}/{max_attempts}).",
                        "iteration": iteration,
                        "model_name": formalization_settings.formalization_model,
                    },
                )
                await asyncio.sleep(delay)
        if hasattr(response, "__aiter__"):
            return await self._collect_stream(run_id, atom_id, response, iteration)
        return _message_from_response(response)

    async def _pace_model(self) -> None:
        interval = max(0.0, formalization_settings.formalization_model_min_interval_seconds)
        if interval <= 0:
            return
        async with self._request_lock:
            elapsed = time.monotonic() - self._last_request_at
            wait = interval - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request_at = time.monotonic()

    async def _collect_stream(
        self, run_id: str, atom_id: str, stream: Any, iteration: int
    ) -> tuple[dict[str, Any], Optional[str]]:
        content_parts: list[str] = []
        tool_parts: dict[int, dict[str, Any]] = {}
        finish_reason: Optional[str] = None
        char_budget = max(0, formalization_settings.formalization_max_output_chars)
        content_chars = 0

        async for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            chunk_finish = getattr(choices[0], "finish_reason", None)
            if chunk_finish is not None:
                finish_reason = chunk_finish
            delta = getattr(choices[0], "delta", None)
            if delta is None:
                continue
            content = getattr(delta, "content", None)
            if content:
                content_parts.append(content)
                content_chars += len(content)
                await _publish(
                    run_id,
                    FormalizationEventType.LLM_THOUGHT,
                    atom_id=atom_id,
                    payload={
                        "delta": content,
                        "iteration": iteration,
                        "model_name": formalization_settings.formalization_model,
                    },
                )
            for tool_delta in getattr(delta, "tool_calls", None) or []:
                index = getattr(tool_delta, "index", 0)
                bucket = tool_parts.setdefault(
                    index,
                    {"id": None, "type": "function", "function": {"name": "", "arguments": ""}},
                )
                if getattr(tool_delta, "id", None):
                    bucket["id"] = tool_delta.id
                function = getattr(tool_delta, "function", None)
                if function is not None:
                    if getattr(function, "name", None):
                        bucket["function"]["name"] += function.name
                    if getattr(function, "arguments", None):
                        bucket["function"]["arguments"] += function.arguments
            # Soft char budget: if the model is monologuing without committing to a tool call,
            # cut the stream early and surface a synthetic "char_budget" finish_reason so the
            # caller can re-prompt for continuation. Never cut mid-tool-call.
            if (
                char_budget
                and not tool_parts
                and content_chars >= char_budget
                and finish_reason is None
            ):
                finish_reason = "char_budget"
                close = getattr(stream, "close", None) or getattr(stream, "aclose", None)
                if callable(close):
                    try:
                        await close()
                    except Exception:  # noqa: BLE001
                        pass
                break

        content = "".join(content_parts)
        tool_calls = [value for _, value in sorted(tool_parts.items()) if value["function"]["name"]]
        for index, tool_call in enumerate(tool_calls):
            tool_call["id"] = tool_call.get("id") or f"call_{uuid.uuid4().hex[:12]}_{index}"
        message = {"role": "assistant", "content": content or None}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return message, finish_reason

    async def _handle_meta_tool(
        self,
        *,
        run_id: str,
        atom_id: str,
        iteration: int,
        result: ToolDispatchResult,
        loop_state: _LoopState,
    ) -> tuple[bool, Optional[str]]:
        meta = result.meta or {}
        name = meta.get("name")
        args = meta.get("args") or {}
        if name == "record_artifact":
            kind = args["kind"]
            lean_code = args["lean_code"]
            artifact = FormalizationArtifact(
                artifact_id=str(uuid.uuid4()),
                kind=kind,
                lean_code=lean_code,
                axle_check_okay=args.get("axle_check_okay"),
                axle_verify_okay=args.get("axle_verify_okay"),
                iteration=iteration,
            )
            artifact.path = write_artifact(run_id, atom_id, artifact)
            formalization_store.add_artifact(run_id, atom_id, artifact)
            loop_state.latest_artifact_id = artifact.artifact_id
            loop_state.latest_artifact_kind = artifact.kind
            if kind == "spec":
                loop_state.latest_spec = lean_code
                loop_state.spec_check_ok = False
                loop_state.verify_ok = False
            elif kind == "proof":
                loop_state.latest_proof = lean_code
                loop_state.proof_check_ok = False
                loop_state.verify_ok = False
            await _publish(
                run_id,
                FormalizationEventType.ARTIFACT_RECORDED,
                atom_id=atom_id,
                payload={
                    "artifact_id": artifact.artifact_id,
                    "kind": artifact.kind,
                    "iteration": artifact.iteration,
                    "path": artifact.path,
                    "lean_code_chars": len(artifact.lean_code),
                    "lean_code": _trim_text(artifact.lean_code, 24000),
                    "lean_code_truncated": len(artifact.lean_code) > 24000,
                    "axle_check_okay": artifact.axle_check_okay,
                    "axle_verify_okay": artifact.axle_verify_okay,
                },
            )
            if kind == "spec":
                return False, (
                    "Recorded a spec artifact. Next, call axle_check on this exact Lean file. "
                    "Do not attempt proof generation or emit a verdict until axle_check returns okay=true."
                )
            if kind == "proof":
                return False, (
                    "Recorded a proof artifact. Next, call axle_check on the proof file, then "
                    "axle_verify_proof using the latest checked spec as formal_statement."
                )
            return False, "Recorded helper lemma. Check or merge it with AXLE before relying on it."
        if name == "emit_verdict":
            label = FormalizationLabel(args["label"])
            gate = _verdict_gate(label, loop_state)
            if gate:
                return False, gate
            await self._finalize(
                run_id,
                atom_id,
                label=label,
                rationale=args.get("rationale") or "",
                used_assumptions=args.get("used_assumptions") or [],
                confidence=float(args.get("confidence") or 0.0),
            )
            return True, None
        if name == "give_up":
            return False, (
                "Blocked give_up. Continue the repair loop. Use the latest AXLE feedback, revise "
                "the Lean file, record_artifact again, and run axle_check/axle_verify_proof again. "
                "Only the server guardrail can stop this before a compiled spec."
            )
        return False, None

    async def _handle_axle_feedback(
        self,
        *,
        run_id: str,
        atom_id: str,
        result: ToolDispatchResult,
        loop_state: _LoopState,
    ) -> str:
        tool_name = result.record.tool_name
        summary = result.record.result_summary or {}
        okay = result.record.status == "success" and summary.get("okay") is True

        if tool_name == "axle_check":
            loop_state.check_attempts += 1
            cheat_msg = _scan_lean_for_cheats(loop_state.latest_spec) if loop_state.latest_artifact_kind == "spec" else _scan_lean_for_cheats(loop_state.latest_proof)
            spec_okay = okay and cheat_msg is None
            if loop_state.latest_artifact_id:
                formalization_store.update_artifact_status(
                    run_id,
                    atom_id,
                    loop_state.latest_artifact_id,
                    axle_check_okay=spec_okay,
                )
                await _publish_artifact_update(
                    run_id,
                    atom_id,
                    artifact_id=loop_state.latest_artifact_id,
                    axle_check_okay=spec_okay,
                )
            if loop_state.latest_artifact_kind == "spec":
                loop_state.spec_check_ok = spec_okay
                if spec_okay:
                    loop_state.latest_checked_spec = loop_state.latest_spec
                    return (
                        "AXLE check returned okay=true for the spec, and the spec is free of "
                        "sorry/axiom-of-conclusion cheats. Now write a proof artifact and run "
                        "axle_verify_proof against this checked spec."
                    )
                if cheat_msg:
                    return (
                        f"Spec rejected by anti-cheat scanner: {cheat_msg} "
                        "AXLE check returned okay=true (sorries/axioms compile in Lean), but a "
                        "spec with sorry or an axiom that *is* the atom's conclusion is not a "
                        "real formalization. Rewrite the spec without these patterns and "
                        "call axle_check again."
                    )
                return _repair_instruction(
                    "AXLE check failed for the spec. Revise the Lean spec, record_artifact(kind='spec'), "
                    "and call axle_check again. Do not emit formalized_only until okay=true.",
                    result,
                )
            if loop_state.latest_artifact_kind == "proof":
                loop_state.proof_check_ok = spec_okay
                if spec_okay:
                    return (
                        "AXLE check returned okay=true for the proof file. Now call axle_verify_proof "
                        "with formal_statement equal to the latest checked spec and content equal to this proof."
                    )
                if cheat_msg:
                    return (
                        f"Proof file rejected by anti-cheat scanner: {cheat_msg} "
                        "Rewrite without these patterns and call axle_check again."
                    )
                return _repair_instruction(
                    "AXLE check failed for the proof file. Revise the proof, record_artifact(kind='proof'), "
                    "and call axle_check again before verify_proof.",
                    result,
                )

        if tool_name == "axle_verify_proof":
            loop_state.verify_attempts += 1
            cheat_msg = _scan_lean_for_cheats(loop_state.latest_proof) or _scan_lean_for_cheats(loop_state.latest_checked_spec)
            verify_okay = okay and cheat_msg is None
            loop_state.verify_ok = verify_okay
            if loop_state.latest_artifact_id:
                formalization_store.update_artifact_status(
                    run_id,
                    atom_id,
                    loop_state.latest_artifact_id,
                    axle_verify_okay=verify_okay,
                )
                await _publish_artifact_update(
                    run_id,
                    atom_id,
                    artifact_id=loop_state.latest_artifact_id,
                    axle_verify_okay=verify_okay,
                )
            if verify_okay:
                return (
                    "AXLE verify_proof returned okay=true with permitted_sorries=[] and the spec/proof "
                    "passed the anti-cheat scanner. You may emit fully_verified."
                )
            if cheat_msg:
                return (
                    f"verify_proof returned okay=true but the spec or proof was rejected by the "
                    f"anti-cheat scanner: {cheat_msg} Rewrite without these patterns, then re-run "
                    "axle_check on the spec and axle_verify_proof on the new proof."
                )
            return _repair_instruction(
                "AXLE verify_proof failed (with permitted_sorries=[] meaning sorries are not allowed). "
                "Use the errors to revise/decompose the proof. Try repair_proofs, "
                "sorry2lemma/have2lemma, record the revised proof, then run axle_check and axle_verify_proof again.",
                result,
            )

        if result.record.status == "error":
            return _repair_instruction(
                f"{tool_name} returned an error. Correct the tool arguments or Lean code and try again.",
                result,
            )
        return ""

    async def _finalize_on_guardrail(
        self,
        run_id: str,
        atom_id: str,
        loop_state: _LoopState,
        guardrail_name: str,
    ) -> None:
        if loop_state.verify_ok:
            await self._finalize(
                run_id,
                atom_id,
                label=FormalizationLabel.FULLY_VERIFIED,
                rationale=f"Reached the {guardrail_name} guardrail after AXLE verify_proof returned okay=true.",
                confidence=0.8,
            )
            return
        if loop_state.spec_check_ok:
            await self._finalize(
                run_id,
                atom_id,
                label=FormalizationLabel.FORMALIZED_ONLY,
                rationale=f"Reached the {guardrail_name} guardrail after AXLE compiled the spec but before proof verification succeeded.",
                confidence=0.45,
            )
            return
        await self._finalize(
            run_id,
            atom_id,
            label=FormalizationLabel.FORMALIZATION_FAILED,
            rationale=f"Reached the {guardrail_name} guardrail before AXLE compiled a faithful spec.",
            confidence=0.1,
            error=f"{guardrail_name}_guardrail_reached_without_compiled_spec",
        )

    async def _finalize(
        self,
        run_id: str,
        atom_id: str,
        *,
        label: FormalizationLabel,
        rationale: str,
        used_assumptions: Optional[list[str]] = None,
        confidence: float,
        error: Optional[str] = None,
    ) -> None:
        formalization_store.finalize_atom(
            run_id,
            atom_id,
            label=label,
            rationale=rationale,
            used_assumptions=used_assumptions,
            confidence=confidence,
            error=error,
        )
        await _publish(
            run_id,
            FormalizationEventType.ATOM_VERDICT,
            atom_id=atom_id,
            payload={
                "label": label.value,
                "rationale": rationale,
                "used_assumptions": used_assumptions or [],
                "confidence": confidence,
                "error": error,
            },
        )


def _append_user_feedback(
    messages: list[dict[str, Any]],
    run_id: str,
    atom_id: str,
    content: str,
) -> None:
    message = {"role": "user", "content": content}
    messages.append(message)
    formalization_store.append_llm_message(run_id, atom_id, message)


def _settings_key_value(env_name: str) -> str:
    normalized = env_name.lower()
    if hasattr(settings, normalized):
        return str(getattr(settings, normalized) or "")
    return ""


def _resolve_api_key(env_name: str) -> str:
    value = os.getenv(env_name) or _settings_key_value(env_name)
    if not value:
        raise RuntimeError(f"missing formalization model API key for {env_name}")
    return value


def _chat_kwargs(*, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": formalization_settings.formalization_model or settings.openai_model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "stream": True,
        "max_tokens": max(512, formalization_settings.formalization_max_output_tokens),
    }
    if formalization_settings.formalization_reasoning_effort:
        kwargs["extra_body"] = {
            "reasoning_effort": formalization_settings.formalization_reasoning_effort,
        }
    return kwargs


def _normalize_agent_tool_args(name: str, args: dict[str, Any], loop_state: _LoopState) -> dict[str, Any]:
    clean = dict(args)
    if name == "axle_verify_proof":
        if loop_state.latest_spec and not _looks_like_lean_decl(clean.get("formal_statement")):
            clean["formal_statement"] = loop_state.latest_checked_spec or loop_state.latest_spec
        if loop_state.latest_proof and not clean.get("content"):
            clean["content"] = loop_state.latest_proof
    if name in {"axle_repair_proofs", "axle_sorry2lemma", "axle_have2lemma"}:
        clean.pop("names", None)
        clean.pop("indices", None)
    return clean


def _looks_like_lean_decl(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return any(token in value for token in ("theorem ", "lemma ", "def "))


def _compact_messages(
    messages: list[dict[str, Any]],
    loop_state: _LoopState,
    *,
    force: bool = False,
    max_chars: int = 42000,
) -> list[dict[str, Any]]:
    if not force and sum(len(json.dumps(message, default=str)) for message in messages) <= max_chars:
        return messages
    if len(messages) < 2:
        return messages

    summary = [
        "The previous tool transcript was compacted to stay within model token limits.",
        "Continue the same formalization loop. Do not restart from scratch.",
        f"Spec AXLE check ok: {loop_state.spec_check_ok}",
        f"Proof AXLE check ok: {loop_state.proof_check_ok}",
        f"AXLE verify_proof ok: {loop_state.verify_ok}",
        f"AXLE check attempts: {loop_state.check_attempts}",
        f"AXLE verify attempts: {loop_state.verify_attempts}",
    ]
    if loop_state.latest_spec:
        summary.extend(
            [
                "Latest spec Lean:",
                "```lean",
                _trim_text(loop_state.latest_spec, 9000),
                "```",
            ]
        )
    if loop_state.latest_proof:
        summary.extend(
            [
                "Latest proof Lean:",
                "```lean",
                _trim_text(loop_state.latest_proof, 9000),
                "```",
            ]
        )
    if loop_state.last_feedback:
        summary.extend(
            [
                "Most recent AXLE/agent feedback:",
                _trim_text(loop_state.last_feedback, 9000),
            ]
        )
    return [messages[0], messages[1], {"role": "user", "content": "\n".join(summary)}]


def _verdict_gate(label: FormalizationLabel, loop_state: _LoopState) -> Optional[str]:
    if label == FormalizationLabel.NOT_A_THEOREM:
        return None
    if label == FormalizationLabel.FULLY_VERIFIED and not loop_state.verify_ok:
        return (
            "Blocked verdict: fully_verified requires AXLE verify_proof okay=true. "
            "Continue repairing and rerun axle_verify_proof."
        )
    if label == FormalizationLabel.CONDITIONALLY_VERIFIED and not loop_state.spec_check_ok:
        return (
            "Blocked verdict: conditionally_verified requires at least a compiling spec. "
            "Revise the spec and call axle_check until okay=true."
        )
    if label in {FormalizationLabel.FORMALIZATION_FAILED, FormalizationLabel.GAVE_UP}:
        return (
            "Blocked verdict: do not end the loop with formalization_failed/gave_up. Continue "
            "using AXLE feedback to repair the Lean file. Only the server guardrail can stop "
            "before a compiled spec."
        )
    if label == FormalizationLabel.FORMALIZED_ONLY and not loop_state.spec_check_ok:
        return (
            "Blocked verdict: formalized_only requires AXLE check okay=true for the spec. "
            "Recorded Lean text is not enough. Revise the spec and call axle_check again."
        )
    return None


def _repair_instruction(prefix: str, result: ToolDispatchResult) -> str:
    return "\n".join(
        [
            prefix,
            "AXLE feedback:",
            _compact_tool_feedback(result),
        ]
    )


def _compact_tool_feedback(result: ToolDispatchResult, max_chars: int = 2500) -> str:
    payload = {
        "tool_name": result.record.tool_name,
        "status": result.record.status,
        "summary": result.record.result_summary,
        "error": result.record.error,
        "full_result": _trim_value(result.full_result, max_chars=max_chars),
    }
    text = json.dumps(payload, default=str, indent=2)
    if len(text) > max_chars:
        return text[:max_chars] + f"\n... ({len(text)} chars total)"
    return text


def _trim_value(value: Any, *, max_chars: int) -> Any:
    if isinstance(value, str):
        return value if len(value) <= max_chars else value[:max_chars] + f"... ({len(value)} chars total)"
    if isinstance(value, list):
        return [_trim_value(item, max_chars=max_chars) for item in value[:20]]
    if isinstance(value, dict):
        return {key: _trim_value(val, max_chars=max_chars) for key, val in list(value.items())[:40]}
    return value


def _trim_text(value: str, max_chars: int) -> str:
    return value if len(value) <= max_chars else value[:max_chars] + f"\n... ({len(value)} chars total)"


def _parse_tool_call(tool_call: Any) -> tuple[str, dict[str, Any], str]:
    if isinstance(tool_call, dict):
        call_id = tool_call.get("id") or f"call_{uuid.uuid4().hex[:12]}"
        function = tool_call.get("function") or {}
        name = function.get("name") or tool_call.get("name") or ""
        raw_args = function.get("arguments") or tool_call.get("arguments") or "{}"
    else:
        call_id = getattr(tool_call, "id", None) or f"call_{uuid.uuid4().hex[:12]}"
        function = getattr(tool_call, "function", None)
        name = getattr(function, "name", "") if function is not None else ""
        raw_args = getattr(function, "arguments", "{}") if function is not None else "{}"
    try:
        args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
    except (json.JSONDecodeError, TypeError, ValueError):
        args = {}
    return name, args, call_id


def _message_from_response(response: Any) -> tuple[dict[str, Any], Optional[str]]:
    choice = response.choices[0]
    raw_message = choice.message
    finish_reason = getattr(choice, "finish_reason", None)
    content = getattr(raw_message, "content", None)
    tool_calls = []
    for tool_call in getattr(raw_message, "tool_calls", None) or []:
        name, args, call_id = _parse_tool_call(tool_call)
        tool_calls.append(
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)},
            }
        )
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return message, finish_reason


def _tool_message(result: ToolDispatchResult) -> dict[str, Any]:
    payload = {
        "status": result.record.status,
        "result_summary": result.record.result_summary,
        "error": result.record.error,
        "full_result": _trim_value(result.full_result, max_chars=1500),
    }
    return {
        "role": "tool",
        "tool_call_id": result.record.call_id,
        "content": json.dumps(payload),
    }


async def _publish_tool_result(run_id: str, atom_id: str, result: ToolDispatchResult) -> None:
    await _publish(
        run_id,
        FormalizationEventType.TOOL_CALL_COMPLETE,
        atom_id=atom_id,
        payload=_tool_event_payload(result.record),
    )
    if result.record.tool_name == "axle_check":
        await _publish(
            run_id,
            FormalizationEventType.AXLE_CHECK_RESULT,
            atom_id=atom_id,
            payload=result.record.result_summary or {},
        )
    if result.record.tool_name == "axle_verify_proof":
        await _publish(
            run_id,
            FormalizationEventType.AXLE_VERIFY_RESULT,
            atom_id=atom_id,
            payload=result.record.result_summary or {},
        )


async def _publish_artifact_update(
    run_id: str,
    atom_id: str,
    *,
    artifact_id: str,
    axle_check_okay: Optional[bool] = None,
    axle_verify_okay: Optional[bool] = None,
) -> None:
    payload: dict[str, Any] = {"artifact_id": artifact_id}
    if axle_check_okay is not None:
        payload["axle_check_okay"] = axle_check_okay
    if axle_verify_okay is not None:
        payload["axle_verify_okay"] = axle_verify_okay
    await _publish(
        run_id,
        FormalizationEventType.ARTIFACT_UPDATED,
        atom_id=atom_id,
        payload=payload,
    )


def _tool_event_payload(record: ToolCallRecord) -> dict[str, Any]:
    duration_ms = None
    if record.completed_at:
        duration_ms = round((record.completed_at - record.started_at).total_seconds() * 1000)
    return {
        "call_id": record.call_id,
        "tool_name": record.tool_name,
        "arguments": _summarize_arguments(record.arguments),
        "started_at": record.started_at.isoformat(),
        "completed_at": record.completed_at.isoformat() if record.completed_at else None,
        "duration_ms": duration_ms,
        "status": record.status,
        "result_summary": record.result_summary,
        "error": record.error,
    }


def _summarize_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    summarized: dict[str, Any] = {}
    for key, value in arguments.items():
        if isinstance(value, str) and len(value) > 600:
            summarized[key] = value[:600] + f"... ({len(value)} chars)"
        else:
            summarized[key] = value
    return summarized


async def _publish(
    run_id: str,
    event_type: FormalizationEventType,
    *,
    atom_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> None:
    try:
        await formalization_event_bus.publish(
            run_id,
            FormalizationEvent(
                event_id=str(uuid.uuid4()),
                run_id=run_id,
                event_type=event_type,
                atom_id=atom_id,
                payload=payload or {},
                timestamp=datetime.utcnow(),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("formalization event publish failed: %s", exc)


_LEAN_LINE_COMMENT_RE = re.compile(r"--.*$", re.MULTILINE)
_LEAN_BLOCK_COMMENT_RE = re.compile(r"/-.*?-/", re.DOTALL)
_LEAN_DOC_COMMENT_RE = re.compile(r"/--.*?-/", re.DOTALL)
_LEAN_AXIOM_RE = re.compile(r"^\s*axiom\s+(\w+)", re.MULTILINE)
_LEAN_SORRY_RE = re.compile(r"\bsorry\b")
_LEAN_TRIVIAL_TAUTOLOGY_RE = re.compile(
    r":\s*\(?\s*(True|0\s*=\s*0|∃\s*\w+\s*:\s*Type\s*,\s*True|∃\s*\w+\s*:\s*Sort\b.*?,\s*True)\s*\)?",
    re.DOTALL,
)
_LEAN_DEF_FALSE_RE = re.compile(r"^\s*def\s+(\w+).*:=\s*False\b", re.MULTILINE)


def _strip_lean_comments(text: str) -> str:
    text = _LEAN_DOC_COMMENT_RE.sub(" ", text)
    text = _LEAN_BLOCK_COMMENT_RE.sub(" ", text)
    text = _LEAN_LINE_COMMENT_RE.sub("", text)
    return text


def _scan_lean_for_cheats(lean_text: Optional[str]) -> Optional[str]:
    """Return a human description of a cheat pattern, or None if clean.

    AXLE's `okay=true` only means the file parses; a sorry-laden spec or a
    spec that declares the conclusion as an axiom and "proves" it trivially
    will both compile. Catch those patterns here.
    """
    if not lean_text:
        return None
    stripped = _strip_lean_comments(lean_text)
    if _LEAN_SORRY_RE.search(stripped):
        return "found `sorry` in the Lean source (sorry leaves the goal unproven)."
    axiom_names = _LEAN_AXIOM_RE.findall(stripped)
    if axiom_names:
        # An axiom of the same name being used as the proof of the main theorem
        # is the classic cheat. Even one bare `axiom` declaration is suspicious
        # because we are formalizing claims, not assumptions.
        return (
            f"found `axiom {axiom_names[0]}` declaration. Declaring the conclusion "
            "as an axiom and discharging it with `trivial`/`exact` is not a real proof. "
            "Inline the assumption as a theorem hypothesis instead."
        )
    if _LEAN_TRIVIAL_TAUTOLOGY_RE.search(stripped):
        return (
            "the claim is encoded as `True`/`0 = 0`/`∃ _ : Type, True` — a tautology "
            "provable by `trivial`. This is not a faithful encoding of the atom."
        )
    if _LEAN_DEF_FALSE_RE.search(stripped):
        return (
            "found a `def ... := False` pattern, which makes `¬ <pred>` vacuously true. "
            "Define the predicate faithfully or emit not_a_theorem."
        )
    return None


def _rate_limit_delay_seconds(exc: Exception, attempt: int) -> float:
    import random

    text = str(exc)
    jitter = random.uniform(0.5, 3.0)
    max_delay = max(5.0, formalization_settings.formalization_model_retry_max_delay_seconds)
    match = re.search(r"try again in ([0-9.]+)s", text, flags=re.IGNORECASE)
    if match:
        return min(max_delay, max(5.0, float(match.group(1)) + 3.0 + jitter))
    return min(max_delay, 10.0 * attempt + jitter)
