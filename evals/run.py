"""Run a target against all 12 cases, score it, and write timestamped results.

    python -m evals.run --target baseline
    python -m evals.run --target solution
    python -m evals.run --target baseline --cases case_01,case_12

Scoring is deterministic. Cost is the amount actually charged, read from
OpenRouter's usage block, never computed from a price table.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

from evals import config
from evals.harness import minutes as minutes_mod
from evals.harness import score as scoring

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLD_DIR = ROOT / "evals" / "gold"
SRC_DIR = ROOT / "data" / "synthetic" / "source_text"
RESULTS_DIR = ROOT / "evals" / "results"

TARGETS = ("baseline", "solution")


def load_cases(only: list | None = None) -> list:
    cases = []
    for p in sorted(GOLD_DIR.glob("case_*.json")):
        gold = json.loads(p.read_text(encoding="utf-8"))
        cid = gold["case_id"]
        if only and cid not in only:
            continue
        text = (SRC_DIR / (cid + ".txt")).read_text(encoding="utf-8")
        cases.append((cid, gold, text))
    return cases


def get_runner(target: str):
    """Return (run_callable, active_levers)."""
    if target == "baseline":
        from baseline import run_baseline
        return run_baseline.run, None
    if target == "solution":
        try:
            from solution import run_solution
        except ImportError as e:
            raise SystemExit("solution target not implemented yet (%s)" % e)
        return run_solution.run, list(getattr(run_solution, "ACTIVE_LEVERS", ()))
    raise SystemExit("unknown target: %s" % target)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run and score a BidTriage target.")
    ap.add_argument("--target", required=True, choices=TARGETS)
    ap.add_argument("--cases", default=None,
                    help="comma-separated case ids; default all 12")
    ap.add_argument("--model", default=None,
                    help="override model id (logged in results)")
    ap.add_argument("--label", default=None,
                    help="short label recorded in the results file, e.g. lever name")
    args = ap.parse_args(argv)

    only = [c.strip() for c in args.cases.split(",")] if args.cases else None
    cases = load_cases(only)
    if not cases:
        raise SystemExit("no cases matched")

    runner, active_levers = get_runner(args.target)
    started = datetime.now(timezone.utc)

    case_scores, triage_scores, call_meta = [], [], {}
    failures = []
    total_cost = 0.0
    total_retries = 0

    print("target=%s  model=%s  routing=%s(%s)  cases=%d"
          % (args.target, args.model or config.MODEL, config.ROUTING_MODE,
             config.PINNED_PROVIDER, len(cases)))
    if active_levers is not None:
        print("active levers: %s" % (", ".join(active_levers) or "none"))
    print("-" * 92)

    for cid, gold, text in cases:
        try:
            prediction, flagged, res = runner(cid, gold, text)
        except Exception as e:  # a target crash must not be silent
            failures.append({"case_id": cid, "kind": "runner_exception", "detail": repr(e)})
            prediction, flagged = None, []
            res = None

        meta = res.as_dict() if res is not None else {"ok": False, "error": "no result"}
        audit = getattr(res, "verification_audit", None)
        if audit:
            meta["verification_audit"] = audit
        t_audit = getattr(res, "triage_audit", None)
        if t_audit:
            meta["triage_audit"] = t_audit
        if flagged:
            meta["flagged_fields"] = list(flagged)
        brief_text = getattr(res, "brief", None)
        if brief_text:
            meta["brief"] = brief_text
            meta["brief_checks"] = getattr(res, "brief_checks", None)
        call_meta[cid] = meta
        total_cost += (res.cost_usd if res else 0.0)
        total_retries += (res.retries if res else 0)

        if res is not None and not res.ok:
            failures.append({"case_id": cid, "kind": "api_failure",
                             "detail": res.error, "attempts": res.attempts,
                             "retries": res.retries})
        elif prediction is None:
            failures.append({"case_id": cid, "kind": "no_prediction",
                             "detail": (res.error if res else None)})

        cs = scoring.score_case(gold, prediction, flagged)
        case_scores.append(cs)
        triage_scores.append({"case_id": cid, **scoring.score_triage(gold, prediction)})

        acc = sum(1 for f in cs["fields"].values()
                  if f["outcome"] in scoring.COUNTS_AS_CORRECT)
        print("  %-9s %d/8 correct  provider=%-11s retries=%d  cost=$%.5f%s"
              % (cid, acc, meta.get("provider"), meta.get("retries", 0),
                 meta.get("cost_usd", 0.0),
                 "  FAILED" if (res is None or not res.ok) else ""))

    agg = scoring.aggregate(case_scores)
    src = {cid: text for cid, _, text in cases}
    mins = minutes_mod.summarize(case_scores, src)

    triage_correct = sum(1 for t in triage_scores if t["decision_correct"])
    finished = datetime.now(timezone.utc)

    providers = sorted({m.get("provider") for m in call_meta.values() if m.get("provider")})

    results = {
        "target": args.target,
        "label": args.label,
        "active_levers": active_levers,
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "wall_clock_s": round((finished - started).total_seconds(), 2),
        "run_config": config.run_config(args.model),
        "resolved_providers": providers,
        "n_cases": len(cases),
        "metrics": agg,
        "triage": {
            "decision_accuracy": triage_correct / len(cases),
            "n_correct": triage_correct,
            "per_case": triage_scores,
        },
        "minutes_proxy": mins,
        "cost": {
            "total_usd": round(total_cost, 6),
            "per_case_usd": round(total_cost / len(cases), 6),
            "_source": "OpenRouter usage.cost, actual charged amount",
        },
        "reliability": {
            "total_retries": total_retries,
            "failures": failures,
            "n_failures": len(failures),
        },
        "case_scores": case_scores,
        "call_meta": call_meta,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # Second-resolution timestamps collide when arms run concurrently, and the
    # loser is silently overwritten. Caught when a concurrency test lost one of
    # two runs. Microseconds plus pid makes the name unique per process, and the
    # exists() guard is a belt-and-braces backstop.
    stamp = started.strftime("%Y%m%dT%H%M%S%fZ")
    out = RESULTS_DIR / ("%s_%s_p%d.json" % (stamp, args.target, os.getpid()))
    dedup = 0
    while out.exists():
        dedup += 1
        out = RESULTS_DIR / ("%s_%s_p%d_%d.json" % (stamp, args.target, os.getpid(), dedup))
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")

    print("-" * 92)
    print("field accuracy .............. %6.1f%%   (%d/%d slots)"
          % (100 * agg["field_accuracy"], agg["correct_slots"], agg["total_slots"]))
    print("hallucination rate (judged) . %6.1f%%   (%d of %d asserted fields)"
          % (100 * agg["hallucination_rate_asserted"], agg["hallucination_count"],
             agg["asserted_fields"]))
    print("hallucination rate (/%d) ..... %6.1f%%   [diagnostic only]"
          % (agg["total_slots"], 100 * agg["hallucination_rate_all_slots"]))
    print("triage decision accuracy .... %6.1f%%   (%d/%d)"
          % (100 * triage_correct / len(cases), triage_correct, len(cases)))
    print("minutes/intake (PROXY) ...... %6.1f    vs %.1f manual"
          % (mins["assisted_minutes_mean"], mins["manual_minutes_mean"]))
    print("cost per case ............... $%.5f  (total $%.5f)"
          % (results["cost"]["per_case_usd"], results["cost"]["total_usd"]))
    print("retries / failures .......... %d / %d" % (total_retries, len(failures)))
    print("resolved provider(s) ........ %s" % (", ".join(providers) or "none"))
    print("\noutcome breakdown: " + "  ".join(
        "%s=%d" % (k, v) for k, v in agg["outcomes"].items() if v))
    print("\nwrote %s" % out.relative_to(ROOT))

    if failures:
        print("\n%d FAILURE(S) recorded in results file:" % len(failures), file=sys.stderr)
        for f in failures:
            print("  %s: %s %s" % (f["case_id"], f["kind"],
                                   str(f.get("detail"))[:120]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
