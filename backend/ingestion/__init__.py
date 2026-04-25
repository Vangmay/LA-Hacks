"""Source ingestion: arXiv fetch + TeX parsing into `ParsedPaper`."""
from .arxiv import (
    ArxivRef,
    ArxivSource,
    ArxivSourceError,
    fetch_arxiv_source,
    parse_arxiv_url,
)
from .tex_parser import parse_tex

__all__ = [
    "ArxivRef",
    "ArxivSource",
    "ArxivSourceError",
    "fetch_arxiv_source",
    "parse_arxiv_url",
    "parse_tex",
]
