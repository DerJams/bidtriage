"""Build corpus v2: render documents, extract text, author and validate gold.

    python -m data.v2.build

Design decision that matters: a case is defined as a list of BLOCKS, and each
block that carries a scored field is tagged with that field name. The document
is assembled from those blocks, and the gold `source_span` for a field is the
block text itself. The span is therefore verbatim by construction rather than
by me copying it correctly thirty times.

v1 authored spans by hand and validated them afterwards. That worked, but it
made every new case an opportunity to introduce a span that did not quite match
the rendered document. This removes the opportunity.

Multi-part cases (platform invitation plus attachment) render one document per
part and are assembled by evals.harness.documents, which is what the model is
shown and what spans are validated against.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import date

import reportlab.rl_config as rl_config

rl_config.invariant = 1

from reportlab.lib.pagesizes import LETTER  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EMAILS = ROOT / "data" / "synthetic" / "emails_v2"
PDFS = ROOT / "data" / "synthetic" / "pdfs_v2"
SRC = ROOT / "data" / "synthetic" / "source_text_v2"
GOLD = ROOT / "evals" / "gold_v2"

SCORED_FIELDS = ["client_name", "project_title", "trade_scope", "location",
                 "bid_due_date", "estimated_project_value", "bond_insurance",
                 "walkthrough_date"]

_ss = getSampleStyleSheet()
BODY = ParagraphStyle("b", parent=_ss["BodyText"], fontName="Helvetica",
                      fontSize=9.5, leading=13, spaceAfter=6)
MONO = ParagraphStyle("m", parent=BODY, fontName="Courier", fontSize=8.4, leading=11)
H = ParagraphStyle("h", parent=_ss["Heading2"], fontName="Helvetica-Bold",
                   fontSize=11, leading=14, spaceBefore=10, spaceAfter=4)


def ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def render_email(case: dict, part: dict) -> str:
    """An .eml is plain text, so blocks are emitted verbatim."""
    head = part["headers"]
    lines = ["From: %s" % head["from"], "To: %s" % head["to"],
             "Subject: %s" % head["subject"], "Date: %s" % head["date"],
             'Content-Type: text/plain; charset="utf-8"', ""]
    for kind, text in part["blocks"]:
        lines.append(text)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_pdf(case: dict, part: dict, path: pathlib.Path) -> None:
    story = []
    for kind, text in part["blocks"]:
        if kind == "__heading__":
            story.append(Paragraph(text, H))
        elif kind == "__mono__":
            for line in text.split("\n"):
                story.append(Paragraph(line.replace(" ", "&nbsp;") or "&nbsp;", MONO))
        elif kind == "__pagebreak__":
            story.append(PageBreak())
        else:
            story.append(Paragraph(text, BODY))
        story.append(Spacer(1, 2))
    doc = SimpleDocTemplate(str(path), pagesize=LETTER,
                            leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                            topMargin=0.8 * inch, bottomMargin=0.85 * inch,
                            title=path.stem, author="Synthetic corpus v2",
                            subject="Fictional bid document")
    doc.build(story)


def pdf_text(path: pathlib.Path) -> str:
    import pdfplumber
    parts = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            parts.append("[PAGE %d]\n%s" % (i, page.extract_text() or ""))
    return "\n\n".join(parts).strip() + "\n"


# --------------------------------------------------------------------------
# Gold construction
# --------------------------------------------------------------------------

def build_gold(case: dict, assembled: str) -> dict:
    """Spans come from the tagged blocks, so they cannot drift from the doc."""
    spans = {}
    for part in case["parts"]:
        for kind, text in part["blocks"]:
            if kind in SCORED_FIELDS:
                spans.setdefault(kind, text)

    fields = {}
    for f in SCORED_FIELDS:
        spec = case["fields"].get(f)
        if spec is None:
            fields[f] = {"present_in_source": False, "value": None,
                         "normalized": None, "source_span": None,
                         "extra": {"why_absent": case.get("absent_notes", {}).get(f, "")}}
            continue
        value, normalized = spec["value"], spec["normalized"]
        span = spec.get("span") or spans.get(f)
        fields[f] = {"present_in_source": True, "value": value,
                     "normalized": normalized, "source_span": span,
                     "extra": spec.get("extra", {})}

    gold = {
        "case_id": case["id"],
        "format": case["format"],
        "corpus": "v2",
        "sources": [{"path": p["path"], "role": p["role"], "kind": p["kind"]}
                    for p in case["parts"]],
        "fields": fields,
        "construction_window": case.get("construction_window"),
    }
    if case.get("traps"):
        gold["traps"] = case["traps"]
    return gold


def derive_triage(gold: dict, profile: dict) -> dict:
    """Identical rules to v1, applied to v2 gold."""
    from evals.harness.normalize import TRADE_VOCAB
    f = gold["fields"]
    miles = profile["declared_drive_miles_from_base"]
    out_of_scope = set(profile["trade_fit"]["out_of_scope"])
    band = profile["size_band_usd"]
    cap = profile["capacity"]["max_concurrent_projects"]

    missing, crit = [], {}
    trades = f["trade_scope"]["normalized"]
    if trades is None:
        missing.append("trade_scope")
    else:
        crit["trade_fit"] = not (set(trades) & out_of_scope) and set(trades) <= TRADE_VOCAB

    loc = f["location"]["value"]
    if loc is None:
        missing.append("location")
    else:
        if loc not in miles:
            raise SystemExit("%s: location %r missing from profile distance table"
                             % (gold["case_id"], loc))
        crit["within_radius"] = miles[loc] <= profile["service_radius_miles"]

    val = f["estimated_project_value"]["normalized"]
    if val is None:
        missing.append("estimated_project_value")
    else:
        mid = (val["low"] + val["high"]) / 2
        crit["size_band_ok"] = band["min"] <= mid <= band["max"]

    win = gold.get("construction_window")
    if win is None:
        missing.append("construction_window")
    else:
        s, e = date.fromisoformat(win[0]), date.fromisoformat(win[1])
        conflict, d = False, s
        while d <= e:
            active = sum(1 for c in profile["committed_projects"]
                         if date.fromisoformat(c["start"]) <= d <= date.fromisoformat(c["end"]))
            if active >= cap:
                conflict = True
                break
            d = date.fromordinal(d.toordinal() + 1)
        crit["timeline_conflict"] = conflict

    if missing:
        return {"decision": "insufficient_information", "criteria": crit,
                "required_reasons": sorted(missing)}
    failing = []
    for key, bad in (("trade_fit", False), ("within_radius", False),
                     ("size_band_ok", False)):
        if crit[key] is bad:
            failing.append(key)
    if crit["timeline_conflict"]:
        failing.append("timeline_conflict")
    if failing:
        return {"decision": "no_bid", "criteria": crit, "required_reasons": failing}
    return {"decision": "bid", "criteria": crit,
            "required_reasons": ["trade_fit", "size_band_ok"]}


# --------------------------------------------------------------------------

def main() -> int:
    sys.path.insert(0, str(ROOT))
    from data.v2.cases import CASES
    from evals.harness.normalize import TRADE_VOCAB, normalize_field

    for d in (EMAILS, PDFS, SRC, GOLD):
        d.mkdir(parents=True, exist_ok=True)
    profile = json.loads((ROOT / "data" / "contractor_profile.json").read_text(encoding="utf-8"))

    failures, rows = [], []
    for case in CASES:
        texts = []
        for part in case["parts"]:
            target = ROOT / part["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if part["kind"] == "email":
                text = render_email(case, part)
                target.write_text(text, encoding="utf-8", newline="\n")
            else:
                render_pdf(case, part, target)
                text = pdf_text(target)
            texts.append((part, text))

        # Canonical per-part text, named the way documents.assemble expects.
        n = len(texts)
        for idx, (part, text) in enumerate(texts, 1):
            name = case["id"] if n == 1 else "%s_%d" % (case["id"], idx)
            (SRC / (name + ".txt")).write_text(text, encoding="utf-8", newline="\n")

        gold = build_gold(case, "")
        from evals.harness.documents import assemble
        assembled, manifest = assemble(case["id"], gold)
        gold["source_manifest"] = manifest

        # Property 1: every span must be recoverable from what the model sees.
        flat = ws(assembled)
        for fname, fval in gold["fields"].items():
            span = fval["source_span"]
            if fval["present_in_source"] and not span:
                failures.append("%s.%s: present but no span" % (case["id"], fname))
            elif span and ws(span) not in flat:
                failures.append("%s.%s: span not found -> %r"
                                % (case["id"], fname, ws(span)[:60]))
            if fname == "trade_scope" and fval["normalized"]:
                bad = set(fval["normalized"]) - TRADE_VOCAB
                if bad:
                    failures.append("%s.trade_scope: outside vocabulary %s"
                                    % (case["id"], sorted(bad)))

        # Property 2: gold normalized must be reproducible by the scorer's own
        # normalizer, for every field where re-derivation is defined.
        for fname, fval in gold["fields"].items():
            if fname == "bond_insurance" or not fval["present_in_source"]:
                continue
            red = normalize_field(fname, fval["value"])
            if red != fval["normalized"]:
                failures.append("%s.%s: normalized not reproducible (authored=%r, got=%r)"
                                % (case["id"], fname, fval["normalized"], red))

        gold["triage"] = derive_triage(gold, profile)
        (GOLD / (case["id"] + ".json")).write_text(
            json.dumps(gold, indent=2) + "\n", encoding="utf-8", newline="\n")

        n_absent = sum(1 for v in gold["fields"].values() if not v["present_in_source"])
        rows.append((case["id"], case["format"], n, 8 - n_absent, n_absent,
                     gold["triage"]["decision"]))

    print("%-10s %-26s %5s %8s %7s  %s"
          % ("CASE", "FORMAT", "PARTS", "PRESENT", "ABSENT", "TRIAGE"))
    print("-" * 88)
    tp = ta = 0
    for r in rows:
        print("%-10s %-26s %5d %8d %7d  %s" % r)
        tp += r[3]
        ta += r[4]
    print("-" * 88)
    print("%-10s %-26s %5s %8d %7d   (total slots: %d)"
          % ("TOTAL", "%d cases" % len(rows), "", tp, ta, tp + ta))

    if failures:
        print("\nVALIDATION FAILURES (%d):" % len(failures), file=sys.stderr)
        for f in failures[:40]:
            print("  - " + f, file=sys.stderr)
        return 1
    print("\nAll v2 gold spans verified against the assembled document text.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
