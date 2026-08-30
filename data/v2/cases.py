"""Corpus v2: 30 synthetic cases, all fictional.

Aggregates the three case batches. Helpers live in common.py so the batch
modules can import them without a circular import.

Batch A (01 to 05): revised from v1, commercial terms aligned.
Batch B (06 to 18): the rest of the v1 revisions, including the two platform
    cases rewritten as multi-part, plus the first new shapes.
Batch C (19 to 30): the remaining new shapes and failure modes.
"""
from __future__ import annotations

from data.v2 import cases_a, cases_b, cases_c

CASES = list(cases_a.CASES) + list(cases_b.CASES) + list(cases_c.CASES)

_ids = [c["id"] for c in CASES]
if len(set(_ids)) != len(_ids):
    dupes = sorted({i for i in _ids if _ids.count(i) > 1})
    raise SystemExit("duplicate case ids in corpus v2: %s" % dupes)
