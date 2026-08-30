"""Compare two groups of runs, with the noise floor enforced in code.

    python -m evals.compare --a baseline --b lever2_verify

Temperature 0 is not deterministic on this provider, so a single run is not a
measurement and a raw delta is not a result. This module makes the rule
mechanical rather than a matter of judgement:

* An **exact permutation test** over all C(n_a+n_b, n_a) label assignments.
  At n=5 vs n=5 that is 252 splits -- exact, and no scipy needed.
* A **noise floor** taken as the larger of the two groups' observed spreads.
* A delta is only called an improvement when it clears the noise floor AND the
  permutation test reaches p < 0.05. Anything else is reported as WITHIN NOISE,
  regardless of which direction it points.

The permutation test is two-sided and makes no normality assumption, which
matters at these sample sizes.
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import pathlib
import statistics as st

from evals import config

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "evals" / "results"
GOLD_DIR = ROOT / "evals" / config.GOLD_DIRNAME

# Full-corpus size for the SELECTED corpus. Hardcoding 12 would have silently
# excluded every v2 run, which is exactly the kind of empty-comparison failure
# that looks like a missing arm rather than a filter bug.
EXPECTED_CASES = len(list(GOLD_DIR.glob("case_*.json")))

METRICS = [
    ("field_accuracy", "field accuracy %", "higher", lambda r: r["metrics"]["field_accuracy"] * 100),
    ("hallucination", "hallucination % (judged)", "lower",
     lambda r: r["metrics"]["hallucination_rate_asserted"] * 100),
    ("triage", "triage accuracy %", "higher", lambda r: r["triage"]["decision_accuracy"] * 100),
    ("cost", "cost per case $", "lower", lambda r: r["cost"]["per_case_usd"]),
    ("minutes", "minutes/intake (proxy)", "lower",
     lambda r: r["minutes_proxy"]["assisted_minutes_mean"]),
]

ALPHA = 0.05


def load_group(name: str) -> list:
    """A group is 'baseline' or a lever spec.

    A lever spec is one lever id, or several joined with '+' for a stacked arm,
    e.g. 'lever2_verify+lever3_triage'. Matching is on the exact SET of active
    levers, so a stacked arm never silently absorbs single-lever runs.
    SUPERSEDED files are never loaded.
    """
    want = [t for t in name.split("+") if t]
    out, skipped = [], []
    for f in sorted(glob.glob(str(RESULTS / "*.json"))):
        if "SUPERSEDED" in pathlib.Path(f).name:
            continue
        r = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        if r.get("n_cases") != EXPECTED_CASES:
            continue  # partial/target-check runs are not measurements
        if (r.get("run_config") or {}).get("corpus", "v1") != config.CORPUS:
            continue  # never mix corpora in one comparison
        if (r.get("reliability") or {}).get("n_failures"):
            skipped.append(pathlib.Path(f).name)
            continue  # a run with hard failures is not a measurement either
        levers = set(r.get("active_levers") or [])
        if name == "baseline" and r["target"] == "baseline":
            out.append(r)
        elif name != "baseline" and r["target"] == "solution" and levers == set(want):
            out.append(r)
    if skipped:
        print("  note: excluded %d run(s) with hard failures: %s"
              % (len(skipped), ", ".join(skipped[:3]) + ("..." if len(skipped) > 3 else "")))
    return out


def permutation_p(a: list, b: list) -> float:
    """Exact two-sided permutation test on the difference of means."""
    obs = abs(st.mean(b) - st.mean(a))
    pool = list(a) + list(b)
    n = len(a)
    hits = total = 0
    for combo in itertools.combinations(range(len(pool)), n):
        left = [pool[i] for i in combo]
        right = [pool[i] for i in range(len(pool)) if i not in combo]
        total += 1
        if abs(st.mean(right) - st.mean(left)) >= obs - 1e-12:
            hits += 1
    return hits / total


def compare(name_a: str, name_b: str) -> int:
    ga, gb = load_group(name_a), load_group(name_b)
    if len(ga) < 2 or len(gb) < 2:
        raise SystemExit("need >=2 runs per group (got %d and %d)" % (len(ga), len(gb)))

    print("corpus %s, %d cases per run" % (config.CORPUS, EXPECTED_CASES))
    print("A = %-18s n=%d" % (name_a, len(ga)))
    print("B = %-18s n=%d" % (name_b, len(gb)))
    print("verdict rule: improvement requires |delta| >= noise floor AND p < %.2f\n" % ALPHA)
    print("%-26s %-22s %-22s %9s %9s %8s  %s"
          % ("metric", "A mean [min-max]", "B mean [min-max]", "delta", "floor", "p", "verdict"))
    print("-" * 124)

    rows = []
    for key, label, better, getter in METRICS:
        a = [getter(r) for r in ga]
        b = [getter(r) for r in gb]
        ma, mb = st.mean(a), st.mean(b)
        delta = mb - ma
        floor = max(max(a) - min(a), max(b) - min(b))
        p = permutation_p(a, b)

        favourable = (delta > 0) if better == "higher" else (delta < 0)
        if abs(delta) < floor or p >= ALPHA:
            verdict = "WITHIN NOISE"
        else:
            verdict = "IMPROVEMENT" if favourable else "REGRESSION"

        fmt = "%.5f" if key == "cost" else "%.2f"
        print("%-26s %-22s %-22s %+9s %9s %8.3f  %s"
              % (label,
                 (fmt + " [" + fmt + "-" + fmt + "]") % (ma, min(a), max(a)),
                 (fmt + " [" + fmt + "-" + fmt + "]") % (mb, min(b), max(b)),
                 fmt % delta, fmt % floor, p, verdict))
        rows.append({"metric": key, "label": label, "a_mean": ma, "b_mean": mb,
                     "delta": delta, "noise_floor": floor, "p_value": p,
                     "verdict": verdict, "a_values": a, "b_values": b})

    # The corpus must be in the filename. Without it a v2 comparison silently
    # overwrote the v1 comparison of the same two arms, because the arms are
    # named identically on both corpora. Same class of collision as the results
    # filenames, found the same way: by looking at what was actually on disk.
    out = RESULTS / ("comparison_%s_%s_vs_%s.json" % (config.CORPUS, name_a, name_b))
    out.write_text(json.dumps({"a": name_a, "b": name_b, "n_a": len(ga), "n_b": len(gb),
                               "alpha": ALPHA, "rows": rows}, indent=2) + "\n",
                   encoding="utf-8", newline="\n")
    print("\nwrote %s" % out.relative_to(ROOT))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="baseline")
    ap.add_argument("--b", required=True)
    args = ap.parse_args(argv)
    return compare(args.a, args.b)


if __name__ == "__main__":
    raise SystemExit(main())
