"""arXiv source ingestion utilities.

An arXiv URL or article id identifies the e-print source bundle. The ingestion
path downloads that bundle, extracts it safely, selects the root TeX document,
and assembles local TeX includes for downstream review agents.
"""
from __future__ import annotations

import gzip
import logging
import re
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


_ARXIV_ID_RE = re.compile(
    r"""
    (?P<id>
        \d{4}\.\d{4,5}                         # numeric archive id: 1706.03762
      | [a-z\-]+(?:\.[a-z]{2})?/\d{7}          # category archive id: hep-th/9901001
    )
    (?:v(?P<version>\d+))?
    """,
    re.IGNORECASE | re.VERBOSE,
)

_ARXIV_HOSTS = (
    "arxiv.org",
    "www.arxiv.org",
    "browse.arxiv.org",
    "ar5iv.labs.arxiv.org",
    "ar5iv.org",
)

_FETCH_TIMEOUT_SECONDS = 60.0
_MAX_SOURCE_BYTES = 80 * 1024 * 1024
_TEX_INPUT_RE = re.compile(
    r"""
    (?<!%)
    \\(?P<cmd>input|include|subfile)
    \s*
    (?:\[[^\]]*\]\s*)?
    \{(?P<target>[^{}]+)\}
    """,
    re.VERBOSE,
)


class ArxivSourceError(RuntimeError):
    """Raised when an arXiv source bundle cannot produce assembled TeX."""


@dataclass(frozen=True)
class ArxivRef:
    """Normalized arXiv article reference."""

    arxiv_id: str
    version: Optional[str] = None

    @property
    def canonical(self) -> str:
        """Article id including version when one was supplied."""
        return f"{self.arxiv_id}v{self.version}" if self.version else self.arxiv_id

    @property
    def source_url(self) -> str:
        """Canonical arXiv e-print source URL."""
        return f"https://arxiv.org/e-print/{self.canonical}"


@dataclass(frozen=True)
class ArxivSource:
    """Extracted source metadata and assembled TeX text."""

    ref: ArxivRef
    source_url: str
    archive_path: str
    extract_dir: str
    main_tex_path: str
    tex_text: str
    tex_paths: list[str]


def parse_arxiv_url(value: str) -> Optional[ArxivRef]:
    """Parse an accepted arXiv URL or bare article id."""
    if not value:
        return None
    text = value.strip()
    if not text:
        return None

    # Bare id form: "1706.03762", "1706.03762v3", "hep-th/9901001".
    if "://" not in text:
        m = _ARXIV_ID_RE.fullmatch(text.removesuffix(".pdf"))
        if m:
            return ArxivRef(arxiv_id=m.group("id"), version=m.group("version"))
        return None

    try:
        from urllib.parse import urlparse

        parsed = urlparse(text)
    except Exception:
        return None

    if parsed.netloc.lower() not in _ARXIV_HOSTS:
        return None
    m = _ARXIV_ID_RE.search(parsed.path)
    if not m:
        return None
    return ArxivRef(arxiv_id=m.group("id"), version=m.group("version"))


async def fetch_arxiv_source(ref: ArxivRef, dest_dir: str) -> ArxivSource:
    """Download the e-print source bundle and return assembled TeX metadata."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    archive_path = dest / f"{_safe_name(ref.canonical)}_source.tar.gz"
    extract_dir = dest / "source"
    extract_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(
        timeout=_FETCH_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": "PaperCourt/0.1 (research tool)"},
    ) as client:
        resp = await client.get(ref.source_url)

    if resp.status_code != 200:
        raise ArxivSourceError(f"arXiv source fetch failed with HTTP {resp.status_code}")
    if not resp.content:
        raise ArxivSourceError("arXiv source fetch returned an empty body")
    if len(resp.content) > _MAX_SOURCE_BYTES:
        raise ArxivSourceError(
            f"arXiv source bundle is too large: {len(resp.content)} bytes"
        )

    archive_path.write_bytes(resp.content)

    tex_paths = unpack_source_archive(archive_path, extract_dir)
    main_tex = find_main_tex(extract_dir)
    tex_text = assemble_tex_document(main_tex, extract_dir)

    return ArxivSource(
        ref=ref,
        source_url=ref.source_url,
        archive_path=str(archive_path),
        extract_dir=str(extract_dir),
        main_tex_path=str(main_tex),
        tex_text=tex_text,
        tex_paths=[str(path) for path in tex_paths],
    )


def unpack_source_archive(archive_path: Path, extract_dir: Path) -> list[Path]:
    """Extract an e-print payload into ``extract_dir`` and return TeX files."""
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        extracted = _extract_tar(archive_path, extract_dir)
    except tarfile.TarError:
        extracted = _extract_single_file_payload(archive_path, extract_dir)

    tex_paths = sorted(path for path in extracted if path.suffix.lower() == ".tex")
    if not tex_paths:
        raise ArxivSourceError("source bundle did not contain any .tex files")
    return tex_paths


def find_main_tex(source_dir: Path) -> Path:
    """Select the root TeX document from an extracted source tree."""
    candidates = sorted(source_dir.rglob("*.tex"))
    if not candidates:
        raise ArxivSourceError("no .tex files found after extraction")

    scored = [(score_main_tex(path), path) for path in candidates]
    scored.sort(key=lambda item: (item[0], -len(item[1].parts)), reverse=True)
    best_score, best_path = scored[0]
    if best_score <= 0:
        raise ArxivSourceError("could not identify a main TeX file")
    logger.info("Selected main TeX %s with score %s", best_path, best_score)
    return best_path


def assemble_tex_document(main_tex: Path, source_dir: Path) -> str:
    """Expand local TeX includes into one document string."""
    root = source_dir.resolve()
    visited: set[Path] = set()

    def expand(path: Path) -> str:
        resolved = path.resolve()
        if not _is_within(resolved, root):
            return f"\n% PaperCourt skipped input outside source tree: {path}\n"
        if resolved in visited:
            return f"\n% PaperCourt skipped recursive input: {resolved.name}\n"
        visited.add(resolved)

        text = _read_text(resolved)

        def replace(match: re.Match[str]) -> str:
            target = match.group("target").strip()
            child = _resolve_tex_input(target, resolved.parent, root)
            if child is None:
                return match.group(0)
            return (
                f"\n% PaperCourt inlined {child.relative_to(root)}\n"
                f"{expand(child)}\n"
                f"% PaperCourt end inline {child.relative_to(root)}\n"
            )

        return _TEX_INPUT_RE.sub(replace, text)

    return expand(main_tex)


def _extract_tar(archive_path: Path, extract_dir: Path) -> list[Path]:
    """Extract regular files and directories from a tar payload safely."""
    extracted: list[Path] = []
    root = extract_dir.resolve()
    total_bytes = 0
    with tarfile.open(archive_path, "r:*") as tar:
        for member in tar.getmembers():
            if not (member.isfile() or member.isdir()):
                logger.info("Skipping non-file tar member %s", member.name)
                continue
            target = (extract_dir / member.name).resolve()
            if not _is_within(target, root):
                raise ArxivSourceError(f"unsafe tar member path: {member.name}")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            total_bytes += member.size
            if total_bytes > _MAX_SOURCE_BYTES:
                raise ArxivSourceError("extracted source bundle exceeds size limit")
            target.parent.mkdir(parents=True, exist_ok=True)
            fileobj = tar.extractfile(member)
            if fileobj is None:
                continue
            target.write_bytes(fileobj.read())
            extracted.append(target)
    return extracted


def _extract_single_file_payload(archive_path: Path, extract_dir: Path) -> list[Path]:
    """Store a single-file TeX payload as ``main.tex``."""
    raw = archive_path.read_bytes()
    try:
        data = gzip.decompress(raw)
    except OSError:
        data = raw

    if len(data) > _MAX_SOURCE_BYTES:
        raise ArxivSourceError("single-file source payload exceeds size limit")

    text_start = data[:4096].decode("utf-8", errors="ignore")
    if "\\documentclass" not in text_start and "\\begin{document}" not in text_start:
        raise ArxivSourceError("source payload was neither tar nor TeX")

    target = extract_dir / "main.tex"
    target.write_bytes(data)
    return [target]


def _resolve_tex_input(target: str, current_dir: Path, root: Path) -> Optional[Path]:
    """Resolve a TeX include target inside the extracted source tree."""
    clean = target.strip()
    if not clean or clean.startswith("|"):
        return None
    raw_candidates = [Path(clean)]
    if not Path(clean).suffix:
        raw_candidates.append(Path(f"{clean}.tex"))

    for raw in raw_candidates:
        for base in (current_dir, root):
            candidate = (base / raw).resolve()
            if _is_within(candidate, root) and candidate.is_file():
                return candidate
    return None


def _read_text(path: Path) -> str:
    """Read TeX source with common archive encodings."""
    for encoding in ("utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def score_main_tex(path: Path) -> int:
    """Score how likely a TeX file is to be the root document."""
    text = _read_text(path)
    lower_name = path.name.lower()
    score = 0
    if "\\documentclass" in text:
        score += 100
    if "\\begin{document}" in text:
        score += 80
    if "\\title" in text:
        score += 20
    if "\\begin{abstract}" in text or "\\abstract" in text:
        score += 15
    if lower_name in {"main.tex", "ms.tex", "paper.tex", "article.tex", "arxiv.tex"}:
        score += 25
    if any(part in lower_name for part in ("supp", "appendix", "table", "fig", "macro", "command", "style")):
        score -= 40
    score += min(len(text) // 5000, 10)
    return score


def _safe_name(value: str) -> str:
    """Return a filesystem-safe name for source artifacts."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _is_within(path: Path, root: Path) -> bool:
    """Return whether ``path`` is contained by ``root``."""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
