"""Markdown prompt loading and composition."""
from __future__ import annotations

from pathlib import Path


_PROMPT_DIR = Path(__file__).with_name("prompts")


class PromptBook:
    """Loads prompt markdown files once and formats them with simple variables."""

    def __init__(self, prompt_dir: Path = _PROMPT_DIR) -> None:
        self.prompt_dir = prompt_dir
        self._cache: dict[str, str] = {}

    def load(self, name: str) -> str:
        if name not in self._cache:
            path = self.prompt_dir / name
            self._cache[name] = path.read_text(encoding="utf-8")
        return self._cache[name]

    def render(self, name: str, **values: object) -> str:
        template = self.load(name)
        rendered = template
        for key, value in values.items():
            rendered = rendered.replace("{{" + key + "}}", str(value))
        rendered = rendered.replace("{{novelty_contract}}", "")
        return rendered

    @property
    def shared_tool_spec(self) -> str:
        return self.load("shared_tool_spec.md")

    @property
    def memory_spec(self) -> str:
        return self.load("memory_and_workspace_spec.md")

    @property
    def novelty_ideation_contract(self) -> str:
        return self.load("novelty_ideation_contract.md")

    def investigator_prompt(self, **values: object) -> str:
        return self.render("investigator_agent.md", **values)

    def subagent_prompt(self, **values: object) -> str:
        return self.render("subagent_researcher.md", **values)

    def critique_prompt(self, **values: object) -> str:
        return self.render("critique_agent.md", **values)

    def finalizer_prompt(self, **values: object) -> str:
        return self.render("finalizer.md", **values)
