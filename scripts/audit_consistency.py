"""Repo-wide consistency audit. Reports, does not fix.

    python scripts/audit_consistency.py

Builds the authoritative figure set from the committed results using the same
exclusion rules compare.py applies, then checks every number printed in the
documentation against it. Exists because this repo publishes a lot of measured
figures across several files, and a figure that was right when written goes
stale the moment an arm gains a run.
"""
from __future__ import annotations

import glob
import io
import json
import pathlib
import re
import statistics as st
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "evals" / "results"

DOCS = ["README.md", "CHANGELOG.md", "REPRODUCE.md",
        "docs/scoring-rules.md", "docs/corpus-v2-design.md"]

ARMS = {
    "baseline": [],
    "lever1_parse": ["lever1_parse"],
    "lever2_verify": ["lever2_verify"],
    "lever2b_verify": ["lever2b_verify"],
    "lever2_verify+lever3_triage": ["lever2_verify", "lever3_triage"],
    "lever2+3+4": ["lever2_verify", "lever3_triage", "lever4_brief"],
    "lever2b+3+4": ["lever2b_verify", "lever3_triage", "lever4_brief"],
}


def load_runs(corpus, levers, n_cases):
    out = []
    for f in glob.glob(str(RESULTS / "*.json")):
        name = pathlib.Path(f).name
        if "SUPERSEDED" in name or "CONCTEST" in name or "comparison" in name:
            continue
        r = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        if r.get("n_cases") != n_cases:
            continue
        if (r.get("run_config") or {}).get("corpus", "v1") != corpus:
            continue
        if set(r.get("active_levers") or []) != set(levers):
            continue
        if (r.get("reliability") or {}).get("n_failures"):
            continue
        out.append(r)
    return out


def arm_levels():
    """Authoritative per-arm means, both corpora."""
    table = {}
    for corpus, n_cases in (("v1", 12), ("v2", 30)):
        for label, levers in ARMS.items():
            rs = load_runs(corpus, levers, n_cases)
            if not rs:
                continue
            table[(corpus, label)] = {
                "n": len(rs),
                "accuracy": st.mean([x["metrics"]["field_accuracy"] * 100 for x in rs]),
                "hallucination": st.mean(
                    [x["metrics"]["hallucination_rate_asserted"] * 100 for x in rs]),
                "triage": st.mean([x["triage"]["decision_accuracy"] * 100 for x in rs]),
                "cost": st.mean([x["cost"]["per_case_usd"] for x in rs]),
            }
    return table


def comparison_rows():
    """Every delta, floor and p currently on disk."""
    rows = {}
    for f in sorted(glob.glob(str(RESULTS / "comparison_*.json"))):
        d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        for r in d["rows"]:
            rows[(pathlib.Path(f).name, r["metric"])] = r
    return rows


def main() -> int:
    levels = arm_levels()
    comps = comparison_rows()

    print("AUTHORITATIVE ARM LEVELS")
    print("%-6s %-30s %3s %9s %9s %9s %10s"
          % ("corpus", "arm", "n", "accuracy", "halluc", "triage", "cost"))
    print("-" * 84)
    for (corpus, label), v in sorted(levels.items()):
        print("%-6s %-30s %3d %9.2f %9.2f %9.2f %10.5f"
              % (corpus, label, v["n"], v["accuracy"], v["hallucination"],
                 v["triage"], v["cost"]))

    # Every percentage figure the docs assert, checked for existence somewhere
    # in the authoritative set. A figure that matches nothing is either stale or
    # a number I invented.
    known = set()
    for v in levels.values():
        for k in ("accuracy", "hallucination", "triage"):
            known.add(round(v[k], 2))
    for r in comps.values():
        known.add(round(abs(r["delta"]), 2))
        known.add(round(r["noise_floor"], 2))

    print("\nUNMATCHED PERCENTAGE FIGURES IN DOCS")
    print("(a figure matching nothing in the results is stale or invented)")
    ALLOW = {90.0, 2.0, 100.0, 0.0, 50.0, 80.0, 20.0, 30.0, 5.0, 10.0, 96.0, 12.0}
    findings = 0
    for doc in DOCS:
        p = ROOT / doc
        if not p.exists():
            continue
        text = io.open(p, encoding="utf-8").read()
        for m in re.finditer(r"(?<![\d.])(\d{1,3}\.\d{1,2})\s*(?:%|pp|percent)", text):
            val = round(float(m.group(1)), 2)
            if val in ALLOW or val in known:
                continue
            line = text[:m.start()].count("\n") + 1
            ctx = text.splitlines()[line - 1].strip()
            print("  %-24s L%-4d %-8s %s" % (doc, line, m.group(1), ctx[:90]))
            findings += 1
    if not findings:
        print("  none")

    print("\nSTALE MARKERS")
    # Word-boundaried on BOTH sides. Without the leading boundary, "spending
    # anything" matched "pending" and the audit reported three false positives,
    # which is how a checker stops being trusted.
    stale_pat = [r"\bnot yet measured\b", r"\bpending\b", r"\bwiring in progress\b",
                 r"\bin progress\b", r"\bTODO\b", r"\bTBD\b", r"\bcoming soon\b"]
    found = 0
    for doc in DOCS:
        p = ROOT / doc
        if not p.exists():
            continue
        for i, line in enumerate(io.open(p, encoding="utf-8").read().splitlines(), 1):
            if line.lstrip().startswith("|") and "Stale" in line:
                continue  # the clean-room findings table records past staleness
            for pat in stale_pat:
                if re.search(pat, line, re.I):
                    print("  %-24s L%-4d %s" % (doc, i, line.strip()[:88]))
                    found += 1
                    break
    if not found:
        print("  none")

    print("\nCORPUS LABELLING ON NUMERIC HEADINGS")
    text = io.open(ROOT / "README.md", encoding="utf-8").read()
    lines = text.splitlines()
    heads = [(i, l) for i, l in enumerate(lines, 1) if l.startswith("#")]
    for idx, (ln, head) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        body = "\n".join(lines[ln:end - 1])
        has_num = bool(re.search(r"\d{1,3}\.\d{1,2}\s*(?:%|pp)", body))
        names = re.search(r"\bv1\b|\bv2\b|corpus|corpora", head, re.I)
        if has_num and not names:
            print("  UNLABELLED  L%-4d %s" % (ln, head[:80]))
            found += 1
    print("  (nothing above = every numeric section names a corpus)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
