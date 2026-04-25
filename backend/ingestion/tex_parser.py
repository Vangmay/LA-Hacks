"""Deterministic TeX → `ParsedPaper` parser.

The parser walks an assembled TeX document and produces a typed `ParsedPaper`
with stable section ids, equation latex (with `\\label{...}` keys preserved),
and bibliography entries that retain the `\\bibitem{key}` so atom citations
can resolve back to the bib by key (not just `[12]`).

Design choices:
- One pass over a comment-stripped document body.
- Section ids are deterministic: `sec_001`, `sec_002`, ... in document order.
- `raw_text` is plain prose; math is preserved as `$...$`/`$$...$$`.
- `assembled_tex` is the un-stripped TeX (post comment removal but with
  environments) so downstream code that wants TeX-level spans has a copy.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from models import (
    CitationEntry,
    EquationBlock,
    PaperSection,
    PaperSource,
    ParsedPaper,
    SourceSpan,
)

logger = logging.getLogger(__name__)


_SECTION_CMD_RE = re.compile(
    r"\\(?P<level>section|subsection|subsubsection|paragraph)\*?\s*"
    r"(?:\[[^\]]*\]\s*)?\{",
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
_LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
_LABEL_STRIP_RE = re.compile(r"\\label\{[^{}]+\}")
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


@dataclass
class _SectionMarker:
    section_id: str
    heading: str
    level: int
    tex_start: int
    tex_end: int  # end of section command (start of body in TeX)


def parse_tex(tex_text: str, source: PaperSource) -> ParsedPaper:
    """Parse an assembled TeX document into a typed `ParsedPaper`."""
    if not isinstance(tex_text, str) or not tex_text.strip():
        return ParsedPaper(
            paper_id=source.paper_id,
            source=source,
            raw_text="",
            assembled_tex=tex_text or "",
            parser_warnings=["empty TeX input"],
        )

    clean = _strip_comments(tex_text)
    body, body_offset = _document_body(clean)

    title = _latex_to_text(_extract_first_command_arg(clean, _TITLE_COMMANDS))
    abstract = _latex_to_text(_extract_environment(body, "abstract") or "")

    section_markers = _section_markers(body, abstract_present=bool(abstract))
    sections = _build_sections(
        body,
        body_offset,
        section_markers,
        abstract,
        paper_id=source.paper_id,
    )

    equations = _extract_equations(
        body,
        body_offset,
        section_markers,
        paper_id=source.paper_id,
    )
    bibliography = _extract_bibliography(body)

    raw_text = _build_raw_text(title, body)

    warnings: list[str] = []
    if not section_markers and not abstract:
        warnings.append("no sections or abstract detected")
    if not equations:
        warnings.append("no equations detected")

    return ParsedPaper(
        paper_id=source.paper_id,
        source=source,
        title=title,
        abstract=abstract,
        sections=sections,
        equations=equations,
        bibliography=bibliography,
        raw_text=raw_text,
        assembled_tex=clean,
        parser_warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Section + body parsing


def _strip_comments(tex: str) -> str:
    lines: List[str] = []
    for line in tex.splitlines():
        cut = len(line)
        for idx, char in enumerate(line):
            if char == "%" and (idx == 0 or line[idx - 1] != "\\"):
                cut = idx
                break
        lines.append(line[:cut])
    return "\n".join(lines)


def _document_body(tex: str) -> Tuple[str, int]:
    begin = _BEGIN_DOCUMENT_RE.search(tex)
    if not begin:
        return tex, 0
    end = _END_DOCUMENT_RE.search(tex, begin.end())
    if not end:
        return tex[begin.end():], begin.end()
    return tex[begin.end():end.start()], begin.end()


def _section_markers(body: str, abstract_present: bool) -> List[_SectionMarker]:
    markers: List[_SectionMarker] = []
    counter = 0
    for match in _SECTION_CMD_RE.finditer(body):
        heading, end = _read_braced(body, match.end() - 1)
        if not heading:
            continue
        counter += 1
        level_str = match.group("level").lower()
        level = {
            "section": 1,
            "subsection": 2,
            "subsubsection": 3,
            "paragraph": 4,
        }.get(level_str, 1)
        markers.append(
            _SectionMarker(
                section_id=f"sec_{counter:03d}",
                heading=_latex_to_text(heading),
                level=level,
                tex_start=match.start(),
                tex_end=end,
            )
        )
    return markers


def _build_sections(
    body: str,
    body_offset: int,
    markers: List[_SectionMarker],
    abstract: str,
    *,
    paper_id: str,
) -> List[PaperSection]:
    sections: List[PaperSection] = []

    if abstract:
        # Pin to the abstract environment span if we can find one.
        abs_match = re.search(
            r"\\begin\s*\{abstract\}(.*?)\\end\s*\{abstract\}",
            body,
            re.IGNORECASE | re.DOTALL,
        )
        if abs_match:
            sections.append(
                PaperSection(
                    section_id="sec_abstract",
                    heading="Abstract",
                    level=1,
                    content=abstract,
                    source_span=SourceSpan(
                        paper_id=paper_id,
                        section_id="sec_abstract",
                        tex_start=body_offset + abs_match.start(),
                        tex_end=body_offset + abs_match.end(),
                        raw_excerpt=abstract[:1000],
                        match_confidence=1.0,
                    ),
                )
            )

    if not markers:
        content = _latex_to_text(body)
        if content:
            sections.append(
                PaperSection(
                    section_id="sec_body",
                    heading="Body",
                    level=1,
                    content=content,
                    source_span=SourceSpan(
                        paper_id=paper_id,
                        section_id="sec_body",
                        tex_start=body_offset,
                        tex_end=body_offset + len(body),
                        raw_excerpt=content[:1000],
                        match_confidence=1.0,
                    ),
                )
            )
        return sections

    for idx, marker in enumerate(markers):
        next_start = markers[idx + 1].tex_start if idx + 1 < len(markers) else len(body)
        body_text = _latex_to_text(body[marker.tex_end:next_start])
        sections.append(
            PaperSection(
                section_id=marker.section_id,
                heading=marker.heading,
                level=marker.level,
                content=body_text,
                source_span=SourceSpan(
                    paper_id=paper_id,
                    section_id=marker.section_id,
                    tex_start=body_offset + marker.tex_start,
                    tex_end=body_offset + next_start,
                    raw_excerpt=body_text[:1000],
                    match_confidence=1.0,
                ),
            )
        )

    return sections


# ---------------------------------------------------------------------------
# Equations


def _extract_equations(
    body: str,
    body_offset: int,
    markers: List[_SectionMarker],
    *,
    paper_id: str,
) -> List[EquationBlock]:
    seen: set[str] = set()
    equations: List[EquationBlock] = []
    counter = 0

    def add(latex: str, env: Optional[str], pos_in_body: int, full_span: Tuple[int, int]) -> None:
        nonlocal counter
        normalized = latex.strip()
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        counter += 1
        label_match = _LABEL_RE.search(normalized)
        label = label_match.group(1) if label_match else None
        section_id = _section_id_for_position(pos_in_body, markers)
        equations.append(
            EquationBlock(
                equation_id=f"eq_{counter:03d}",
                latex=normalized,
                label=label,
                environment=env,
                section_id=section_id,
                source_span=SourceSpan(
                    paper_id=paper_id,
                    section_id=section_id,
                    tex_start=body_offset + full_span[0],
                    tex_end=body_offset + full_span[1],
                    raw_excerpt=normalized[:500],
                    match_confidence=1.0,
                ),
            )
        )

    for env in _EQUATION_ENVS:
        pattern = re.compile(
            rf"\\begin\s*\{{{re.escape(env)}\}}(?P<body>.*?)\\end\s*\{{{re.escape(env)}\}}",
            re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(body):
            add(match.group("body"), env, match.start(), (match.start(), match.end()))

    for env_name, pattern in (
        ("\\[..\\]", re.compile(r"\\\[(?P<body>.*?)\\\]", re.DOTALL)),
        ("$$...$$", re.compile(r"(?<!\\)\$\$(?P<body>.*?)(?<!\\)\$\$", re.DOTALL)),
        ("$...$", re.compile(r"(?<!\\)\$(?!\$)(?P<body>[^$\n]{2,})(?<!\\)\$", re.DOTALL)),
    ):
        for match in pattern.finditer(body):
            add(match.group("body"), env_name, match.start(), (match.start(), match.end()))

    return equations


def _section_id_for_position(pos: int, markers: List[_SectionMarker]) -> Optional[str]:
    current: Optional[str] = None
    for marker in markers:
        if marker.tex_start > pos:
            break
        current = marker.section_id
    return current


# ---------------------------------------------------------------------------
# Bibliography


def _extract_bibliography(body: str) -> List[CitationEntry]:
    bib_text = _extract_environment(body, "thebibliography")
    if bib_text:
        return _parse_bibitems(bib_text)
    entries = _parse_bibitems(body)
    if entries:
        return entries
    bib_commands = re.findall(r"\\bibliography\{([^{}]+)\}", body)
    return [
        CitationEntry(
            citation_id=f"cite_ext_{idx:03d}",
            key=item.strip(),
            raw_bib_text=f"\\bibliography{{{item.strip()}}}",
        )
        for idx, item in enumerate(bib_commands, start=1)
        if item.strip()
    ]


def _parse_bibitems(text: str) -> List[CitationEntry]:
    matches = list(_BIBITEM_RE.finditer(text))
    entries: List[CitationEntry] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        raw = _latex_to_text(text[start:end])
        if not raw:
            continue
        year_match = re.search(r"\b(19|20)\d{2}\b", raw)
        year = int(year_match.group(0)) if year_match else None
        entries.append(
            CitationEntry(
                citation_id=f"cite_{idx + 1:03d}",
                key=match.group("key"),
                raw_bib_text=raw,
                year=year,
            )
        )
    return entries


# ---------------------------------------------------------------------------
# Plain text rendering


def _build_raw_text(title: str, body: str) -> str:
    raw = _latex_to_text(body)
    if title:
        return f"{title}\n\n{raw}".strip()
    return raw


def _latex_to_text(tex: str) -> str:
    text = tex
    text = _replace_equation_blocks(text)
    text = _replace_section_commands(text)
    text = _remove_environment(text, "abstract")
    text, math_segments = _protect_math_segments(text)
    text = _LABEL_STRIP_RE.sub("", text)
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
    text = tex
    for env in _EQUATION_ENVS:
        pattern = re.compile(
            rf"\\begin\s*\{{{re.escape(env)}\}}(?P<body>.*?)\\end\s*\{{{re.escape(env)}\}}",
            re.IGNORECASE | re.DOTALL,
        )
        text = pattern.sub(lambda m: f"\n$${m.group('body').strip()}$$\n", text)
    text = re.sub(
        r"\\\[(?P<body>.*?)\\\]",
        lambda m: f"\n$${m.group('body').strip()}$$\n",
        text,
        flags=re.DOTALL,
    )
    return text


def _protect_math_segments(tex: str):
    segments: dict[str, str] = {}
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
    output: List[str] = []
    cursor = 0
    for match in _SECTION_CMD_RE.finditer(tex):
        heading, end = _read_braced(tex, match.end() - 1)
        output.append(tex[cursor:match.start()])
        output.append(f"\n\n{_latex_to_text(heading)}\n")
        cursor = end
    output.append(tex[cursor:])
    return "".join(output)


def _remove_environment(tex: str, env: str) -> str:
    pattern = re.compile(
        rf"\\begin\s*\{{{re.escape(env)}\}}.*?\\end\s*\{{{re.escape(env)}\}}",
        re.IGNORECASE | re.DOTALL,
    )
    return pattern.sub("", tex)


# ---------------------------------------------------------------------------
# Helpers


def _extract_command_arg(tex: str, command: str) -> str:
    pattern = re.compile(rf"\\{re.escape(command)}\s*(?:\[[^\]]*\]\s*)?\{{", re.DOTALL)
    match = pattern.search(tex)
    if not match:
        return ""
    value, _ = _read_braced(tex, match.end() - 1)
    return value


def _extract_first_command_arg(tex: str, commands: Tuple[str, ...]) -> str:
    for command in commands:
        value = _extract_command_arg(tex, command)
        if value.strip():
            return value
    return ""


def _extract_environment(tex: str, env: str) -> str:
    pattern = re.compile(
        rf"\\begin\s*\{{{re.escape(env)}\}}(?P<body>.*?)\\end\s*\{{{re.escape(env)}\}}",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(tex)
    return match.group("body").strip() if match else ""


def _read_braced(text: str, open_brace_idx: int) -> Tuple[str, int]:
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
