import asyncio
import logging
import os
import re
import statistics
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


_EQ_PATTERNS = [
    re.compile(r"\$\$(.+?)\$\$", re.DOTALL),
    re.compile(r"\\begin\{equation\*?\}(.+?)\\end\{equation\*?\}", re.DOTALL),
    re.compile(r"\\begin\{align\*?\}(.+?)\\end\{align\*?\}", re.DOTALL),
    re.compile(r"\\begin\{eqnarray\*?\}(.+?)\\end\{eqnarray\*?\}", re.DOTALL),
    re.compile(r"\$([^$\n]{2,})\$"),
]
_BIB_HEADING_RE = re.compile(r"^\s*(references|bibliography)\b.*$", re.IGNORECASE)
_NUMBERED_HEADING_RE = re.compile(r"^\s*\d+(\.\d+){0,3}\.?\s+[A-Z]")
_BIBITEM_RE = re.compile(r"\\bibitem\{[^}]*\}")
_NUMBERED_BIB_RE = re.compile(r"\[(\d+)\]")
_KNOWN_HEADINGS = {
    "abstract", "introduction", "background", "related work",
    "methodology", "methods", "experiments", "results", "discussion",
    "conclusion", "conclusions", "acknowledgments", "acknowledgements",
    "references", "bibliography", "appendix",
}


class ParserAgent(BaseAgent):
    agent_id = "parser"

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
        pdf_path: Optional[str] = (context.extra or {}).get("pdf_path")
        if not pdf_path or not os.path.isfile(pdf_path):
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="error",
                output=dict(self.EMPTY_OUTPUT),
                confidence=0.0,
                error=f"pdf_path not found: {pdf_path!r}",
            )
        try:
            output = self._parse_pdf(pdf_path)
            confidence = 0.1 if output.get("is_scanned") else 0.6
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="success",
                output=output,
                confidence=confidence,
            )
        except Exception as e:
            logger.exception("ParserAgent failed on %s", pdf_path)
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="error",
                output=dict(self.EMPTY_OUTPUT),
                confidence=0.0,
                error=str(e),
            )

    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        output = dict(self.EMPTY_OUTPUT)
        doc = fitz.open(file_path)
        try:
            spans = self._collect_spans(doc)
            raw_text = "\n".join(page.get_text() for page in doc)
            output["raw_text"] = raw_text

            if not raw_text.strip():
                output["is_scanned"] = True
                return output

            output["title"] = self._extract_title(spans)
            output["sections"] = self._extract_sections(spans)
            output["abstract"] = self._extract_abstract(output["sections"], raw_text)
            output["equations"] = self._extract_equations(output["sections"], raw_text)
            output["bibliography"] = self._extract_bibliography(output["sections"], raw_text)
            return output
        finally:
            doc.close()

    def _collect_spans(self, doc) -> List[Dict[str, Any]]:
        spans: List[Dict[str, Any]] = []
        for page_idx, page in enumerate(doc):
            data = page.get_text("dict")
            for block in data.get("blocks", []):
                if block.get("type", 0) != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        spans.append({
                            "text": text,
                            "size": float(span.get("size", 0.0)),
                            "font": span.get("font", ""),
                            "page": page_idx,
                        })
        return spans

    def _body_font_size(self, spans: List[Dict[str, Any]]) -> float:
        sizes = [s["size"] for s in spans if s["size"] > 0]
        return statistics.median(sizes) if sizes else 10.0

    def _extract_title(self, spans: List[Dict[str, Any]]) -> str:
        # Skip arXiv banner spans — they often outrank the real title in size.
        page_zero = [
            s for s in spans
            if s["page"] == 0 and not s["text"].lstrip().lower().startswith("arxiv:")
        ]
        if not page_zero:
            return ""
        max_size = max(s["size"] for s in page_zero)
        title_parts: List[str] = []
        for s in page_zero:
            if abs(s["size"] - max_size) < 0.25:
                title_parts.append(s["text"])
            elif title_parts:
                break
        return " ".join(title_parts).strip()

    def _is_heading_text(self, text: str) -> bool:
        stripped = text.strip().rstrip(".:")
        if len(stripped) > 80:
            return False
        if stripped.lower() in _KNOWN_HEADINGS:
            return True
        if _NUMBERED_HEADING_RE.match(text):
            return True
        return False

    def _extract_sections(self, spans: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        body = self._body_font_size(spans)
        size_threshold = body + 1.0

        sections: List[Dict[str, Any]] = []
        current = {"heading": "preamble", "parts": []}

        for s in spans:
            text = s["text"].strip()
            looks_like_heading = (
                (s["size"] > size_threshold and len(text) < 120)
                or self._is_heading_text(text)
            )
            if looks_like_heading:
                if current["parts"] or current["heading"] != "preamble":
                    sections.append({
                        "heading": current["heading"],
                        "content": " ".join(current["parts"]).strip(),
                    })
                current = {"heading": text, "parts": []}
            else:
                current["parts"].append(text)

        sections.append({
            "heading": current["heading"],
            "content": " ".join(current["parts"]).strip(),
        })
        return [sec for sec in sections if sec["heading"] or sec["content"]]

    def _extract_abstract(self, sections: List[Dict[str, str]], raw_text: str) -> str:
        for sec in sections:
            if sec["heading"].strip().lower().startswith("abstract"):
                return sec["content"]
        m = re.search(
            r"abstract\s*[:\-—]?\s*(.+?)(?:\n\s*\n|\b1\s+introduction\b)",
            raw_text,
            re.IGNORECASE | re.DOTALL,
        )
        return m.group(1).strip() if m else ""

    def _extract_equations(
        self,
        sections: List[Dict[str, str]],
        raw_text: str,
    ) -> List[Dict[str, str]]:
        eqs: List[Dict[str, str]] = []
        seen: set = set()

        def add(latex: str, section: str) -> None:
            normalized = latex.strip()
            if not normalized or normalized in seen:
                return
            seen.add(normalized)
            eqs.append({
                "id": f"eq_{len(eqs) + 1}",
                "latex": normalized,
                "section": section,
            })

        for sec in sections:
            for pat in _EQ_PATTERNS:
                for m in pat.finditer(sec["content"]):
                    add(m.group(1) if m.lastindex else m.group(0), sec["heading"])

        if not eqs:
            for pat in _EQ_PATTERNS:
                for m in pat.finditer(raw_text):
                    add(m.group(1) if m.lastindex else m.group(0), "")

        return eqs

    def _extract_bibliography(
        self,
        sections: List[Dict[str, str]],
        raw_text: str,
    ) -> List[Dict[str, str]]:
        text = ""
        for sec in sections:
            if _BIB_HEADING_RE.match(sec["heading"].strip()):
                text = sec["content"]
                break
        if not text:
            m = re.search(r"\b(References|Bibliography)\b", raw_text)
            if m:
                text = raw_text[m.end():]
        if not text:
            return []

        if _BIBITEM_RE.search(text):
            chunks = _BIBITEM_RE.split(text)[1:]
            return [
                {"ref_id": f"ref_{i + 1}", "raw_text": chunk.strip()}
                for i, chunk in enumerate(chunks) if chunk.strip()
            ]

        if _NUMBERED_BIB_RE.search(text):
            parts = re.split(r"\[(\d+)\]", text)
            entries: List[Dict[str, str]] = []
            for i in range(1, len(parts) - 1, 2):
                raw = parts[i + 1].strip()
                if raw:
                    entries.append({"ref_id": f"[{parts[i]}]", "raw_text": raw})
            if entries:
                return entries

        return [
            {"ref_id": f"ref_{i + 1}", "raw_text": line.strip()}
            for i, line in enumerate(re.split(r"\n\s*\n", text))
            if line.strip()
        ]


def parse_pdf(file_path: str) -> dict:
    """Convenience wrapper: instantiate the agent and run it synchronously."""
    agent = ParserAgent()
    ctx = AgentContext(job_id="standalone", extra={"pdf_path": file_path})
    result = asyncio.run(agent.run(ctx))
    return result.output


if __name__ == "__main__":
    # Run from the backend/ directory:  python -m agents.parser <pdf_path>
    import sys

    test_path = sys.argv[1] if len(sys.argv) > 1 else "tests/fixtures/test_paper.pdf"
    out = parse_pdf(test_path)
    title = out.get("title", "") or ""
    print(f"title:        {title[:80]}")
    print(f"sections:     {len(out.get('sections', []))}")
    print(f"equations:    {len(out.get('equations', []))}")
    print(f"bibliography: {len(out.get('bibliography', []))}")
    print(f"is_scanned:   {out.get('is_scanned')}")
