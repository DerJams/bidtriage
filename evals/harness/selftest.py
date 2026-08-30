"""Self-test for the deterministic normalizers and scorer.

    python -m evals.harness.selftest

Runs before the harness is trusted with real results. Exits non-zero on any
failure. Deliberately includes the phrasings the scoring rules promise to
handle ("5%", "five percent", "$1.2M"), plus the traps the corpus contains.
"""
from __future__ import annotations

import sys

from evals.harness import score as S
from evals.harness.normalize import (
    UNPARSEABLE,
    norm_bond,
    norm_date,
    norm_money,
    norm_string,
    norm_trades,
)

FAILS = []


def check(label, got, want):
    if got != want:
        FAILS.append("%-46s got=%r want=%r" % (label, got, want))


def main() -> int:
    # --- dates -------------------------------------------------------------
    for raw, want in [
        ("September 25, 2026", "2026-09-25"),
        ("Sept 25, 2026", "2026-09-25"),
        ("2026-09-25", "2026-09-25"),
        ("November 6, 2026 at 2:00 PM MT", "2026-11-06"),
        ("6 November 2026", "2026-11-06"),
        ("9/25/2026", "2026-09-25"),
        ("2026-10-06 15:00 MT", "2026-10-06"),
        ("sometime next spring", UNPARSEABLE),
        (None, None),
    ]:
        check("date(%r)" % raw, norm_date(raw), want)

    # --- money -------------------------------------------------------------
    for raw, want in [
        ("$850,000", {"low": 850000, "high": 850000, "currency": "USD"}),
        ("850000", {"low": 850000, "high": 850000, "currency": "USD"}),
        ("$1.2M", {"low": 1200000, "high": 1200000, "currency": "USD"}),
        ("approximately $1.2 million", {"low": 1200000, "high": 1200000, "currency": "USD"}),
        ("$1,800,000 to $2,100,000", {"low": 1800000, "high": 2100000, "currency": "USD"}),
        ("$1.8M - $2.1M", {"low": 1800000, "high": 2100000, "currency": "USD"}),
        (600000, {"low": 600000, "high": 600000, "currency": "USD"}),
        ("not stated", UNPARSEABLE),
        (None, None),
    ]:
        check("money(%r)" % raw, norm_money(raw), want)

    # --- strings -----------------------------------------------------------
    check("string suffix strip", norm_string("Vantage Point Logistics, LLC"),
          "vantage point logistics")
    check("string whitespace", norm_string("  Denver,   CO  "), "denver, co")
    check("string none", norm_string(None), None)

    # --- trades ------------------------------------------------------------
    check("trades list", norm_trades(["HVAC", "sheet metal", "controls"]),
          ["controls", "hvac", "sheet_metal"])
    check("trades string", norm_trades("HVAC, sheet metal, and controls"),
          ["controls", "hvac", "sheet_metal"])
    check("trades synonyms", norm_trades(["Building Automation", "Process Piping"]),
          ["controls", "piping"])
    check("trades case12 correct", norm_trades("mechanical (HVAC), process and hydronic piping, "
                                               "and automatic temperature controls"),
          ["controls", "hvac", "piping"])
    check("trades none", norm_trades(None), None)

    # --- bonds: the phrasings the rules promise to accept ------------------
    want_full = {"required": True, "bid_bond_pct": 5, "performance_bond_pct": 100,
                 "payment_bond_pct": 100, "gl_limit_usd": 2000000}
    for label, raw in [
        ("numeric", {"required": True, "bid_bond_pct": 5, "performance_bond_pct": 100,
                     "payment_bond_pct": 100, "gl_limit_usd": 2000000}),
        ("pct strings", {"required": True, "bid_bond_pct": "5%", "performance_bond_pct": "100%",
                         "payment_bond_pct": "100%", "gl_limit_usd": "$2,000,000"}),
        ("word pct", {"required": True, "bid_bond_pct": "five percent",
                      "performance_bond_pct": "100 percent",
                      "payment_bond_pct": "100 percent", "gl_limit_usd": "$2M"}),
        ("alias keys", {"required": True, "bid_bond": "5 percent", "performance_bond": 100,
                        "payment_bond": "100%", "general_liability": "2 million"}),
    ]:
        check("bond %s" % label, norm_bond(raw), want_full)

    check("bond none-required dict", norm_bond({"required": False}), {"required": False})
    check("bond none-required prose", norm_bond("No bonding is required for this project."),
          {"required": False})
    check("bond partial (bid only)", norm_bond({"required": True, "bid_bond_pct": "5%"}),
          {"required": True, "bid_bond_pct": 5})
    check("bond none", norm_bond(None), None)

    # --- scorer outcomes ---------------------------------------------------
    gold = {
        "case_id": "t1",
        "fields": {
            "client_name": {"present_in_source": True, "normalized": "acme district"},
            "project_title": {"present_in_source": True, "normalized": "roof job"},
            "trade_scope": {"present_in_source": True, "normalized": ["controls", "hvac"]},
            "location": {"present_in_source": True, "normalized": "denver, co"},
            "bid_due_date": {"present_in_source": True, "normalized": "2026-09-25"},
            "estimated_project_value": {"present_in_source": True,
                                        "normalized": {"low": 100, "high": 100, "currency": "USD"}},
            "bond_insurance": {"present_in_source": True, "normalized": {"required": False}},
            "walkthrough_date": {"present_in_source": False, "normalized": None},
        },
        "triage": {"decision": "bid", "required_reasons": ["trade_fit"]},
    }
    pred = {
        "client_name": "Acme District",            # correct
        "project_title": "Wrong Title",            # incorrect
        "trade_scope": ["HVAC", "controls"],       # correct
        "location": None,                          # missed
        "bid_due_date": "September 25, 2026",      # correct
        "estimated_project_value": "$100",         # correct
        "bond_insurance": {"required": False},     # correct
        "walkthrough_date": "October 1, 2026",     # hallucinated (gold absent)
    }
    cs = S.score_case(gold, pred)
    outcomes = {k: v["outcome"] for k, v in cs["fields"].items()}
    check("outcome client_name", outcomes["client_name"], S.CORRECT)
    check("outcome project_title", outcomes["project_title"], S.INCORRECT)
    check("outcome trade_scope", outcomes["trade_scope"], S.CORRECT)
    check("outcome location", outcomes["location"], S.MISSED)
    check("outcome walkthrough", outcomes["walkthrough_date"], S.HALLUCINATED)

    # Abstention: correct where gold is absent, missed where gold is present.
    cs2 = S.score_case(gold, dict(pred, walkthrough_date=None, location="Denver, CO"))
    check("abstain on absent gold",
          cs2["fields"]["walkthrough_date"]["outcome"], S.CORRECT_ABSTENTION)

    # Flagging costs accuracy but is not an assertion.
    cs3 = S.score_case(gold, pred, flagged=["walkthrough_date"])
    check("flagged outcome", cs3["fields"]["walkthrough_date"]["outcome"], S.FLAGGED)
    agg_f = S.aggregate([cs3])
    check("flagged not asserted", agg_f["outcomes"][S.HALLUCINATED], 0)

    # Trade token outside the closed vocabulary fails the field.
    cs4 = S.score_case(gold, dict(pred, trade_scope=["HVAC", "controls", "elevator"]))
    check("out-of-vocab trade", cs4["fields"]["trade_scope"]["outcome"], S.INCORRECT)

    # Bond key-set rule: inventing an unstated performance bond fails.
    gold_bond = {"case_id": "t2", "fields": {
        **{k: {"present_in_source": True, "normalized": v["normalized"]}
           for k, v in gold["fields"].items()},
    }, "triage": {}}
    gold_bond["fields"]["bond_insurance"] = {"present_in_source": True,
                                             "normalized": {"required": True, "bid_bond_pct": 5}}
    cs5 = S.score_case(gold_bond, dict(pred, bond_insurance={
        "required": True, "bid_bond_pct": 5, "performance_bond_pct": 100}))
    check("bond invented key fails", cs5["fields"]["bond_insurance"]["outcome"], S.INCORRECT)

    # Aggregate arithmetic.
    agg = S.aggregate([cs])
    check("agg total slots", agg["total_slots"], 8)
    check("agg correct", agg["correct_slots"], 5)
    check("agg asserted", agg["asserted_fields"], 7)   # 5 correct + 1 incorrect + 1 halluc
    check("agg halluc count", agg["hallucination_count"], 2)
    check("agg field accuracy", round(agg["field_accuracy"], 4), round(5 / 8, 4))
    check("agg halluc asserted", round(agg["hallucination_rate_asserted"], 4),
          round(2 / 7, 4))
    check("agg halluc all slots", round(agg["hallucination_rate_all_slots"], 4),
          round(2 / 8, 4))

    # Triage scoring.
    tr = S.score_triage(gold, {"triage_decision": "BID", "triage_reasons": ["trade fit"]})
    check("triage decision", tr["decision_correct"], True)
    check("triage reason recall", tr["reasons_recall"], 1.0)

    if FAILS:
        print("SELFTEST FAILURES (%d):" % len(FAILS), file=sys.stderr)
        for f in FAILS:
            print("  " + f, file=sys.stderr)
        return 1
    print("normalizer + scorer selftest: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
