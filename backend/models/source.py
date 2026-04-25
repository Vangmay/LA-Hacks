"""Source-grounded paper objects.

`PaperSource` is the provenance handle. `ParsedPaper` is the typed handoff
between ingestion and atom extraction. Every span-bearing object carries a
`SourceSpan` so every later artifact can quote the exact paper text.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SourceKind(str, Enum):
    ARXIV = "arxiv"
    MANUAL_TEX = "manual_tex"


class PaperSource(BaseModel):
    paper_id: str
    source_kind: SourceKind

    arxiv_id: Optional[str] = None
    arxiv_version: Optional[str] = None
    source_url: Optional[str] = None
    abs_url: Optional[str] = None
    pdf_url: Optional[str] = None

    source_archive_path: Optional[str] = None
    source_extract_dir: Optional[str] = None
    main_tex_path: Optional[str] = None
    assembled_tex_path: Optional[str] = None

    fetched_at: datetime
    content_hash: str


class SourceSpan(BaseModel):
    """Source grounding for any extracted object.

    `char_start`/`char_end` index `ParsedPaper.raw_text`.
    `tex_start`/`tex_end` index `ParsedPaper.assembled_tex`.
    `raw_excerpt` is mandatory because the frontend can always render it.
    `match_confidence` is 1.0 only when the resolver landed an exact hit.
    """

    paper_id: str
    section_id: Optional[str] = None

    char_start: Optional[int] = None
    char_end: Optional[int] = None
    tex_start: Optional[int] = None
    tex_end: Optional[int] = None

    raw_excerpt: str
    match_confidence: float = Field(ge=0.0, le=1.0)


class PaperSection(BaseModel):
    section_id: str
    heading: str
    level: int = 1
    content: str
    source_span: SourceSpan


class EquationBlock(BaseModel):
    equation_id: str
    latex: str

    label: Optional[str] = None
    environment: Optional[str] = None
    section_id: Optional[str] = None

    source_span: Optional[SourceSpan] = None


class CitationEntry(BaseModel):
    citation_id: str

    key: Optional[str] = None
    label: Optional[str] = None

    raw_bib_text: str = ""

    title: Optional[str] = None
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None


class ParsedPaper(BaseModel):
    paper_id: str
    source: PaperSource

    title: str = ""
    authors: list[str] = Field(default_factory=list)
    abstract: str = ""

    sections: list[PaperSection] = Field(default_factory=list)
    equations: list[EquationBlock] = Field(default_factory=list)
    bibliography: list[CitationEntry] = Field(default_factory=list)

    raw_text: str
    assembled_tex: Optional[str] = None

    parser_name: Literal["tex_parser"] = "tex_parser"
    parser_warnings: list[str] = Field(default_factory=list)
