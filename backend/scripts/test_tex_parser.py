"""Test TexParserAgent without LLM calls.

Usage:
    python backend/scripts/test_tex_parser.py
    python backend/scripts/test_tex_parser.py --live https://arxiv.org/abs/1706.03762
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from agents.base import AgentContext  # noqa: E402
from agents.tex_parser import TexParserAgent, parse_tex_text  # noqa: E402
from utils.arxiv import fetch_arxiv_source, parse_arxiv_url  # noqa: E402


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


def test_sample_parse_sync() -> None:
    parsed = parse_tex_text(SAMPLE_TEX)
    _assert(parsed["title"] == "A Tiny Theorem Paper", f"bad title: {parsed['title']!r}")
    _assert("nonnegativity theorem" in parsed["abstract"], "abstract missing")
    _assert(len(parsed["sections"]) >= 3, f"too few sections: {parsed['sections']}")
    _assert(any(s["heading"] == "Main Result" for s in parsed["sections"]), "section missing")
    _assert(any("x^2 \\ge 0" in eq["latex"] for eq in parsed["equations"]), "equation missing")
    _assert(parsed["bibliography"][0]["ref_id"] == "hardy", "bibitem key missing")
    _assert("For every $x \\in \\mathbb{R}$" in parsed["raw_text"], "claim text missing")


async def test_sample_parse_agent() -> None:
    result = await TexParserAgent().run(
        AgentContext(job_id="tex-parser-test", extra={"tex_text": SAMPLE_TEX})
    )
    _assert(result.status == "success", f"agent failed: {result.error}")
    _assert(result.confidence >= 0.8, f"unexpected confidence: {result.confidence}")
    _assert(result.output["equations"], "agent output has no equations")


async def test_live_parse(urls: list[str]) -> None:
    for url in urls:
        ref = parse_arxiv_url(url)
        _assert(ref is not None, f"could not parse live URL {url!r}")
        with tempfile.TemporaryDirectory() as tmp:
            source = await fetch_arxiv_source(ref, tmp)
            result = await TexParserAgent().run(
                AgentContext(job_id="tex-parser-live", extra={"tex_text": source.tex_text})
            )
            _assert(result.status == "success", f"{url}: parser failed: {result.error}")
            out = result.output
            _assert(out["raw_text"], f"{url}: no raw_text")
            _assert(out["sections"], f"{url}: no sections")
            _assert(out["equations"], f"{url}: no equations")
            print(
                f"  live {url}: title={out['title'][:60]!r}, "
                f"sections={len(out['sections'])}, equations={len(out['equations'])}, "
                f"chars={len(out['raw_text'])}"
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

    test_sample_parse_sync()
    asyncio.run(test_sample_parse_agent())
    print("offline TeX parser tests OK")

    if args.live is not None:
        urls = args.live or ["https://arxiv.org/abs/1706.03762"]
        asyncio.run(test_live_parse(urls))
        print("live TeX parser tests OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
