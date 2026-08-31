"""Is lever 3's triage result hollow?

The model evaluates the four capacity criteria and code applies the boolean
formula to the model's own answers. If the formula were doing the work, the
triage number would prove nothing. This counts how often the two agreed across
the final arm's runs.

    python scripts/check_triage_agreement.py
"""
import glob
import json
import pathlib

FINAL = {"lever2b_verify", "lever3_triage", "lever4_brief"}

runs = [json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        for f in glob.glob("evals/results/*_solution*.json")
        if "SUPERSEDED" not in f and "CONCTEST" not in f]
runs = [r for r in runs
        if r.get("n_cases") == 30 and set(r.get("active_levers") or []) == FINAL]

agree = sum(1 for r in runs for m in r["call_meta"].values()
            if (m.get("triage_audit") or {}).get("model_agreed_with_rule"))
total = sum(1 for r in runs for m in r["call_meta"].values() if m.get("triage_audit"))

print("model agreed with the boolean rule on %d of %d decisions" % (agree, total))
