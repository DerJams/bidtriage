"""Assemble the document text for a case, single or multi-part.

Corpus v1 has exactly one source document per case. Corpus v2 introduces
platform cases that are a structured invitation email PLUS an attached scope
document, because that is how platform-sourced work actually arrives: the
invitation is system-generated and field-rich, and the ambiguity lives in the
attachment.

That breaks the one-document-per-case assumption in the runner, so assembly
lives here rather than being inlined. Two shapes are supported:

    "source":  "data/synthetic/emails/case_01.eml"          (v1, still valid)

    "sources": [
        {"path": "...", "role": "platform invitation", "kind": "email"},
        {"path": "...", "role": "scope attachment",    "kind": "pdf"}
    ]

Parts are concatenated with explicit headers so the model can tell an
invitation from an attachment, and so a citation can be traced to the part it
came from. Span validation runs against this same assembled text, which means a
gold citation can only be accepted if it is recoverable from exactly what the
model was shown.
"""
from __future__ import annotations

import pathlib

from evals import config

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT / "data" / "synthetic" / config.SOURCE_DIRNAME


def _part_header(index: int, total: int, role: str, kind: str) -> str:
    if total == 1:
        return ""
    return "[DOCUMENT %d of %d: %s (%s)]" % (index, total, role.upper(), kind)


def sources_of(gold: dict) -> list:
    """Normalize either shape into an ordered list of part descriptors."""
    if gold.get("sources"):
        out = []
        for s in gold["sources"]:
            if isinstance(s, str):
                out.append({"path": s, "role": "document",
                            "kind": "pdf" if s.lower().endswith(".pdf") else "email"})
            else:
                out.append({"path": s.get("path"),
                            "role": s.get("role") or "document",
                            "kind": s.get("kind")
                            or ("pdf" if str(s.get("path", "")).lower().endswith(".pdf")
                                else "email")})
        return out
    src = gold.get("source")
    if not src:
        return []
    return [{"path": src, "role": "document",
             "kind": "pdf" if src.lower().endswith(".pdf") else "email"}]


def _text_for_part(case_id: str, part: dict, index: int, total: int, loader=None) -> str:
    """Text for one part.

    `loader` lets a lever supply its own extraction (lever 1's parser, for
    instance) without this module needing to know about it. When absent, the
    pre-extracted canonical text is used, which is what the baseline sees.
    """
    if loader is not None:
        got = loader(part)
        if got is not None:
            return got
        # A loader that declines this part (lever 1's parser only handles PDFs)
        # falls through to the canonical extracted text rather than crashing.
    # Canonical extracted text. Multi-part cases store one file per part,
    # suffixed by index; single-part cases keep the plain case_id name.
    name = case_id if total == 1 else "%s_%d" % (case_id, index)
    path = SRC_DIR / (name + ".txt")
    if not path.exists() and total > 1:
        # Tolerate a corpus that has not been split yet.
        path = SRC_DIR / (case_id + ".txt")
    return path.read_text(encoding="utf-8")


def assemble(case_id: str, gold: dict, loader=None) -> tuple:
    """Return (document_text, manifest).

    manifest lists what was assembled, so a results file records exactly which
    parts the model was shown rather than leaving it implicit.
    """
    parts = sources_of(gold)
    total = len(parts)
    if total == 0:
        return "", []

    chunks, manifest = [], []
    for i, part in enumerate(parts, 1):
        text = _text_for_part(case_id, part, i, total, loader)
        header = _part_header(i, total, part["role"], part["kind"])
        chunks.append((header + "\n" + text).strip() if header else text.strip())
        manifest.append({"index": i, "path": part["path"], "role": part["role"],
                         "kind": part["kind"], "chars": len(text)})

    return "\n\n".join(chunks) + "\n", manifest
