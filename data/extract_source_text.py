"""Produce the canonical plain-text form of every case.

    python -m data.extract_source_text

For email cases the .eml is already plain text and is copied verbatim.
For PDF cases the text is what pdfplumber actually extracts -- not the
authoring source. That distinction matters: gold `source_span` values are
validated against THIS text, so a span can only be cited if a downstream
consumer could really recover it from the document.
"""
from __future__ import annotations

import pathlib

import pdfplumber

ROOT = pathlib.Path(__file__).resolve().parent.parent
EMAILS = ROOT / "data" / "synthetic" / "emails"
PDFS = ROOT / "data" / "synthetic" / "pdfs"
OUT = ROOT / "data" / "synthetic" / "source_text"

EMAIL_CASES = ["case_01", "case_02", "case_03", "case_04", "case_05",
               "case_10", "case_11"]
PDF_CASES = ["case_06", "case_07", "case_08", "case_09", "case_12"]


def pdf_text(path: pathlib.Path) -> str:
    parts = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            parts.append("[PAGE %d]\n%s" % (i, page.extract_text() or ""))
    return "\n\n".join(parts).strip() + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for case_id in EMAIL_CASES:
        text = (EMAILS / (case_id + ".eml")).read_text(encoding="utf-8")
        (OUT / (case_id + ".txt")).write_text(text, encoding="utf-8", newline="\n")
        print("%s  <- email   %6d chars" % (case_id, len(text)))
    for case_id in PDF_CASES:
        text = pdf_text(PDFS / (case_id + ".pdf"))
        (OUT / (case_id + ".txt")).write_text(text, encoding="utf-8", newline="\n")
        print("%s  <- pdf     %6d chars" % (case_id, len(text)))


if __name__ == "__main__":
    main()
