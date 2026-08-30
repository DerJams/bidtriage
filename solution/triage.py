"""Lever 3: structured triage against explicit capacity criteria.

The baseline and lever 2 are told the contractor's constraints in a paragraph
of prose. Both get case_06 wrong essentially every run: its construction window
(2026-11-01 to 2027-02-28) overlaps the period where all three committed
projects are already running, so the honest answer is no_bid on a timeline
conflict. Prose does not make that evaluable, so neither arm evaluates it.

This lever renders `data/contractor_profile.json` into criteria the model can
actually check, and asks it to evaluate each one and say why.

On not scoring the gold generator against itself
------------------------------------------------
Gold triage is DERIVED by `derive_triage()` in `evals/author_gold.py`. Porting
that computation into the solution would score my own generator against itself
and return a meaningless ~100%. So the work is split:

* The MODEL evaluates the four criteria. That is the judgment: find the
  construction window in the document, decide whether it overlaps a period that
  is already at capacity, look the site up in the distance table, decide whether
  the trades are ones the contractor self-performs.
* CODE applies the boolean formula to whatever the model concluded. That part is
  trivial and is published in the profile itself.

The raw model decision is recorded alongside the rule-applied one, so how much
each contributed is visible rather than assumed.

The derived at-capacity window is deliberately NOT precomputed for the model.
It is given the three committed projects and the concurrency limit and has to
work the overlap out, because that is the actual reasoning being tested.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILE = json.loads((ROOT / "data" / "contractor_profile.json").read_text(encoding="utf-8"))

DECISIONS = ["bid", "no_bid", "insufficient_information"]
CRITERIA = ["trade_fit", "within_radius", "size_band_ok", "timeline_conflict"]

# Which extracted input each criterion needs. Used only to report an
# insufficient_information decision in the same vocabulary gold uses.
CRITERION_INPUT = {
    "trade_fit": "trade_scope",
    "within_radius": "location",
    "size_band_ok": "estimated_project_value",
    "timeline_conflict": "construction_window",
}


def render_criteria() -> str:
    """The profile as something checkable, not as a paragraph of prose."""
    p = PROFILE
    miles = p["declared_drive_miles_from_base"]
    table = "\n".join("    %-24s %4d miles" % (k, v) for k, v in sorted(miles.items()))
    committed = "\n".join(
        "    %-46s %s to %s" % (c["name"], c["start"], c["end"])
        for c in p["committed_projects"])

    return """CONTRACTOR CAPACITY CRITERIA for %s (home base %s)

Evaluate all four criteria. For each one answer true or false and give a short
reason citing the specific figures you used.

CRITERION 1: trade_fit
  Self-performed trades: %s
  NOT self-performed:    %s
  trade_fit is TRUE only if every required trade is self-performed. If any
  required trade is in the not-self-performed list, trade_fit is FALSE.

CRITERION 2: within_radius
  Service radius: %d miles from %s.
  Declared drive distances (use this table, do not estimate distances):
%s
  within_radius is TRUE if the project's location is at or under the radius.

CRITERION 3: size_band_ok
  Accepted project size: $%s to $%s.
  Use the MIDPOINT of the estimated value. If the estimate is a range, the
  midpoint is (low + high) / 2. size_band_ok is TRUE if that midpoint falls
  inside the band, inclusive.

CRITERION 4: timeline_conflict
  Maximum concurrent projects: %d.
  Already committed:
%s
  Work out the periods during which %d projects are ALREADY running at once.
  A new project conflicts if its construction window overlaps any part of such
  a period, even by one day. timeline_conflict is TRUE when it overlaps.
  Take the construction window from the document. It is usually given as a
  construction start date and a substantial completion date. If the document
  does not state a construction window, set timeline_conflict to null.

DECISION RULE
  If any criterion cannot be evaluated because the document does not state what
  it needs, set that criterion to null and the decision to
  insufficient_information.
  Otherwise the decision is "bid" only when trade_fit AND within_radius AND
  size_band_ok are all true AND timeline_conflict is false.
  Otherwise the decision is "no_bid", and every failing criterion is a reason.
""" % (
        p["company"], p["home_base"],
        ", ".join(p["trade_fit"]["in_scope"]),
        ", ".join(p["trade_fit"]["out_of_scope"]),
        p["service_radius_miles"], p["home_base"], table,
        "{:,}".format(p["size_band_usd"]["min"]),
        "{:,}".format(p["size_band_usd"]["max"]),
        p["capacity"]["max_concurrent_projects"], committed,
        p["capacity"]["max_concurrent_projects"],
    )


_criterion_obj = {
    "type": "object",
    "additionalProperties": False,
    "required": ["value", "reason"],
    "properties": {
        "value": {"type": ["boolean", "null"],
                  "description": "null only if the document does not state what "
                                 "this criterion needs."},
        "reason": {"type": "string",
                   "description": "One sentence citing the specific figures used."},
    },
}

TRIAGE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["construction_window", "criteria", "decision", "reasons"],
    "properties": {
        "construction_window": {
            "type": "object",
            "additionalProperties": False,
            "required": ["start", "end"],
            "properties": {
                "start": {"type": ["string", "null"], "description": "ISO YYYY-MM-DD or null."},
                "end": {"type": ["string", "null"], "description": "ISO YYYY-MM-DD or null."},
            },
        },
        "criteria": {
            "type": "object",
            "additionalProperties": False,
            "required": CRITERIA,
            "properties": {c: dict(_criterion_obj) for c in CRITERIA},
        },
        "decision": {"type": ["string", "null"], "enum": DECISIONS + [None]},
        "reasons": {"type": "array", "items": {"type": "string"}},
    },
}


def response_format(name: str = "bid_triage") -> dict:
    return {"type": "json_schema",
            "json_schema": {"name": name, "strict": True, "schema": TRIAGE_SCHEMA}}


def apply_rule(criteria: dict) -> tuple:
    """Apply the published boolean formula to the MODEL's own criterion values.

    This does not re-derive the criteria. It only combines them, which is the
    trivial half of the job and is written down in contractor_profile.json.
    Returns (decision, reasons).
    """
    vals = {c: (criteria.get(c) or {}).get("value") for c in CRITERIA}

    missing = sorted(c for c, v in vals.items() if v is None)
    if missing:
        # Gold names the missing INPUT for an insufficient_information decision,
        # not the criterion that could not be evaluated. Map to that convention
        # so reason recall compares like with like. This is naming alignment
        # only: it cannot change a decision, and the decision is already set.
        return "insufficient_information", sorted(CRITERION_INPUT[c] for c in missing)

    failing = []
    if not vals["trade_fit"]:
        failing.append("trade_fit")
    if not vals["within_radius"]:
        failing.append("within_radius")
    if not vals["size_band_ok"]:
        failing.append("size_band_ok")
    if vals["timeline_conflict"]:
        failing.append("timeline_conflict")

    if failing:
        return "no_bid", failing
    return "bid", ["trade_fit", "size_band_ok"]
