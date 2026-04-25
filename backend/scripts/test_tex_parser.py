"""Test the deterministic v0.4 TeX parser without LLM calls.

Usage:
    python backend/scripts/test_tex_parser.py
    python backend/scripts/test_tex_parser.py --live https://arxiv.org/abs/1706.03762
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from ingestion.arxiv import fetch_arxiv_source, parse_arxiv_url  # noqa: E402
from ingestion.tex_parser import parse_tex  # noqa: E402
from models import PaperSource, SourceKind  # noqa: E402


SAMPLE_TEX = r"""
\documentclass{article}
\title{A Tiny Theorem Paper}
\begin{document}
\maketitle
\begin{abstract}
We prove a nonnegativity theorem.
\end{abstract}

\section{Introduction}
For all real numbers $x$, the square is nonnegative.

\section{Main Result}
\begin{theorem}
For every $x \in \mathbb{R}$, $x^2 \ge 0$.
\end{theorem}
\begin{equation}
x^2 \ge 0
\end{equation}
This follows from $x \cdot x$ being a square \cite{hardy}.

\begin{thebibliography}{9}
\bibitem{hardy} G. H. Hardy. A Course of Pure Mathematics.
\end{thebibliography}
\end{document}
"""


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _source(paper_id: str, tex_text: str) -> PaperSource:
    return PaperSource(
        paper_id=paper_id,
        source_kind=SourceKind.MANUAL_TEX,
        fetched_at=datetime.utcnow(),
        content_hash=hashlib.md5(tex_text.encode("utf-8")).hexdigest()[:16],
    )


def test_sample_parse() -> None:
    parsed = parse_tex(SAMPLE_TEX, _source("sample", SAMPLE_TEX))
    _assert(parsed.title == "A Tiny Theorem Paper", f"bad title: {parsed.title!r}")
    _assert("nonnegativity theorem" in parsed.abstract, "abstract missing")
    _assert(len(parsed.sections) >= 3, f"too few sections: {parsed.sections}")
    _assert(any(s.heading == "Main Result" for s in parsed.sections), "section missing")
    _assert(any("x^2 \\ge 0" in eq.latex for eq in parsed.equations), "equation missing")
    _assert(parsed.bibliography[0].key == "hardy", "bibitem key missing")
    _assert("For every $x \\in \\mathbb{R}$" in parsed.raw_text, "claim text missing")


async def test_live_parse(urls: list[str]) -> None:
    for url in urls:
        ref = parse_arxiv_url(url)
        _assert(ref is not None, f"could not parse live URL {url!r}")
        with tempfile.TemporaryDirectory() as tmp:
            source = await fetch_arxiv_source(ref, tmp)
            parsed = parse_tex(source.tex_text, _source(ref.canonical, source.tex_text))
            _assert(parsed.raw_text, f"{url}: no raw_text")
            _assert(parsed.sections, f"{url}: no sections")
            _assert(parsed.equations, f"{url}: no equations")
            print(
                f"  live {url}: title={parsed.title[:60]!r}, "
                f"sections={len(parsed.sections)}, equations={len(parsed.equations)}, "
                f"chars={len(parsed.raw_text)}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        nargs="*",
        metavar="ARXIV_URL_OR_ID",
        help="Also fetch and parse real arXiv sources. Defaults to 1706.03762.",
    )
    args = parser.parse_args()

    test_sample_parse()
    print("offline TeX parser tests OK")

    if args.live is not None:
        urls = args.live or ["https://arxiv.org/abs/1706.03762"]
        asyncio.run(test_live_parse(urls))
        print("live TeX parser tests OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
