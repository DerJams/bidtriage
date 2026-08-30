"""Lever 1: document parsing with real table handling.

The baseline pastes whatever `page.extract_text()` returns. That flattens a
spec table into a stream of words: column boundaries vanish, and a row reading

    21 12 00  Standpipe riser modification,  EA   0    6

arrives as "21 12 00 Standpipe riser modification, EA 0 6" -- the reader has to
infer which zero belongs to BASE BID and which six belongs to ALT 1.

This module instead:

* extracts tables structurally with pdfplumber and re-renders them as pipe
  tables, so column membership survives;
* uses layout-preserving text for the prose around them, so fixed-width blocks
  keep their alignment;
* marks page boundaries and calls out addenda sections explicitly, because a
  superseding addendum is the single most expensive thing to miss.

Email cases are already plain text and are passed through untouched, so this
lever only changes the five PDF cases. That bounds how much it could possibly
move the numbers, which is worth knowing before measuring it.
"""
from __future__ import annotations

import pathlib
import re

import pdfplumber

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Must match an actual addendum HEADING, not a passing mention. A cover sheet
# saying "issued subject to addenda" is not an addendum, and flagging it as one
# points the model at the wrong page -- worse than not flagging at all.
ADDENDUM_RE = re.compile(r"\bADDENDUM\s+NO\.?\s*\d|\bADDENDA\s+ISSUED\b", re.IGNORECASE)


def _render_table(table) -> str:
    rows = [["" if c is None else re.sub(r"\s+", " ", c).strip() for c in row]
            for row in table if row]
    rows = [r for r in rows if any(c for c in r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |",
           "|" + "|".join(["---"] * width) + "|"]
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def parse_pdf(path: pathlib.Path) -> str:
    parts = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            chunk = ["[PAGE %d]" % i]

            tables = page.find_tables()
            if tables:
                for n, t in enumerate(tables, 1):
                    rendered = _render_table(t.extract())
                    if rendered:
                        chunk.append("\n[TABLE %d.%d]\n%s" % (i, n, rendered))
                # Prose outside the tables, so table cells are not duplicated
                # into the narrative and read as loose numbers.
                outside = page
                for t in tables:
                    try:
                        outside = outside.outside_bbox(t.bbox)
                    except ValueError:
                        pass
                prose = outside.extract_text(layout=True) or ""
            else:
                prose = page.extract_text(layout=True) or ""

            prose = "\n".join(line.rstrip() for line in prose.splitlines() if line.strip())
            if prose:
                chunk.append("\n[TEXT]\n" + prose)

            page_text = "\n".join(chunk)
            if ADDENDUM_RE.search(page_text):
                chunk.insert(1, "\n[NOTICE] This page contains ADDENDA. An addendum "
                                "supersedes the cover sheet and page footers wherever "
                                "they disagree.")
                page_text = "\n".join(chunk)
            parts.append(page_text)
    return "\n\n".join(parts).strip() + "\n"


def build_document(gold: dict, fallback_text: str) -> tuple:
    """Return (document_text, parser_used)."""
    src = gold.get("source") or ""
    if not src.lower().endswith(".pdf"):
        return fallback_text, "passthrough_email"
    path = ROOT / src
    if not path.exists():
        return fallback_text, "fallback_missing_pdf"
    try:
        return parse_pdf(path), "pdfplumber_tables_layout"
    except Exception as e:  # never fail the case over a parser problem
        return fallback_text, "fallback_parse_error:%r" % (e,)


if __name__ == "__main__":
    import json
    import sys

    cid = sys.argv[1] if len(sys.argv) > 1 else "case_12"
    gold = json.loads((ROOT / "evals" / "gold" / (cid + ".json")).read_text(encoding="utf-8"))
    fb = (ROOT / "data" / "synthetic" / "source_text" / (cid + ".txt")).read_text(encoding="utf-8")
    text, used = build_document(gold, fb)
    print("parser: %s   chars: %d (was %d)\n" % (used, len(text), len(fb)))
    print(text)
