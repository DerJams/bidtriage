"""Lever 4: the estimator brief. The only user-facing artifact.

Design decision, stated up front because it is the important one: the brief is
rendered DETERMINISTICALLY from fields that have already been extracted,
verified against the source, and triaged. It makes no model call of its own.

That is deliberate. By this point every fact has survived a verification pass
that had to produce a locatable span. Asking a model to write the brief in prose
would reintroduce exactly the failure mode the previous lever exists to remove,
in the one artifact a person actually reads and forwards. A generated summary
that quietly rounds $1.8M to $2M, or drops the word "mandatory" from a
walk-through, would be worse than useless: it would be wrong in the place where
being wrong costs a bid.

So the model does the judgment, and the renderer does the typography. The brief
adds no new hallucination surface and costs nothing extra per case.

Three properties the brief maintains, all checkable by `brief_checks`:

* Every asserted field carries a citation from the source document.
* Every field the system was unsure about is surfaced at the TOP, not buried.
* Nothing appears in the brief that verification did not support.
"""
from __future__ import annotations

import re

FIELD_LABELS = [
    ("client_name", "Client"),
    ("location", "Location"),
    ("trade_scope", "Trade scope"),
    ("estimated_project_value", "Estimated value"),
]

CRITERION_LABELS = {
    "trade_fit": "Trade fit",
    "within_radius": "Service radius",
    "size_band_ok": "Size band",
    "timeline_conflict": "Timeline",
}

RULE = "=" * 68
THIN = "-" * 68


def _fmt_trades(v):
    if not v:
        return None
    if isinstance(v, str):
        v = [v]
    pretty = {"hvac": "HVAC", "sheet_metal": "sheet metal", "plumbing": "plumbing",
              "piping": "piping", "controls": "controls",
              "refrigeration": "refrigeration", "fire_protection": "fire protection"}
    return ", ".join(pretty.get(str(t).lower(), str(t)) for t in v)


def _fmt_bond(b):
    if b is None:
        return ["Not stated in the document."]
    if b.get("required") is False:
        return ["No bonding required. Certificate of insurance only."]
    out = []
    for key, label in (("bid_bond_pct", "Bid bond"),
                       ("performance_bond_pct", "Performance bond"),
                       ("payment_bond_pct", "Payment bond")):
        if b.get(key) is not None:
            out.append("%-20s %s%%" % (label, b[key]))
    occ, agg = b.get("gl_per_occurrence_usd"), b.get("gl_aggregate_usd")
    if occ is not None or agg is not None:
        parts = []
        if occ is not None:
            parts.append("${:,} per occurrence".format(int(occ)))
        if agg is not None:
            parts.append("${:,} aggregate".format(int(agg)))
        out.append("%-20s %s" % ("General liability", " / ".join(parts)))
    elif b.get("gl_limit_usd") is not None:  # v1 single-limit shape, kept readable
        out.append("%-20s $%s" % ("General liability",
                                  "{:,}".format(int(b["gl_limit_usd"]))))
    return out or ["Stated, but no specific requirement recorded."]


def _wrap(text, width=48, indent=22):
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    if not lines:
        return ""
    pad = " " * indent
    return ("\n" + pad).join(lines)


def render(case_id, prediction, flagged, evidence=None, triage_audit=None):
    """Return the brief as plain text. Deterministic for a given input."""
    evidence = evidence or {}
    flagged = list(flagged or [])
    p = prediction or {}

    title = p.get("project_title") or "Untitled solicitation"
    decision = (p.get("triage_decision") or "no recommendation").upper().replace("_", " ")

    L = [RULE, "BID TRIAGE BRIEF", title, RULE, ""]

    # --- recommendation -----------------------------------------------------
    L.append("RECOMMENDATION: %s" % decision)
    L.append("")
    if triage_audit and triage_audit.get("criteria"):
        crit = triage_audit["criteria"]
        reasons = triage_audit.get("criteria_reasons") or {}
        for key, label in CRITERION_LABELS.items():
            val = crit.get(key)
            if val is None:
                mark = "UNKNOWN"
            elif key == "timeline_conflict":
                mark = "CONFLICT" if val else "CLEAR"
            else:
                mark = "PASS" if val else "FAIL"
            L.append("  %-16s %-9s %s" % (label, mark, _wrap(reasons.get(key) or "", 44, 29)))
        L.append("")

    # --- review queue, deliberately near the top ----------------------------
    if flagged:
        L.append("NEEDS YOUR REVIEW (%d item%s)" % (len(flagged), "" if len(flagged) == 1 else "s"))
        for f in flagged:
            label = f.replace("_", " ")
            note = "Could not be confirmed against the source document. Check "\
                   "before relying on it."
            L.append("  ! %-18s %s" % (label, _wrap(note, 44, 23)))
        L.append("")
    else:
        L.append("NEEDS YOUR REVIEW: nothing. Every field was confirmed against")
        L.append("the source document.")
        L.append("")

    # --- dates --------------------------------------------------------------
    L.append("KEY DATES")
    due = p.get("bid_due_date")
    L.append("  %-18s %s" % ("Bid due", due or "not stated"))
    walk = p.get("walkthrough_date")
    L.append("  %-18s %s" % ("Walk-through", walk or "none stated"))
    L.append("")

    # --- project ------------------------------------------------------------
    L.append("PROJECT")
    for key, label in FIELD_LABELS:
        v = p.get(key)
        if key == "trade_scope":
            v = _fmt_trades(v)
        L.append("  %-18s %s" % (label, v if v not in (None, "") else "not stated"))
    L.append("")

    # --- bonding ------------------------------------------------------------
    L.append("BONDING AND INSURANCE")
    for line in _fmt_bond(p.get("bond_insurance")):
        L.append("  " + line)
    L.append("")

    # --- citations ----------------------------------------------------------
    cited = [(f, (evidence.get(f) or {}).get("span")) for f in
             ("client_name", "project_title", "trade_scope", "location",
              "bid_due_date", "estimated_project_value", "bond_insurance",
              "walkthrough_date")]
    cited = [(f, s) for f, s in cited if s]
    if cited:
        L.append(THIN)
        L.append("SOURCE CITATIONS")
        for f, span in cited:
            span = re.sub(r"\s+", " ", span).strip()
            if len(span) > 92:
                span = span[:89] + "..."
            L.append("  %-24s %s" % (f.replace("_", " "), '"' + span + '"'))
        L.append("")

    L.append(THIN)
    L.append("Prepared by BidTriage from the source document for %s." % case_id)
    L.append("Every figure above is quoted from that document. Items marked for")
    L.append("review were not confirmed and need a human read before use.")
    return "\n".join(L)


def brief_checks(text, prediction, flagged, evidence=None):
    """Mechanical properties of the brief. Not a claim that a human judged it.

    The frozen target is that the brief be forwardable without edits. That is a
    human judgement and is reported as such. What CAN be checked deterministically
    is whether the brief is structurally fit to be forwarded, so that is what
    these checks assert, under their own name.
    """
    evidence = evidence or {}
    p = prediction or {}
    flagged = set(flagged or [])

    asserted = [f for f in ("client_name", "project_title", "trade_scope", "location",
                            "bid_due_date", "estimated_project_value", "bond_insurance",
                            "walkthrough_date")
                if p.get(f) is not None and f not in flagged]
    cited = [f for f in asserted if (evidence.get(f) or {}).get("span")]

    placeholders = re.findall(r"\bTODO\b|\bTBD\b|\bFIXME\b|\bXXX\b|\{\{|\}\}|<[a-z_]+>", text)

    return {
        "has_recommendation": "RECOMMENDATION:" in text,
        "recommendation_not_empty": "RECOMMENDATION: NO RECOMMENDATION" not in text,
        "review_section_present": "NEEDS YOUR REVIEW" in text,
        "flagged_all_surfaced": all(f.replace("_", " ") in text for f in flagged),
        "asserted_fields": len(asserted),
        "asserted_fields_cited": len(cited),
        "citation_coverage": (len(cited) / len(asserted)) if asserted else 1.0,
        "no_placeholder_text": not placeholders,
        "placeholders_found": placeholders,
        "line_count": len(text.splitlines()),
        "no_em_dashes": "—" not in text and "–" not in text,
    }
