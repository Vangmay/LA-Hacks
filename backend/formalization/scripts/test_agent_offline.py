from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from formalization.agent import FormalizationAgent
from formalization.event_bus import formalization_event_bus
from formalization.models import FormalizationLabel
from formalization.store import formalization_store
from formalization.toolbox import FormalizationToolbox


BAD_SPEC = "import Mathlib\n\ntheorem smoke_formalization : 1 + 1 = 2 := by\n  bogus\n"
GOOD_SPEC = "import Mathlib\n\ntheorem smoke_formalization : 1 + 1 = 2 := by\n  norm_num\n"


class FakeCompletions:
    def __init__(self) -> None:
        self.index = 0

    async def create(self, **_kwargs):
        self.index += 1
        if self.index == 1:
            return fake_response(
                "I will record the first Lean artifact.",
                [
                    fake_tool_call(
                        "call_record",
                        "record_artifact",
                        {"kind": "spec", "lean_code": BAD_SPEC},
                    )
                ],
            )
        if self.index == 2:
            return fake_response(
                "Now I will ask AXLE to check it.",
                [fake_tool_call("call_check_bad", "axle_check", {"content": BAD_SPEC})],
            )
        if self.index == 3:
            return fake_response(
                "I will try to stop too early.",
                [
                    fake_tool_call(
                        "call_premature_verdict",
                        "emit_verdict",
                        {
                            "label": "formalized_only",
                            "rationale": "This should be blocked because AXLE check failed.",
                            "used_assumptions": [],
                            "confidence": 0.5,
                        },
                    )
                ],
            )
        if self.index == 4:
            return fake_response(
                "I will repair the spec and record it.",
                [
                    fake_tool_call(
                        "call_record_good",
                        "record_artifact",
                        {"kind": "spec", "lean_code": GOOD_SPEC},
                    )
                ],
            )
        if self.index == 5:
            return fake_response(
                "Now I will check the repaired spec.",
                [fake_tool_call("call_check_good", "axle_check", {"content": GOOD_SPEC})],
            )
        return fake_response(
            "The spec compiles, so I will emit an honest verdict.",
            [
                fake_tool_call(
                    "call_verdict",
                    "emit_verdict",
                    {
                        "label": "formalized_only",
                        "rationale": "Offline fake AXLE check succeeded.",
                        "used_assumptions": [],
                        "confidence": 0.7,
                    },
                )
            ],
        )


class FakeOpenAI:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions())


class FakeAxleClient:
    async def call(self, method_name: str, **kwargs):
        assert method_name == "check"
        assert "environment" in kwargs
        okay = "norm_num" in kwargs["content"]
        return {
            "okay": okay,
            "content": kwargs["content"],
            "lean_messages": {
                "errors": [] if okay else ["unknown tactic 'bogus'"],
                "warnings": [],
                "infos": [],
            },
            "tool_messages": {"errors": [], "warnings": [], "infos": []},
            "failed_declarations": [] if okay else ["smoke_formalization"],
            "timings": {"total": 1},
        }


def fake_response(content, tool_calls):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=content,
                    tool_calls=tool_calls,
                )
            )
        ]
    )


def fake_tool_call(call_id, name, args):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(args)),
    )


async def main() -> None:
    run = formalization_store.create_run(
        job_id="job_offline",
        paper_id="paper_offline",
        selected_atom_ids=["atom_offline"],
    )
    formalization_event_bus.create_channel(run.run_id)
    formalization_store.ensure_atom(run.run_id, "atom_offline", "paper_offline")

    agent = FormalizationAgent(
        client=FakeOpenAI(),
        toolbox=FormalizationToolbox(client=FakeAxleClient()),
    )
    await agent.run_atom(
        run_id=run.run_id,
        atom_id="atom_offline",
        context={
            "paper_id": "paper_offline",
            "title": "Offline",
            "atom_id": "atom_offline",
            "atom_type": "theorem",
            "importance": "medium",
            "atom_text": "1 + 1 = 2",
            "tex_excerpt": "1 + 1 = 2",
            "nearby_prose": "A tiny theorem.",
        },
    )

    stored = formalization_store.get_run(run.run_id)
    atom = stored.atom_formalizations["atom_offline"]
    assert atom.label == FormalizationLabel.FORMALIZED_ONLY
    assert len(atom.artifacts) == 2
    assert atom.artifacts[0].axle_check_okay is False
    assert atom.artifacts[1].axle_check_okay is True
    assert atom.tool_calls[-1].tool_name == "emit_verdict"
    assert len(atom.tool_calls) == 6
    print("agent offline ok")


if __name__ == "__main__":
    asyncio.run(main())
