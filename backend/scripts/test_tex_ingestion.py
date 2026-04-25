"""Test arXiv TeX source ingestion without LLM calls.

Usage from repo root or backend/:
    python backend/scripts/test_tex_ingestion.py
    python backend/scripts/test_tex_ingestion.py --live https://arxiv.org/abs/1706.03762
"""
from __future__ import annotations

import argparse
import asyncio
import gzip
import io
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
sys.path.insert(0, str(BACKEND))

from ingestion.arxiv import (  # noqa: E402
    ArxivSourceError,
    assemble_tex_document,
    fetch_arxiv_source,
    find_main_tex,
    parse_arxiv_url,
    unpack_source_archive,
)


def _write_tar(path: Path, files: dict[str, str]) -> None:
    with tarfile.open(path, "w:gz") as tar:
        for name, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_parse_arxiv_url() -> None:
    cases = {
        "1706.03762": "1706.03762",
        "1706.03762v7": "1706.03762v7",
        "https://arxiv.org/abs/1706.03762": "1706.03762",
        "https://arxiv.org/pdf/1706.03762.pdf": "1706.03762",
        "https://arxiv.org/html/1706.03762v7": "1706.03762v7",
        "https://arxiv.org/abs/hep-th/9901001v2": "hep-th/9901001v2",
    }
    for raw, expected in cases.items():
        ref = parse_arxiv_url(raw)
        _assert(ref is not None, f"expected {raw!r} to parse")
        _assert(ref.canonical == expected, f"{raw!r}: {ref.canonical!r} != {expected!r}")
        _assert(ref.source_url.endswith(expected), f"{raw!r}: wrong source URL")

    _assert(parse_arxiv_url("https://example.com/abs/1706.03762") is None, "bad host parsed")
    _assert(parse_arxiv_url("not-an-arxiv-id") is None, "bad id parsed")


def test_unpack_find_and_assemble_tar() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        archive = root / "source.tar.gz"
        extract_dir = root / "extract"
        _write_tar(
            archive,
            {
                "main.tex": r"""
\documentclass{article}
\title{A Tiny Paper}
\begin{document}
\maketitle
\begin{abstract}A short abstract.\end{abstract}
\input{macros}
\include{sections/intro}
\bibliography{refs}
\end{document}
""",
                "macros.tex": r"\newcommand{\R}{\mathbb{R}}",
                "sections/intro.tex": r"\section{Intro} For all $x \in \R$, $x^2 \ge 0$.",
                "supplement.tex": r"\section{Supplement} Not the main file.",
            },
        )

        tex_paths = unpack_source_archive(archive, extract_dir)
        _assert(len(tex_paths) == 4, f"expected 4 tex files, got {len(tex_paths)}")

        main = find_main_tex(extract_dir)
        _assert(main.name == "main.tex", f"wrong main tex selected: {main}")

        assembled = assemble_tex_document(main, extract_dir)
        _assert(r"\newcommand{\R}" in assembled, "macro file was not inlined")
        _assert(r"\section{Intro}" in assembled, "section file was not inlined")
        _assert(r"\include{sections/intro}" not in assembled, "include command remained")


def test_single_gzip_tex_payload() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        archive = root / "source.gz"
        archive.write_bytes(gzip.compress(b"\\documentclass{article}\\begin{document}Hi\\end{document}"))
        extract_dir = root / "extract"

        tex_paths = unpack_source_archive(archive, extract_dir)
        _assert(len(tex_paths) == 1, f"expected one tex file, got {len(tex_paths)}")
        _assert(tex_paths[0].name == "main.tex", f"unexpected tex path {tex_paths[0]}")


def test_rejects_path_traversal() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        archive = root / "evil.tar.gz"
        _write_tar(archive, {"../evil.tex": r"\documentclass{article}"})
        try:
            unpack_source_archive(archive, root / "extract")
        except ArxivSourceError as exc:
            _assert("unsafe tar member" in str(exc), f"unexpected error: {exc}")
            return
        raise AssertionError("unsafe tar member was not rejected")


async def test_live_fetch(urls: list[str]) -> None:
    for url in urls:
        ref = parse_arxiv_url(url)
        _assert(ref is not None, f"could not parse live URL {url!r}")
        with tempfile.TemporaryDirectory() as tmp:
            source = await fetch_arxiv_source(ref, tmp)
            _assert(Path(source.archive_path).is_file(), "archive was not saved")
            _assert(Path(source.main_tex_path).is_file(), "main TeX was not found")
            _assert("\\begin{document}" in source.tex_text, "assembled TeX lacks document body")
            _assert(source.tex_paths, "no TeX paths recorded")
            print(
                f"  live {url}: main={Path(source.main_tex_path).name}, "
                f"tex_files={len(source.tex_paths)}, chars={len(source.tex_text)}"
            )


def run_offline() -> None:
    test_parse_arxiv_url()
    test_unpack_find_and_assemble_tar()
    test_single_gzip_tex_payload()
    test_rejects_path_traversal()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        nargs="*",
        metavar="ARXIV_URL_OR_ID",
        help="Also fetch real arXiv e-print sources. Defaults to 1706.03762 if no URL is supplied.",
    )
    args = parser.parse_args()

    run_offline()
    print("offline TeX ingestion tests OK")

    if args.live is not None:
        urls = args.live or ["https://arxiv.org/abs/1706.03762"]
        asyncio.run(test_live_fetch(urls))
        print("live TeX ingestion tests OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
