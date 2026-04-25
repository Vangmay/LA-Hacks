"""arXiv URL parsing + paper fetcher.

Recognized URL forms (with optional ``vN`` version suffix):
    https://arxiv.org/abs/<id>
    https://arxiv.org/pdf/<id>[.pdf]
    https://arxiv.org/html/<id>
    https://ar5iv.labs.arxiv.org/html/<id>
    https://ar5iv.org/abs/<id>

The HTML rendering (LaTeXML) is preferred when available because it preserves
original LaTeX inside ``<math alttext="...">`` — far cleaner than PDF text
extraction for the numeric/symbolic verifiers.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


_ARXIV_ID_RE = re.compile(
    r"""
    (?P<id>
        \d{4}\.\d{4,5}        # new-style: 1706.03762
      | [a-z\-]+/\d{7}        # old-style: math/0123456
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

_FETCH_TIMEOUT_SECONDS = 30.0


@dataclass
class ArxivRef:
    arxiv_id: str
    version: Optional[str] = None

    @property
    def canonical(self) -> str:
        return f"{self.arxiv_id}v{self.version}" if self.version else self.arxiv_id

    @property
    def html_url(self) -> str:
        return f"https://arxiv.org/html/{self.canonical}"

    @property
    def ar5iv_url(self) -> str:
        return f"https://ar5iv.labs.arxiv.org/html/{self.canonical}"

    @property
    def pdf_url(self) -> str:
        return f"https://arxiv.org/pdf/{self.canonical}"


@dataclass
class FetchedPaper:
    ref: ArxivRef
    pdf_path: Optional[str]
    html_text: Optional[str]
    html_source_url: Optional[str]


def parse_arxiv_url(value: str) -> Optional[ArxivRef]:
    """Parse an arXiv URL or bare id. Returns None if unrecognized."""
    if not value:
        return None
    text = value.strip()
    if not text:
        return None

    # Bare id form: "1706.03762" or "1706.03762v3" or "math/0123456"
    if "/" not in text or text.startswith(("math/", "cs/", "stat/", "physics/")):
        m = _ARXIV_ID_RE.fullmatch(text)
        if m:
            return ArxivRef(arxiv_id=m.group("id"), version=m.group("version"))

    # URL form
    lowered = text.lower()
    if not (lowered.startswith("http://") or lowered.startswith("https://")):
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


async def fetch_paper(ref: ArxivRef, dest_dir: str) -> FetchedPaper:
    """Fetch HTML (preferring arxiv.org/html, falling back to ar5iv) + PDF.

    Always attempts the PDF as a guaranteed fallback. Returns whatever
    succeeded; either path may be None on failure.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    html_text: Optional[str] = None
    html_source_url: Optional[str] = None
    pdf_path: Optional[str] = None

    async with httpx.AsyncClient(
        timeout=_FETCH_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": "PaperCourt/0.1 (research tool)"},
    ) as client:
        for url in (ref.html_url, ref.ar5iv_url):
            try:
                resp = await client.get(url)
            except Exception as e:
                logger.warning("HTML fetch failed for %s: %s", url, e)
                continue
            if resp.status_code == 200 and "html" in resp.headers.get("content-type", "").lower():
                html_text = resp.text
                html_source_url = url
                break
            logger.info("HTML fetch %s -> %s", url, resp.status_code)

        try:
            pdf_resp = await client.get(ref.pdf_url)
            if pdf_resp.status_code == 200:
                target = dest / f"{ref.canonical}.pdf"
                target.write_bytes(pdf_resp.content)
                pdf_path = str(target)
            else:
                logger.warning("PDF fetch %s -> %s", ref.pdf_url, pdf_resp.status_code)
        except Exception as e:
            logger.warning("PDF fetch failed for %s: %s", ref.pdf_url, e)

    return FetchedPaper(
        ref=ref,
        pdf_path=pdf_path,
        html_text=html_text,
        html_source_url=html_source_url,
    )
