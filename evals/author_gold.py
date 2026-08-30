"""Author and validate the gold answer keys.

    python -m evals.author_gold

Two properties this script enforces, so the gold keys cannot quietly drift:

1. Every non-null `source_span` must appear VERBATIM (whitespace-normalized)
   in the case's extracted source text. A span that cannot be found is a hard
   failure, not a warning. This makes it impossible for a gold citation to be
   something I merely believed was in the document.

2. The triage decision is DERIVED from data/contractor_profile.json rather
   than hand-asserted, so gold triage cannot disagree with the stated rules.

Field values themselves are hand-authored -- they are the ground truth, and
something has to be. The span check is what keeps that honest.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import date

from evals.harness.normalize import normalize_field

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "synthetic" / "source_text"
OUT = ROOT / "evals" / "gold"
PROFILE = json.loads((ROOT / "data" / "contractor_profile.json").read_text(encoding="utf-8"))

TRADE_VOCAB = {"hvac", "plumbing", "piping", "sheet_metal", "controls",
               "refrigeration", "fire_protection"}


def ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def money(low, high=None):
    return {"low": low, "high": low if high is None else high, "currency": "USD"}


# --------------------------------------------------------------------------
# Field-level gold. `None` for a field means: not present in the source, and
# the correct model output is null.
# --------------------------------------------------------------------------
# Each entry: value, normalized, span  (and optional extra)

def F(value, normalized, span, extra=None):
    return {"present_in_source": True, "value": value, "normalized": normalized,
            "source_span": span, "extra": extra or {}}


def ABSENT(note):
    return {"present_in_source": False, "value": None, "normalized": None,
            "source_span": None, "extra": {"why_absent": note}}


GOLD = {
    "case_01": {
        "format": "email_rfp",
        "source": "data/synthetic/emails/case_01.eml",
        "fields": {
            "client_name": F("Cascade Ridge School District 12", "cascade ridge school district 12",
                             "Cascade Ridge School District 12 is soliciting competitive sealed bids"),
            "project_title": F("Cascade Ridge Middle School RTU Replacement",
                               "cascade ridge middle school rtu replacement",
                               "Cascade Ridge Middle School RTU Replacement project"),
            "trade_scope": F(["hvac", "sheet_metal", "controls"], ["controls", "hvac", "sheet_metal"],
                             "Trades required: HVAC, sheet metal, and controls."),
            "location": F("Arvada, CO", "arvada, co",
                          "Cascade Ridge Middle School, Arvada, CO."),
            "bid_due_date": F("September 25, 2026", "2026-09-25",
                              "Sealed bids are due no later than September 25, 2026 at 2:00 PM MT",
                              {"time_local": "14:00", "tz": "America/Denver"}),
            "estimated_project_value": F("$850,000", money(850000),
                                         "construction budget of $850,000"),
            "bond_insurance": F("5% bid bond; 100% performance and payment bonds; $2M GL",
                                {"required": True, "bid_bond_pct": 5, "performance_bond_pct": 100,
                                 "payment_bond_pct": 100, "gl_limit_usd": 2000000},
                                "A bid bond in the amount of 5% of the total bid is required with submission."),
            "walkthrough_date": F("September 11, 2026", "2026-09-11",
                                  "Mandatory pre-bid walk-through: September 11, 2026 at 9:00 AM local time."),
        },
        "construction_window": ["2027-02-15", "2027-07-30"],
    },
    "case_02": {
        "format": "email_rfp",
        "source": "data/synthetic/emails/case_02.eml",
        "fields": {
            "client_name": F("Bright Mesa Property Group", "bright mesa property group",
                             "Bright Mesa Property Group is looking for bids"),
            "project_title": F("Bright Mesa Commons Domestic Water Piping Retrofit",
                               "bright mesa commons domestic water piping retrofit",
                               "the Bright Mesa Commons Domestic Water Piping Retrofit"),
            "trade_scope": F(["plumbing", "piping"], ["piping", "plumbing"],
                             "Scope is plumbing and piping only - no HVAC, no controls."),
            "location": F("Boulder, CO", "boulder, co", "our Boulder, CO property"),
            "bid_due_date": F("September 18, 2026", "2026-09-18",
                              "Bids are due September 18, 2026."),
            "estimated_project_value": F("$310,000", money(310000),
                                         "Budget we're working with is $310,000."),
            "bond_insurance": F("No bonding required", {"required": False},
                                "this is a private project and we are not requiring any bonding on it"),
            "walkthrough_date": ABSENT("Source states no formal walk-through will be held; no date exists."),
        },
        "construction_window": ["2027-03-01", "2027-06-15"],
    },
    "case_03": {
        "format": "email_rfp_forwarded",
        "source": "data/synthetic/emails/case_03.eml",
        "fields": {
            "client_name": F("Verge Cold Chain Holdings", "verge cold chain holdings",
                             "Verge Cold Chain Holdings is issuing an invitation to bid"),
            "project_title": F("Larimer Street Cold Storage Buildout",
                               "larimer street cold storage buildout",
                               "the Larimer Street Cold Storage Buildout at our Denver, CO facility"),
            "trade_scope": F(["refrigeration", "piping", "hvac"], ["hvac", "piping", "refrigeration"],
                             "Trades required: refrigeration, piping, HVAC."),
            "location": F("Denver, CO", "denver, co",
                          "at our Denver, CO facility"),
            "bid_due_date": F("September 30, 2026", "2026-09-30",
                              "Bids close September 30, 2026."),
            "estimated_project_value": F("$700,000", money(700000),
                                         "Engineer's estimate is $700,000."),
            "bond_insurance": F("5% bid bond; 100% performance and payment bonds; $1M GL",
                                {"required": True, "bid_bond_pct": 5, "performance_bond_pct": 100,
                                 "payment_bond_pct": 100, "gl_limit_usd": 1000000},
                                "Bonding: bid bond at 5%, performance and payment bonds at 100% each. GL limit $1,000,000."),
            "walkthrough_date": F("September 14, 2026", "2026-09-14",
                                  "Site walk is set for September 14, 2026."),
        },
        "construction_window": ["2027-04-05", "2027-08-20"],
    },
    "case_04": {
        "format": "email_rfp",
        "source": "data/synthetic/emails/case_04.eml",
        "fields": {
            "client_name": F("Mesa Verdana Industrial Partners", "mesa verdana industrial partners",
                             "Aurelio Nakashima-Prather\nMesa Verdana Industrial Partners"),
            "project_title": F("Mesa Verdana Industrial Park Building C",
                               "mesa verdana industrial park building c",
                               "the mechanical package for Mesa Verdana Industrial Park\nBuilding C"),
            "trade_scope": F(["hvac", "controls"], ["controls", "hvac"],
                             "Scope: HVAC and controls."),
            "location": F("Grand Junction, CO", "grand junction, co",
                          "Building C in Grand Junction, CO."),
            "bid_due_date": F("September 22, 2026", "2026-09-22", "Bids due: September 22, 2026."),
            "estimated_project_value": F("$480,000", money(480000), "Estimated value: $480,000."),
            "bond_insurance": F("5% bid bond; 100% performance and payment bonds; $2M GL",
                                {"required": True, "bid_bond_pct": 5, "performance_bond_pct": 100,
                                 "payment_bond_pct": 100, "gl_limit_usd": 2000000},
                                "Bonding requirements are bid bond 5%, performance bond 100%, payment bond 100%."),
            "walkthrough_date": F("September 8, 2026", "2026-09-08",
                                  "Walk-through: September 8, 2026, 10:00 AM."),
        },
        "construction_window": ["2027-01-11", "2027-05-28"],
    },
    "case_05": {
        "format": "email_rfp_tabular",
        "source": "data/synthetic/emails/case_05.eml",
        "fields": {
            "client_name": F("Helioptix Data Infrastructure", "helioptix data infrastructure",
                             "Issuing entity ......... Helioptix Data Infrastructure"),
            "project_title": F("Helioptix Data Campus Phase II", "helioptix data campus phase ii",
                               "Project ................ Helioptix Data Campus Phase II"),
            "trade_scope": F(["hvac", "piping", "sheet_metal", "controls"],
                             ["controls", "hvac", "piping", "sheet_metal"],
                             "Trades required ...... HVAC, piping, sheet metal, controls"),
            "location": F("Denver, CO", "denver, co", "Site ................... Denver, CO"),
            "bid_due_date": F("October 9, 2026", "2026-10-09",
                              "Bid due date ......... October 9, 2026, 4:00 PM MT",
                              {"time_local": "16:00", "tz": "America/Denver"}),
            "estimated_project_value": F("$4,500,000", money(4500000),
                                         "Engineer's estimate .. $4,500,000"),
            "bond_insurance": F("5% bid bond; 100% performance and payment bonds; $5M GL",
                                {"required": True, "bid_bond_pct": 5, "performance_bond_pct": 100,
                                 "payment_bond_pct": 100, "gl_limit_usd": 5000000},
                                "Bid bond ............. 5% of base bid"),
            "walkthrough_date": F("September 17, 2026", "2026-09-17",
                                  "Pre-bid walk-through . September 17, 2026"),
        },
        "construction_window": ["2027-03-22", "2027-12-18"],
    },
    "case_06": {
        "format": "pdf_rfp",
        "source": "data/synthetic/pdfs/case_06.pdf",
        "fields": {
            "client_name": F("Larkspur Civic Development Authority", "larkspur civic development authority",
                             "Owner Larkspur Civic Development Authority"),
            "project_title": F("Larkspur Civic Center Annex Mechanical Package",
                               "larkspur civic center annex mechanical package",
                               "Project Larkspur Civic Center Annex Mechanical Package"),
            "trade_scope": F(["hvac", "controls"], ["controls", "hvac"],
                             "Trades Required HVAC and controls"),
            "location": F("Denver, CO", "denver, co", "Project Location Denver, CO"),
            "bid_due_date": F("September 29, 2026", "2026-09-29",
                              "Bid due September 29, 2026 at 2:00 PM MT",
                              {"time_local": "14:00", "tz": "America/Denver"}),
            "estimated_project_value": F("$1,200,000", money(1200000),
                                         "Engineer's estimate $1,200,000"),
            "bond_insurance": F("5% bid bond; 100% performance and payment bonds; $2M GL",
                                {"required": True, "bid_bond_pct": 5, "performance_bond_pct": 100,
                                 "payment_bond_pct": 100, "gl_limit_usd": 2000000},
                                "Bid bond 5% of total base bid"),
            "walkthrough_date": F("September 15, 2026", "2026-09-15",
                                  "Pre-bid walk-through September 15, 2026 at 8:30 AM"),
        },
        "construction_window": ["2026-11-01", "2027-02-28"],
    },
    "case_07": {
        "format": "pdf_rfp",
        "source": "data/synthetic/pdfs/case_07.pdf",
        "fields": {
            "client_name": F("Cache La Poudre Community College District",
                             "cache la poudre community college district",
                             "Owner Cache La Poudre Community College District"),
            "project_title": F("Science Building HVAC Modernization",
                               "science building hvac modernization",
                               "Project Science Building HVAC Modernization"),
            "trade_scope": F(["hvac", "sheet_metal", "controls"], ["controls", "hvac", "sheet_metal"],
                             "Trades Required HVAC, sheet metal, and controls"),
            "location": F("Fort Collins, CO", "fort collins, co", "Project Location Fort Collins, CO"),
            "bid_due_date": F("October 20, 2026", "2026-10-20",
                              "Bid due October 20, 2026 at 3:00 PM MT",
                              {"time_local": "15:00", "tz": "America/Denver"}),
            "estimated_project_value": F("$1,400,000", money(1400000),
                                         "Engineer's estimate $1,400,000"),
            "bond_insurance": F("5% bid bond; 100% performance and payment bonds; $3M GL",
                                {"required": True, "bid_bond_pct": 5, "performance_bond_pct": 100,
                                 "payment_bond_pct": 100, "gl_limit_usd": 3000000},
                                "Commercial general liability $3,000,000 per occurrence"),
            "walkthrough_date": F("October 2, 2026", "2026-10-02",
                                  "Pre-bid walk-through October 2, 2026 at 1:00 PM"),
        },
        "construction_window": ["2027-04-12", "2027-09-24"],
    },
    "case_08": {
        "format": "pdf_rfp",
        "source": "data/synthetic/pdfs/case_08.pdf",
        "fields": {
            "client_name": F("Pikes Hollow Athletic Club", "pikes hollow athletic club",
                             "Owner Pikes Hollow Athletic Club"),
            "project_title": F("Natatorium Pool Mechanical Replacement",
                               "natatorium pool mechanical replacement",
                               "Project Natatorium Pool Mechanical Replacement"),
            "trade_scope": F(["plumbing", "piping"], ["piping", "plumbing"],
                             "Trades Required plumbing and process piping"),
            "location": F("Colorado Springs, CO", "colorado springs, co",
                          "Project Location Colorado Springs, CO"),
            "bid_due_date": F("October 14, 2026", "2026-10-14",
                              "Bid due October 14, 2026 at 5:00 PM MT",
                              {"time_local": "17:00", "tz": "America/Denver"}),
            "estimated_project_value": F("$600,000", money(600000),
                                         "Engineer's estimate $600,000"),
            "bond_insurance": F("No bonding required", {"required": False},
                                "No bid bond, performance bond, or payment bond is required for this solicitation."),
            "walkthrough_date": ABSENT("Source states a walk-through will not be held; no date exists."),
        },
        "construction_window": ["2027-02-08", "2027-05-29"],
    },
    "case_09": {
        "format": "pdf_rfp",
        "source": "data/synthetic/pdfs/case_09.pdf",
        "fields": {
            "client_name": F("Vantage Point Logistics", "vantage point logistics",
                             "Owner Vantage Point Logistics"),
            "project_title": F("Distribution Center Ventilation Upgrade",
                               "distribution center ventilation upgrade",
                               "Project Distribution Center Ventilation Upgrade"),
            "trade_scope": F(["sheet_metal", "hvac"], ["hvac", "sheet_metal"],
                             "Trades Required sheet metal and HVAC"),
            "location": F("Longmont, CO", "longmont, co", "Project Location Longmont, CO"),
            "bid_due_date": F("November 10, 2026", "2026-11-10",
                              "Bid due November 10, 2026 at 4:00 PM MT",
                              {"time_local": "16:00", "tz": "America/Denver"}),
            "estimated_project_value": F("$2,200,000", money(2200000),
                                         "Engineer's estimate $2,200,000"),
            "bond_insurance": F("5% bid bond; 100% performance and payment bonds; $4M GL",
                                {"required": True, "bid_bond_pct": 5, "performance_bond_pct": 100,
                                 "payment_bond_pct": 100, "gl_limit_usd": 4000000},
                                "Commercial general liability $4,000,000 per occurrence"),
            "walkthrough_date": F("October 22, 2026", "2026-10-22",
                                  "Pre-bid walk-through October 22, 2026 at 9:00 AM"),
        },
        "construction_window": ["2027-05-03", "2027-10-15"],
    },
    "case_10": {
        "format": "portal_notification",
        "source": "data/synthetic/emails/case_10.eml",
        "fields": {
            "client_name": F("Front Range Regional Transit Authority",
                             "front range regional transit authority",
                             "Agency:          Front Range Regional Transit Authority"),
            "project_title": F("Maintenance Facility Bay 4 Mechanical Upgrades",
                               "maintenance facility bay 4 mechanical upgrades",
                               "Title:           Maintenance Facility Bay 4 Mechanical Upgrades"),
            "trade_scope": ABSENT("Only 'Category: Mechanical' is given, which does not resolve to "
                                  "any specific trade in the closed vocabulary."),
            "location": F("Denver, CO", "denver, co", "Place of perf.:  Denver, CO"),
            "bid_due_date": F("2026-10-06", "2026-10-06", "Response due:    2026-10-06 15:00 MT",
                              {"time_local": "15:00", "tz": "America/Denver"}),
            "estimated_project_value": ABSENT("Documents are plan-holder gated; no value in the notice."),
            "bond_insurance": ABSENT("Documents are plan-holder gated; no bonding terms in the notice."),
            "walkthrough_date": ABSENT("No walk-through mentioned in the notice."),
        },
        "construction_window": None,
    },
    "case_11": {
        "format": "portal_notification",
        "source": "data/synthetic/emails/case_11.eml",
        "fields": {
            "client_name": F("Idaho Springs Municipal Utilities District",
                             "idaho springs municipal utilities district",
                             "Owner:        Idaho Springs Municipal Utilities District"),
            "project_title": F("Water Treatment Plant No. 2 Chemical Feed Piping Replacement",
                               "water treatment plant no. 2 chemical feed piping replacement",
                               "Project:      Water Treatment Plant No. 2 Chemical Feed Piping Replacement"),
            "trade_scope": F(["plumbing", "piping"], ["piping", "plumbing"],
                             "Trades:       Plumbing, process piping"),
            "location": F("Idaho Springs, CO", "idaho springs, co", "Location:     Idaho Springs, CO"),
            "bid_due_date": F("November 3, 2026", "2026-11-03", "Bids close:   November 3, 2026"),
            "estimated_project_value": ABSENT("Notice states any engineer's estimate is in the gated documents."),
            "bond_insurance": F("5% bid bond required; no other bonding stated",
                                {"required": True, "bid_bond_pct": 5},
                                "Bid security: 5% bid bond required with submission"),
            "walkthrough_date": ABSENT("No walk-through mentioned in the notice."),
        },
        "construction_window": None,
    },
    "case_12": {
        "format": "pdf_hard",
        "source": "data/synthetic/pdfs/case_12.pdf",
        "fields": {
            "client_name": F("Silver Aspen Regional Medical Campus",
                             "silver aspen regional medical campus",
                             "OWNER Silver Aspen Regional Medical Campus"),
            "project_title": F("Central Plant Upgrade", "central plant upgrade",
                               "CENTRAL PLANT UPGRADE"),
            "trade_scope": F(["hvac", "piping", "controls"], ["controls", "hvac", "piping"],
                             "Base Bid trades are mechanical (HVAC), process and hydronic piping, "
                             "and automatic temperature controls."),
            "location": F("Castle Rock, CO", "castle rock, co", "SITE Castle Rock, CO"),
            "bid_due_date": F("November 6, 2026", "2026-11-06",
                              "Bids are now due November 6, 2026 at 2:00 PM MT",
                              {"time_local": "14:00", "tz": "America/Denver"}),
            "estimated_project_value": F("$1,800,000 to $2,100,000", money(1800000, 2100000),
                                         "ENGINEER ESTIMATE $1,800,000 to $2,100,000"),
            "bond_insurance": F("5% bid bond; 100% performance and payment bonds; $5M GL",
                                {"required": True, "bid_bond_pct": 5, "performance_bond_pct": 100,
                                 "payment_bond_pct": 100, "gl_limit_usd": 5000000},
                                "GENERAL LIABILITY $5,000,000 per occurrence"),
            "walkthrough_date": F("September 30, 2026", "2026-09-30",
                                  "PRE-BID WALK September 30, 2026 at 7:30 AM"),
        },
        "construction_window": ["2027-03-15", "2027-11-30"],
        "traps": [
            {"kind": "addendum_supersedes", "field": "bid_due_date",
             "naive_value": "2026-10-16", "correct_value": "2026-11-06",
             "note": "Superseded date appears 5x (cover + 4 page footers); controlling "
                     "Addendum No. 2 date appears once on page 4."},
            {"kind": "alternate_read_as_base", "field": "trade_scope",
             "naive_value": ["hvac", "piping", "controls", "fire_protection"],
             "correct_value": ["controls", "hvac", "piping"],
             "note": "Spec 21 12 00 / 21 13 16 have BASE BID QTY of 0 and sit under ALT 1. "
                     "Including fire_protection also flips triage to no_bid."},
            {"kind": "range_not_point", "field": "estimated_project_value",
             "note": "Estimate is a range; a point value is wrong."},
        ],
    },
}


# --------------------------------------------------------------------------
# Triage derivation -- from the profile, never hand-asserted.
# --------------------------------------------------------------------------

def derive_triage(case: dict) -> dict:
    f = case["fields"]
    miles = PROFILE["declared_drive_miles_from_base"]
    out_of_scope = set(PROFILE["trade_fit"]["out_of_scope"])
    band = PROFILE["size_band_usd"]
    cap = PROFILE["capacity"]["max_concurrent_projects"]

    missing = []
    crit = {}

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
            raise SystemExit("location %r missing from profile distance table" % loc)
        crit["within_radius"] = miles[loc] <= PROFILE["service_radius_miles"]

    val = f["estimated_project_value"]["normalized"]
    if val is None:
        missing.append("estimated_project_value")
    else:
        mid = (val["low"] + val["high"]) / 2
        crit["size_band_ok"] = band["min"] <= mid <= band["max"]

    win = case["construction_window"]
    if win is None:
        missing.append("construction_window")
    else:
        s, e = date.fromisoformat(win[0]), date.fromisoformat(win[1])
        conflict = False
        d = s
        while d <= e:
            active = sum(1 for c in PROFILE["committed_projects"]
                         if date.fromisoformat(c["start"]) <= d <= date.fromisoformat(c["end"]))
            if active >= cap:
                conflict = True
                break
            d = date.fromordinal(d.toordinal() + 1)
        crit["timeline_conflict"] = conflict

    if missing:
        return {"decision": "insufficient_information", "criteria": crit,
                "required_reasons": sorted(missing),
                "_derivation": "Missing input field(s) prevent evaluation: " + ", ".join(sorted(missing))}

    failing = []
    if not crit["trade_fit"]:
        failing.append("trade_fit")
    if not crit["within_radius"]:
        failing.append("within_radius")
    if not crit["size_band_ok"]:
        failing.append("size_band_ok")
    if crit["timeline_conflict"]:
        failing.append("timeline_conflict")

    if failing:
        return {"decision": "no_bid", "criteria": crit, "required_reasons": failing,
                "_derivation": "Failing criteria: " + ", ".join(failing)}
    return {"decision": "bid", "criteria": crit,
            "required_reasons": ["trade_fit", "size_band_ok"],
            "_derivation": "All four criteria pass."}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    failures = []
    summary = []

    for case_id in sorted(GOLD):
        case = GOLD[case_id]
        text = ws((SRC / (case_id + ".txt")).read_text(encoding="utf-8"))

        # Property 1: every cited span must really be in the document.
        for fname, fval in case["fields"].items():
            span = fval["source_span"]
            if span is None:
                if fval["present_in_source"]:
                    failures.append("%s.%s: present_in_source but no span" % (case_id, fname))
                continue
            if ws(span) not in text:
                failures.append("%s.%s: span not found in source text -> %r"
                                % (case_id, fname, ws(span)[:70]))
            # Trade vocabulary check
            if fname == "trade_scope" and fval["normalized"] is not None:
                bad = set(fval["normalized"]) - TRADE_VOCAB
                if bad:
                    failures.append("%s.trade_scope: outside vocabulary %s" % (case_id, sorted(bad)))

        # Property 3: gold's hand-authored `normalized` must be reproducible by
        # the SAME normalizer the scorer uses. Without this, a normalizer bug
        # silently fails every prediction while gold looks fine -- which is
        # exactly what happened when the corporate-suffix stripper ate the "CO"
        # in "Denver, CO". bond_insurance is excluded: its `value` is prose and
        # its `normalized` is a dict, so re-derivation is not defined.
        for fname, fval in case["fields"].items():
            if fname == "bond_insurance" or not fval["present_in_source"]:
                continue
            rederived = normalize_field(fname, fval["value"])
            if rederived != fval["normalized"]:
                failures.append("%s.%s: normalized not reproducible from value "
                                "(authored=%r, normalizer=%r)"
                                % (case_id, fname, fval["normalized"], rederived))

        # Property 2: triage derived, not asserted.
        case["triage"] = derive_triage(case)
        case["case_id"] = case_id

        n_absent = sum(1 for v in case["fields"].values() if not v["present_in_source"])
        summary.append((case_id, case["format"], 8 - n_absent, n_absent,
                        case["triage"]["decision"],
                        ",".join(case["triage"]["required_reasons"])))

        (OUT / (case_id + ".json")).write_text(
            json.dumps(case, indent=2, sort_keys=False) + "\n",
            encoding="utf-8", newline="\n")

    print("%-9s %-22s %7s %7s  %-24s %s"
          % ("CASE", "FORMAT", "PRESENT", "ABSENT", "TRIAGE", "REASONS"))
    print("-" * 104)
    tot_p = tot_a = 0
    for row in summary:
        print("%-9s %-22s %7d %7d  %-24s %s" % row)
        tot_p += row[2]
        tot_a += row[3]
    print("-" * 104)
    print("%-9s %-22s %7d %7d   (total slots: %d)" % ("TOTAL", "", tot_p, tot_a, tot_p + tot_a))

    if failures:
        print("\nVALIDATION FAILURES (%d):" % len(failures), file=sys.stderr)
        for x in failures:
            print("  - " + x, file=sys.stderr)
        return 1
    print("\nAll gold spans verified verbatim against extracted source text.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
