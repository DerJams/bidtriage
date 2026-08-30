"""Export the estimator briefs from a results file into docs/sample-briefs/.

    python scripts/export_briefs.py <results.json> [case_id ...]

The brief is the only user-facing artifact in this project, so a reader should
be able to see one without installing anything or spending API credit. These
files are exported from a real recorded run, not hand-written for display.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "sample-briefs"


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    src = pathlib.Path(argv[0])
    if not src.is_absolute():
        src = ROOT / src
    data = json.loads(src.read_text(encoding="utf-8"))
    wanted = argv[1:]

    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for cid, meta in sorted(data.get("call_meta", {}).items()):
        if wanted and cid not in wanted:
            continue
        text = meta.get("brief")
        if not text:
            continue
        decision = "unknown"
        for t in data.get("triage", {}).get("per_case", []):
            if t["case_id"] == cid:
                decision = t.get("pred_decision") or "unknown"
        path = OUT / ("%s_%s.txt" % (cid, decision))
        header = (
            "Exported from %s\n"
            "Run label: %s   levers: %s\n"
            "Model: %s via %s\n"
            "This file is generated output from a recorded run, not written by hand.\n"
            "%s\n\n" % (src.name, data.get("label"),
                        ", ".join(data.get("active_levers") or []),
                        data.get("run_config", {}).get("model"),
                        (data.get("resolved_providers") or ["?"])[0],
                        "-" * 72))
        path.write_text(header + text + "\n", encoding="utf-8", newline="\n")
        written.append(path)
        print("wrote %s" % path.relative_to(ROOT))
    if not written:
        print("no briefs found in %s (was lever4_brief active?)" % src.name)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
