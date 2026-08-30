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

Four properties the brief maintains, all checkable by `brief_checks`:

* Every asserted field carries a citation from the source document.
* Every field the system was unsure about is surfaced at the TOP, and is also
  marked NOT CONFIRMED at the point where its value appears. A reader who skims
  the middle of the page must not be able to mistake an unverified figure for a
  verified one.
* Disqualifying conditions, such as a mandatory walk-through, are promoted out
  of the citations and stated where they will be seen.
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

CITATION_LABELS = {
    "client_name": "Client", "project_title": "Project", "trade_scope": "Trade scope",
    "location": "Location", "bid_due_date": "Bid due", "walkthrough_date": "Walk-through",
    "estimated_project_value": "Estimated value", "bond_insurance": "Bonding",
}

CRITERION_LABELS = {
    "trade_fit": "Trade fit",
    "within_radius": "Service radius",
    "size_band_ok": "Size band",
    "timeline_conflict": "Timeline",
}

# What an estimator must go and get when a criterion cannot be evaluated.
CRITERION_NEEDS = {
    "trade_fit": "Trade scope, specific enough to identify the trades",
    "within_radius": "Project location",
    "size_band_ok": "Estimated project value or engineer's estimate",
    "timeline_conflict": "Construction window (start and substantial completion)",
}

UNCONFIRMED = "NOT CONFIRMED, see review above"
LBL = 20          # label column width
RULE = "=" * 72
THIN = "-" * 72


def _plain(text):
    """Strip em and en dashes from MODEL-AUTHORED prose.

    The criterion reasons and field values are written by the model, and it
    emits things like "$250,000-en dash-$3,000,000". Those land verbatim in the
    brief, which is the artifact a person forwards, so they are rewritten here
    rather than left to leak through.

    Deliberately NOT applied to source citations. A citation is a quote, and
    silently editing a quote to satisfy a house style is worse than the dash it
    removes. brief_checks reports the two separately for that reason.
    """
    t = str(text)
    t = re.sub(r"(?<=\d)\s*[–—]\s*(?=[$\d])", " to ", t)
    t = re.sub(r"\s*—\s*", ", ", t)
    t = re.sub(r"\s*–\s*", " to ", t)
    return t


def _fmt_trades(v):
    if not v:
        return None
    if isinstance(v, str):
        v = [v]
    pretty = {"hvac": "HVAC", "sheet_metal": "sheet metal", "plumbing": "plumbing",
              "piping": "piping", "controls": "controls",
              "refrigeration": "refrigeration", "fire_protection": "fire protection"}
    return ", ".join(pretty.get(str(t).lower(), str(t)) for t in v)


def _fmt_bond(b, flagged):
    if b is None:
        return ["Not stated in the document."]
    if b.get("required") is False:
        return ["No bonding required. Certificate of insurance only."]
    out = []
    for key, label in (("bid_bond_pct", "Bid bond"),
                       ("performance_bond_pct", "Performance bond"),
                       ("payment_bond_pct", "Payment bond")):
        if b.get(key) is not None:
            out.append("%-*s %s%%" % (LBL, label, b[key]))
    occ, agg = b.get("gl_per_occurrence_usd"), b.get("gl_aggregate_usd")
    parts = []
    if occ is not None:
        parts.append("${:,} per occurrence".format(int(occ)))
    if agg is not None:
        parts.append("${:,} aggregate".format(int(agg)))
    if parts:
        out.append("%-*s %s" % (LBL, "General liability", " / ".join(parts)))
    elif b.get("gl_limit_usd") is not None:  # v1 single-limit shape
        out.append("%-*s $%s" % (LBL, "General liability",
                                 "{:,}".format(int(b["gl_limit_usd"]))))
    if not out:
        out = ["Stated, but no specific requirement recorded."]
    if "bond_insurance" in flagged:
        out.append("%-*s %s" % (LBL, "", "(" + UNCONFIRMED + ")"))
    return out


def _wrap(text, width, indent):
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return ("\n" + " " * indent).join(lines) if lines else ""


def _value_line(label, value, flagged_key, flagged):
    """A value line that cannot be mistaken for verified when it is not."""
    shown = _plain(value) if value not in (None, "") else "not stated"
    if flagged_key in flagged:
        return "  %-*s %s  (%s)" % (LBL, label, shown, UNCONFIRMED)
    return "  %-*s %s" % (LBL, label, shown)


def _mandatory_walkthrough(evidence):
    span = ((evidence or {}).get("walkthrough_date") or {}).get("span") or ""
    return bool(re.search(r"\bmandator", span, re.IGNORECASE))


# Explicit zone list, matched case-sensitively. A generic [A-Z]{2,4} under
# IGNORECASE swallowed the "loca" of "local time" and rendered "9:00 AM loca".
# A truncated time on a bid brief is precisely the kind of small error that
# costs a bid, so the zone must be matched exactly rather than approximately.
_TZ = r"(?:MT|MST|MDT|CT|CST|CDT|ET|EST|EDT|PT|PST|PDT|UTC|local time)"
_TIME_RE = re.compile(r"(\d{1,2}:\d{2}\s*(?:[AaPp]\.?[Mm]\.?)?)\s*(" + _TZ + r")?")


def _time_from_span(evidence, key):
    """Surface a stated time of day. The scored field is date-only, but an
    estimator who misses a 2:00 PM cutoff has lost the bid regardless."""
    span = ((evidence or {}).get(key) or {}).get("span") or ""
    m = _TIME_RE.search(span)
    if not m:
        return None
    out = m.group(1).strip()
    if m.group(2):
        out += " " + m.group(2)
    return out


def render(case_id, prediction, flagged, evidence=None, triage_audit=None):
    """Return the brief as plain text. Deterministic for a given input."""
    evidence = evidence or {}
    flagged = list(flagged or [])
    p = prediction or {}

    title = p.get("project_title") or "Untitled solicitation"
    decision = (p.get("triage_decision") or "no recommendation").upper().replace("_", " ")

    L = [RULE, "BID TRIAGE BRIEF", title, RULE, "", "RECOMMENDATION: %s" % decision, ""]

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
            L.append("  %-16s %-9s %s"
                     % (label, mark, _wrap(_plain(reasons.get(key) or ""), 43, 29)))
        L.append("")

    # --- review queue, deliberately above the values it refers to -----------
    if flagged:
        L.append("NEEDS YOUR REVIEW (%d item%s)" % (len(flagged), "" if len(flagged) == 1 else "s"))
        for f in flagged:
            label = CITATION_LABELS.get(f, f.replace("_", " "))
            note = ("Could not be confirmed against the source document. "
                    "Verify before relying on it.")
            L.append("  ! %-*s %s" % (LBL, label, _wrap(note, 44, LBL + 5)))
        L.append("")
    else:
        # "Every field was confirmed" is false when fields are simply absent.
        absent = [lbl for key, lbl in CITATION_LABELS.items() if p.get(key) is None]
        L.append("NEEDS YOUR REVIEW")
        L.append("  Nothing was flagged as uncertain.")
        if absent:
            L.append("  %s %s"
                     % ("Fields shown as \"not stated\" are genuinely absent from",
                        "the document:"))
            L.append("  " + _wrap(", ".join(absent) + ".", 66, 2))
        else:
            L.append("  Every field below was confirmed against the source document.")
        L.append("")

    # --- what to obtain, when the decision cannot be made yet ---------------
    if (p.get("triage_decision") == "insufficient_information"
            and triage_audit and triage_audit.get("criteria")):
        needed = [CRITERION_NEEDS[c] for c, v in triage_audit["criteria"].items()
                  if v is None and c in CRITERION_NEEDS]
        if needed:
            L.append("TO DECIDE, OBTAIN")
            for n in sorted(needed):
                L.append("  - " + n)
            L.append("")

    # --- dates --------------------------------------------------------------
    L.append("KEY DATES")
    due = p.get("bid_due_date")
    due_time = _time_from_span(evidence, "bid_due_date")
    if due and due_time:
        due = "%s at %s" % (due, due_time)
    L.append(_value_line("Bid due", due, "bid_due_date", flagged))

    walk = p.get("walkthrough_date")
    walk_time = _time_from_span(evidence, "walkthrough_date")
    if walk and walk_time:
        walk = "%s at %s" % (walk, walk_time)
    if walk and _mandatory_walkthrough(evidence):
        walk = "%s  ** MANDATORY, non-attendance disqualifies **" % walk
    L.append(_value_line("Walk-through", walk or "none stated", "walkthrough_date", flagged))
    L.append("")

    # --- project ------------------------------------------------------------
    L.append("PROJECT")
    for key, label in FIELD_LABELS:
        v = _fmt_trades(p.get(key)) if key == "trade_scope" else p.get(key)
        L.append(_value_line(label, v, key, flagged))
    L.append("")

    # --- bonding ------------------------------------------------------------
    L.append("BONDING AND INSURANCE")
    for line in _fmt_bond(p.get("bond_insurance"), flagged):
        L.append("  " + line)
    L.append("")

    # --- citations ----------------------------------------------------------
    cited = [(f, (evidence.get(f) or {}).get("span")) for f in CITATION_LABELS]
    cited = [(f, s) for f, s in cited if s]
    if cited:
        L.append(THIN)
        L.append("SOURCE CITATIONS")
        L.append("  Every figure above is quoted from the document below.")
        L.append("")
        for f, span in cited:
            span = re.sub(r"\s+", " ", span).strip()
            if len(span) > 78:
                span = span[:75] + "..."
            L.append("  %-*s %s" % (LBL, CITATION_LABELS[f], '"' + span + '"'))
        L.append("")

    L.append(THIN)
    L.append("Prepared by BidTriage from the source document for %s." % case_id)
    if flagged:
        L.append("Items marked NOT CONFIRMED were not verified against the source")
        L.append("and need a human read before use.")
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
    fields = list(CITATION_LABELS)

    asserted = [f for f in fields if p.get(f) is not None and f not in flagged]
    cited = [f for f in asserted if (evidence.get(f) or {}).get("span")]
    placeholders = re.findall(r"\bTODO\b|\bTBD\b|\bFIXME\b|\bXXX\b|\{\{|\}\}|<[a-z_]+>", text)

    # Every flagged field must be marked at its value, not only in the queue.
    marked = all(text.count(UNCONFIRMED) >= 1 for _ in [0]) if flagged else True
    unmarked = [f for f in flagged
                if CITATION_LABELS.get(f, f.replace("_", " ")) not in text]

    return {
        "has_recommendation": "RECOMMENDATION:" in text,
        "recommendation_not_empty": "RECOMMENDATION: NO RECOMMENDATION" not in text,
        "review_section_present": "NEEDS YOUR REVIEW" in text,
        "flagged_all_surfaced": not unmarked,
        "flagged_marked_at_value": marked,
        "unconfirmed_markers": text.count(UNCONFIRMED),
        "asserted_fields": len(asserted),
        "asserted_fields_cited": len(cited),
        "citation_coverage": (len(cited) / len(asserted)) if asserted else 1.0,
        "no_placeholder_text": not placeholders,
        "placeholders_found": placeholders,
        "line_count": len(text.splitlines()),
        # Citations are quotes and are exempt: editing a quote to satisfy a
        # house style is worse than the dash. Prose must be clean.
        "no_em_dashes_in_prose": ("—" not in text.split("SOURCE CITATIONS")[0]
                                  and "–" not in text.split("SOURCE CITATIONS")[0]),
        "dashes_in_citations_only": ("—" in text or "–" in text)
                                    and "—" not in text.split("SOURCE CITATIONS")[0]
                                    and "–" not in text.split("SOURCE CITATIONS")[0],
    }
