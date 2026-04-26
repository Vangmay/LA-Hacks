from __future__ import annotations

import asyncio

from formalization.toolbox import FormalizationToolbox, build_tool_schemas


class FakeAxleClient:
    def __init__(self) -> None:
        self.calls = []

    async def call(self, method_name: str, **kwargs):
        self.calls.append((method_name, kwargs))
        return {
            "okay": True,
            "content": kwargs.get("content", ""),
            "lean_messages": {"errors": [], "warnings": ["unused"], "infos": []},
            "tool_messages": {"errors": [], "warnings": [], "infos": []},
            "failed_declarations": [],
            "timings": {"total": 10},
        }


async def main() -> None:
    schemas = build_tool_schemas()
    names = {tool["function"]["name"] for tool in schemas}
    assert "axle_check" in names
    assert "emit_verdict" in names
    assert "record_artifact" in names

    fake = FakeAxleClient()
    toolbox = FormalizationToolbox(client=fake)
    result = await toolbox.dispatch(
        "axle_check",
        {"content": "import Mathlib\nexample : 1 + 1 = 2 := by norm_num\n"},
        call_id="call_check",
    )
    assert result.record.status == "success"
    assert result.record.result_summary["okay"] is True
    assert fake.calls[0][0] == "check"
    assert fake.calls[0][1]["environment"]
    assert fake.calls[0][1]["timeout_seconds"]

    meta = await toolbox.dispatch(
        "emit_verdict",
        {
            "label": "formalized_only",
            "rationale": "Spec compiles; proof was not attempted.",
            "confidence": 0.6,
        },
        call_id="call_verdict",
    )
    assert meta.record.status == "success"
    assert meta.meta["name"] == "emit_verdict"
    print("toolbox offline ok")


if __name__ == "__main__":
    asyncio.run(main())
