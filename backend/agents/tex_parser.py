"""Parse assembled arXiv TeX into PaperCourt parser output.

The parser extracts title, abstract, sections, equations, bibliography entries,
plain review text, and scan status from a TeX document string.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


_SECTION_CMD_RE = re.compile(
    r"\\(?P<level>section|subsection|subsubsection|paragraph)\*?\s*(?:\[[^\]]*\]\s*)?\{",
    re.IGNORECASE,
)
_BEGIN_DOCUMENT_RE = re.compile(r"\\begin\s*\{document\}", re.IGNORECASE)
_END_DOCUMENT_RE = re.compile(r"\\end\s*\{document\}", re.IGNORECASE)
_BIBITEM_RE = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{(?P<key>[^{}]+)\}", re.DOTALL)
_TEXT_COMMAND_RE = re.compile(
    r"\\(?:textbf|textit|emph|texttt|textrm|mathrm|mathbf|mathit|caption)\*?"
    r"(?:\[[^\]]*\])?\{([^{}]*)\}"
)
_CITE_RE = re.compile(r"\\(?:cite|citep|citet|citealp|nocite)(?:\[[^\]]*\])*\{([^{}]+)\}")
_REF_RE = re.compile(r"\\(?:ref|eqref|autoref|cref|Cref)\{([^{}]+)\}")
_LABEL_RE = re.compile(r"\\label\{[^{}]+\}")
_ENV_WRAPPER_RE = re.compile(r"\\(?:begin|end)\s*\{[^{}]+\}")
_COMMAND_WITH_OPT_RE = re.compile(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])*")
_WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES_RE = re.compile(r"\n{3,}")

_EQUATION_ENVS = (
    "equation",
    "equation*",
    "align",
    "align*",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "eqnarray",
    "eqnarray*",
    "displaymath",
)
_TITLE_COMMANDS = ("title", "icmltitle", "papertitle")


class TexParserAgent(BaseAgent):
    """Extract review-ready paper structure from assembled TeX."""

    agent_id = "tex_parser"

    EMPTY_OUTPUT: Dict[str, Any] = {
        "title": "",
        "abstract": "",
        "sections": [],
        "equations": [],
        "bibliography": [],
        "raw_text": "",
        "is_scanned": False,
    }

    async def run(self, context: AgentContext) -> AgentResult:
        """Parse TeX from ``context.extra["tex_text"]`` or ``tex_path``."""
        tex_text = (context.extra or {}).get("tex_text")
        tex_path: Optional[str] = (context.extra or {}).get("tex_path") or (
            context.extra or {}
        ).get("main_tex_path")

        if not tex_text and tex_path:
            if not os.path.isfile(tex_path):
                return AgentResult(
                    agent_id=self.agent_id,
                    claim_id=None,
                    status="error",
                    output=dict(self.EMPTY_OUTPUT),
                    confidence=0.0,
                    error=f"tex_path not found: {tex_path!r}",
                )
            tex_text = Path(tex_path).read_text(encoding="utf-8", errors="replace")

        if not isinstance(tex_text, str) or not tex_text.strip():
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="error",
                output=dict(self.EMPTY_OUTPUT),
                confidence=0.0,
                error="tex_text missing or empty",
            )

        try:
            output = self._parse_tex(tex_text)
            confidence = 0.9 if output["raw_text"].strip() else 0.2
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="success",
                output=output,
                confidence=confidence,
            )
        except Exception as e:
            logger.exception("TexParserAgent failed")
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="error",
                output=dict(self.EMPTY_OUTPUT),
                confidence=0.0,
                error=str(e),
            )

    def _parse_tex(self, tex: str) -> Dict[str, Any]:
        """Return structured parser output for a TeX document."""
        clean = _strip_comments(tex)
        body = _document_body(clean)

        output = dict(self.EMPTY_OUTPUT)
        output["title"] = _latex_to_text(_extract_first_command_arg(clean, _TITLE_COMMANDS))
        output["abstract"] = _latex_to_text(_extract_environment(body, "abstract") or "")
        output["sections"] = _extract_sections(body, output["abstract"])
        output["equations"] = _extract_equations(body, output["sections"])
        output["bibliography"] = _extract_bibliography(body)
        output["raw_text"] = _build_raw_text(output["title"], body)
        return output


def parse_tex_text(tex_text: str) -> Dict[str, Any]:
    """Parse TeX synchronously for scripts and offline tests."""
    return TexParserAgent()._parse_tex(tex_text)


def _strip_comments(tex: str) -> str:
    """Remove unescaped TeX comments while preserving line structure."""
    lines: List[str] = []
    for line in tex.splitlines():
        cut = len(line)
        for idx, char in enumerate(line):
            if char == "%" and (idx == 0 or line[idx - 1] != "\\"):
                cut = idx
                break
        lines.append(line[:cut])
    return "\n".join(lines)


def _document_body(tex: str) -> str:
    """Return content between document boundaries when present."""
    begin = _BEGIN_DOCUMENT_RE.search(tex)
    if not begin:
        return tex
    end = _END_DOCUMENT_RE.search(tex, begin.end())
    if not end:
        return tex[begin.end() :]
    return tex[begin.end() : end.start()]


def _extract_command_arg(tex: str, command: str) -> str:
    """Return the first braced argument for a TeX command."""
    pattern = re.compile(rf"\\{re.escape(command)}\s*(?:\[[^\]]*\]\s*)?\{{", re.DOTALL)
    match = pattern.search(tex)
    if not match:
        return ""
    value, _ = _read_braced(tex, match.end() - 1)
    return value


def _extract_first_command_arg(tex: str, commands: Tuple[str, ...]) -> str:
    """Return the first populated command argument from ``commands``."""
    for command in commands:
        value = _extract_command_arg(tex, command)
        if value.strip():
            return value
    return ""


def _extract_environment(tex: str, env: str) -> str:
    """Return the body of the first matching TeX environment."""
    pattern = re.compile(
        rf"\\begin\s*\{{{re.escape(env)}\}}(?P<body>.*?)\\end\s*\{{{re.escape(env)}\}}",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(tex)
    return match.group("body").strip() if match else ""


def _extract_sections(body: str, abstract: str) -> List[Dict[str, str]]:
    """Split the document body into section dictionaries."""
    matches: List[Tuple[int, int, str]] = []
    for match in _SECTION_CMD_RE.finditer(body):
        heading, end = _read_braced(body, match.end() - 1)
        if heading:
            matches.append((match.start(), end, _latex_to_text(heading)))

    sections: List[Dict[str, str]] = []
    if abstract:
        sections.append({"heading": "Abstract", "content": abstract})

    if not matches:
        content = _latex_to_text(body)
        if content:
            sections.append({"heading": "body", "content": content})
        return sections

    preamble = body[: matches[0][0]]
    preamble_text = _latex_to_text(_remove_environment(preamble, "abstract"))
    if preamble_text:
        sections.append({"heading": "preamble", "content": preamble_text})

    for idx, (start, content_start, heading) in enumerate(matches):
        next_start = matches[idx + 1][0] if idx + 1 < len(matches) else len(body)
        content = _latex_to_text(body[content_start:next_start])
        if heading or content:
            sections.append({"heading": heading, "content": content})

    return [section for section in sections if section["heading"] or section["content"]]


def _extract_equations(body: str, sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Extract display and inline math with section labels."""
    section_spans = _section_spans(body)
    seen: set[str] = set()
    equations: List[Dict[str, str]] = []

    def add(latex: str, pos: int) -> None:
        normalized = latex.strip()
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        equations.append(
            {
                "id": f"eq_{len(equations) + 1}",
                "latex": normalized,
                "section": _section_for_position(pos, section_spans),
            }
        )

    for env in _EQUATION_ENVS:
        pattern = re.compile(
            rf"\\begin\s*\{{{re.escape(env)}\}}(?P<body>.*?)\\end\s*\{{{re.escape(env)}\}}",
            re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(body):
            add(match.group("body"), match.start())

    for pattern in (
        re.compile(r"\\\[(?P<body>.*?)\\\]", re.DOTALL),
        re.compile(r"(?<!\\)\$\$(?P<body>.*?)(?<!\\)\$\$", re.DOTALL),
        re.compile(r"(?<!\\)\$(?!\$)(?P<body>[^$\n]{2,})(?<!\\)\$", re.DOTALL),
    ):
        for match in pattern.finditer(body):
            add(match.group("body"), match.start())

    return equations


def _section_spans(body: str) -> List[Tuple[int, str]]:
    """Map section command positions to section headings."""
    spans: List[Tuple[int, str]] = [(0, "")]
    for match in _SECTION_CMD_RE.finditer(body):
        heading, _ = _read_braced(body, match.end() - 1)
        spans.append((match.start(), _latex_to_text(heading)))
    return sorted(spans, key=lambda item: item[0])


def _section_for_position(pos: int, spans: List[Tuple[int, str]]) -> str:
    """Return the section heading active at ``pos``."""
    current = ""
    for start, heading in spans:
        if start > pos:
            break
        current = heading
    return current


def _extract_bibliography(body: str) -> List[Dict[str, str]]:
    """Extract bibliography entries from TeX bibliography constructs."""
    bib_text = _extract_environment(body, "thebibliography")
    if bib_text:
        return _parse_bibitems(bib_text)

    entries = _parse_bibitems(body)
    if entries:
        return entries

    bib_commands = re.findall(r"\\bibliography\{([^{}]+)\}", body)
    return [
        {"ref_id": f"bibliography_{idx}", "raw_text": item.strip()}
        for idx, item in enumerate(bib_commands, start=1)
        if item.strip()
    ]


def _parse_bibitems(text: str) -> List[Dict[str, str]]:
    """Parse ``\\bibitem`` entries into bibliography dictionaries."""
    matches = list(_BIBITEM_RE.finditer(text))
    entries: List[Dict[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        raw = _latex_to_text(text[start:end])
        if raw:
            entries.append({"ref_id": match.group("key"), "raw_text": raw})
    return entries


def _build_raw_text(title: str, body: str) -> str:
    """Build plain review text from the title and document body."""
    raw = _latex_to_text(body)
    if title:
        return f"{title}\n\n{raw}".strip()
    return raw


def _latex_to_text(tex: str) -> str:
    """Convert common TeX markup to compact plain text."""
    text = tex
    text = _replace_equation_blocks(text)
    text = _replace_section_commands(text)
    text = _remove_environment(text, "abstract")
    text, math_segments = _protect_math_segments(text)
    text = _LABEL_RE.sub("", text)
    text = _CITE_RE.sub(lambda m: f"[{m.group(1)}]", text)
    text = _REF_RE.sub(lambda m: f"({m.group(1)})", text)

    previous = None
    while previous != text:
        previous = text
        text = _TEXT_COMMAND_RE.sub(lambda m: m.group(1), text)

    text = text.replace(r"\%", "%")
    text = text.replace(r"\&", "&")
    text = text.replace(r"\_", "_")
    text = text.replace(r"\#", "#")
    text = text.replace("~", " ")
    text = text.replace("\\\\", "\n")
    text = _ENV_WRAPPER_RE.sub("", text)
    text = _COMMAND_WITH_OPT_RE.sub("", text)
    text = text.replace("{", "").replace("}", "")
    for placeholder, value in math_segments.items():
        text = text.replace(placeholder, value)
    text = _WHITESPACE_RE.sub(" ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def _replace_equation_blocks(tex: str) -> str:
    """Normalize display math environments into delimited math blocks."""
    text = tex
    for env in _EQUATION_ENVS:
        pattern = re.compile(
            rf"\\begin\s*\{{{re.escape(env)}\}}(?P<body>.*?)\\end\s*\{{{re.escape(env)}\}}",
            re.IGNORECASE | re.DOTALL,
        )
        text = pattern.sub(lambda m: f"\n$${m.group('body').strip()}$$\n", text)
    text = re.sub(r"\\\[(?P<body>.*?)\\\]", lambda m: f"\n$${m.group('body').strip()}$$\n", text, flags=re.DOTALL)
    return text


def _protect_math_segments(tex: str) -> Tuple[str, Dict[str, str]]:
    """Protect math spans from command stripping."""
    segments: Dict[str, str] = {}
    pattern = re.compile(
        r"(?<!\\)\$\$(?P<display>.*?)(?<!\\)\$\$|"
        r"(?<!\\)\$(?!\$)(?P<inline>[^$\n]+?)(?<!\\)\$",
        re.DOTALL,
    )

    def replace(match: re.Match[str]) -> str:
        placeholder = f"@@PAPERCOURT_MATH_{len(segments)}@@"
        segments[placeholder] = match.group(0)
        return placeholder

    return pattern.sub(replace, tex), segments


def _replace_section_commands(tex: str) -> str:
    """Render section commands as plain-text headings."""
    output: List[str] = []
    cursor = 0
    for match in _SECTION_CMD_RE.finditer(tex):
        heading, end = _read_braced(tex, match.end() - 1)
        output.append(tex[cursor : match.start()])
        output.append(f"\n\n{_latex_to_text(heading)}\n")
        cursor = end
    output.append(tex[cursor:])
    return "".join(output)


def _remove_environment(tex: str, env: str) -> str:
    """Remove all instances of a TeX environment."""
    pattern = re.compile(
        rf"\\begin\s*\{{{re.escape(env)}\}}.*?\\end\s*\{{{re.escape(env)}\}}",
        re.IGNORECASE | re.DOTALL,
    )
    return pattern.sub("", tex)


def _read_braced(text: str, open_brace_idx: int) -> Tuple[str, int]:
    """Read a balanced braced value starting at ``open_brace_idx``."""
    if open_brace_idx < 0 or open_brace_idx >= len(text) or text[open_brace_idx] != "{":
        return "", open_brace_idx

    depth = 0
    start = open_brace_idx + 1
    idx = open_brace_idx
    while idx < len(text):
        char = text[idx]
        escaped = idx > 0 and text[idx - 1] == "\\"
        if char == "{" and not escaped:
            depth += 1
        elif char == "}" and not escaped:
            depth -= 1
            if depth == 0:
                return text[start:idx], idx + 1
        idx += 1
    return text[start:], len(text)
