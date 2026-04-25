"""HtmlParserAgent — parse arXiv HTML (LaTeXML / ar5iv) into the same
``parser_output`` shape that ParserAgent emits.

Why: PDF text extraction loses LaTeX structure. arXiv's HTML build wraps every
equation in ``<math alttext="$LaTeX$">`` — exactly what the symbolic and
numeric verifiers want.

Input:
    context.extra["html_text"]   — required (string)
    context.extra["html_url"]    — optional, used for logging only

Output (matches ParserAgent.EMPTY_OUTPUT):
    {title, abstract, sections, equations, bibliography, raw_text, is_scanned}
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag

from .base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class HtmlParserAgent(BaseAgent):
    agent_id = "html_parser"

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
        html_text: Optional[str] = (context.extra or {}).get("html_text")
        if not html_text or not html_text.strip():
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="error",
                output=dict(self.EMPTY_OUTPUT),
                confidence=0.0,
                error="html_text missing or empty",
            )
        try:
            output = self._parse_html(html_text)
            confidence = 0.8 if output["raw_text"].strip() else 0.2
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="success",
                output=output,
                confidence=confidence,
            )
        except Exception as e:
            logger.exception("HtmlParserAgent failed")
            return AgentResult(
                agent_id=self.agent_id,
                claim_id=None,
                status="error",
                output=dict(self.EMPTY_OUTPUT),
                confidence=0.0,
                error=str(e),
            )

    def _parse_html(self, html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")

        # Strip nav / footer chrome that pollutes raw text.
        for sel in ("script", "style", "nav", "footer", "header", "aside"):
            for el in soup.find_all(sel):
                el.decompose()

        output = dict(self.EMPTY_OUTPUT)
        output["title"] = self._extract_title(soup)
        output["sections"] = self._extract_sections(soup)
        output["abstract"] = self._extract_abstract(soup, output["sections"])
        output["equations"] = self._extract_equations(soup)
        output["bibliography"] = self._extract_bibliography(soup)
        output["raw_text"] = self._extract_raw_text(soup)
        return output

    def _extract_title(self, soup: BeautifulSoup) -> str:
        for selector in ("h1.ltx_title_document", "h1.ltx_title", "h1"):
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                return el.get_text(" ", strip=True)
        if soup.title and soup.title.get_text(strip=True):
            return soup.title.get_text(strip=True)
        return ""

    def _extract_abstract(
        self,
        soup: BeautifulSoup,
        sections: List[Dict[str, str]],
    ) -> str:
        el = soup.select_one("div.ltx_abstract, section.ltx_abstract, abstract")
        if el:
            return el.get_text(" ", strip=True)
        for sec in sections:
            if sec["heading"].strip().lower().startswith("abstract"):
                return sec["content"]
        return ""

    def _extract_sections(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        # Prefer LaTeXML's explicit <section class="ltx_section"> nesting.
        ltx_sections = soup.select("section.ltx_section, section.ltx_subsection")
        sections: List[Dict[str, str]] = []
        if ltx_sections:
            for sec in ltx_sections:
                heading_el = sec.find(["h2", "h3", "h4"])
                heading = heading_el.get_text(" ", strip=True) if heading_el else ""
                body_parts: List[str] = []
                for child in sec.find_all(["p", "li"], recursive=True):
                    text = child.get_text(" ", strip=True)
                    if text:
                        body_parts.append(text)
                sections.append({"heading": heading, "content": " ".join(body_parts).strip()})
            return [s for s in sections if s["heading"] or s["content"]]

        # Generic fallback: walk h1/h2/h3 boundaries.
        body = soup.body or soup
        current = {"heading": "preamble", "parts": []}
        out: List[Dict[str, Any]] = []
        for el in body.find_all(["h1", "h2", "h3", "p", "li"]):
            if not isinstance(el, Tag):
                continue
            if el.name in ("h1", "h2", "h3"):
                if current["parts"] or current["heading"] != "preamble":
                    out.append({
                        "heading": current["heading"],
                        "content": " ".join(current["parts"]).strip(),
                    })
                current = {"heading": el.get_text(" ", strip=True), "parts": []}
            else:
                text = el.get_text(" ", strip=True)
                if text:
                    current["parts"].append(text)
        out.append({"heading": current["heading"], "content": " ".join(current["parts"]).strip()})
        return [s for s in out if s["heading"] or s["content"]]

    def _extract_equations(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        seen: set = set()
        eqs: List[Dict[str, str]] = []
        for math_el in soup.find_all("math"):
            latex = (math_el.get("alttext") or "").strip()
            if not latex:
                # ltx_Math span sometimes carries the LaTeX in data-* attrs
                latex = (math_el.get("data-latex") or "").strip()
            if not latex:
                continue
            if latex in seen:
                continue
            seen.add(latex)
            section = ""
            ancestor = math_el.find_parent(class_="ltx_section") or math_el.find_parent("section")
            if ancestor:
                heading_el = ancestor.find(["h2", "h3", "h4"])
                if heading_el:
                    section = heading_el.get_text(" ", strip=True)
            eqs.append({"id": f"eq_{len(eqs) + 1}", "latex": latex, "section": section})
        return eqs

    def _extract_bibliography(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        items = soup.select("li.ltx_bibitem, li.bibitem, ul.ltx_biblist > li")
        out: List[Dict[str, str]] = []
        for i, li in enumerate(items, start=1):
            text = li.get_text(" ", strip=True)
            if not text:
                continue
            ref_id = li.get("id") or f"ref_{i}"
            out.append({"ref_id": ref_id, "raw_text": text})
        return out

    def _extract_raw_text(self, soup: BeautifulSoup) -> str:
        # Replace each <math> with its LaTeX so downstream regex equation
        # matching still has something to bite on.
        for math_el in soup.find_all("math"):
            latex = math_el.get("alttext") or ""
            math_el.replace_with(f"$${latex}$$" if latex else "")
        return soup.get_text("\n", strip=True)
