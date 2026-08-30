# The loop catching its own error before it corrupted any result

> **This is an annotated extract.** The complete, unedited transcript is in [`traces/`](../) as raw JSONL. Nothing here is paraphrased: every block below the annotations is verbatim from that file. Long tool inputs and outputs are truncated with the omitted character count shown.

## Why this episode

The agent wrote a self-test for its scorer before trusting the scorer with a paid run. The test failed immediately and caught two real defects. The serious one: the corporate-suffix stripper treated 'co' as a company suffix and silently truncated 'denver, co' to 'denver', which would have failed every location field in the corpus while the gold keys still looked correct.

## What to watch for

1. The self-test is written before it is needed, not after a failure.
2. It fails on the first run and names both defects precisely.
3. The fix carries a comment explaining why 'co' must stay out, so the bug cannot be reintroduced by someone tidying the list.
4. The test is re-run and passes. Nothing was measured while the bug was live.

---

<a id="e195"></a>`event 195`

**Agent:**

Before scoring anything with these, let me prove the normalizers actually work.

<a id="e196"></a>`event 196`

**Tool call: `Write`**

```
file: C:\Users\James\bidtriage\evals\harness\selftest.py

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
... [7790 more characters in the raw transcript]
```

<a id="e197"></a>`event 197`

**Tool result:**

```
File created successfully at: C:\Users\James\bidtriage\evals\harness\selftest.py (file state is current in your context — no need to Read it back)
```

<a id="e198"></a>`event 198`

**Tool call: `Bash`**

```bash
cd ~/bidtriage && touch evals/harness/__init__.py && ./.venv/Scripts/python.exe -m evals.harness.selftest; echo "EXIT: $?"
```

<a id="e199"></a>`event 199`

**Tool result:**

```
SELFTEST FAILURES (2):
  string whitespace                              got='denver' want='denver, co'
  trades case12 correct                          got=['controls', 'hvac', 'piping', 'process'] want=['controls', 'hvac', 'piping']
EXIT: 1
```

<a id="e200"></a>`event 200`

**Agent:**

Two real bugs, exactly what the selftest was for. The first is serious.

<a id="e201"></a>`event 201`

**Tool call: `Edit`**

```
file: C:\Users\James\bidtriage\evals\harness\normalize.py

# "co" is deliberately NOT here. It is a corporate suffix, but it is also the
# Colorado state abbreviation, and every location in this corpus ends in ", CO".
# Including it silently truncated "denver, co" to "denver" and would have failed
# all 12 location fields. Caught by selftest.py.
_SUFFIXES = ("inc", "llc", "ltd", "corp", "incorporated", "corporation")
```

<a id="e202"></a>`event 202`

**Tool result:**

```
The file C:\Users\James\bidtriage\evals\harness\normalize.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

<a id="e203"></a>`event 203`

**Tool call: `Edit`**

```
file: C:\Users\James\bidtriage\evals\harness\normalize.py

# Keyword -> trade, checked by containment within a token. Ordered longest
# first so "fire protection" wins before a bare "protection" could matter.
_TRADE_KEYWORDS = [
    ("fire protection", "fire_protection"), ("fire suppression", "fire_protection"),
    ("fire sprinkler", "fire_protection"), ("sprinkler", "fire_protection"),
    ("standpipe", "fire_protection"),
    ("sheet metal", "sheet_metal"), ("sheetmetal", "sheet_metal"),
    ("sheet_metal", "sheet_metal"), ("ductwork", "sheet_metal"), ("duct", "sheet_metal"),
    ("refrigeration", "refrigeration"), ("ammonia", "refrigeration"),
    ("plumbing", "plumbing"), ("domestic water", "plumbing"),
    ("piping", "piping"), ("hydronic", "piping"),
    ("controls", "controls"), ("automation", "controls"), ("ddc", "controls"),
    ("bas", "controls"),
    ("hvac", "hvac"), ("air conditioning", "hvac"), ("ventilation", "hvac"),
    ("heating", "hvac"),
]

# Bare modifiers that are not trades on their own. Splitting "process and
# hydronic piping" on " and " strands "process"; without this it would leak
# through as a bogus token. Caught by selftest.py.
_TRADE_MODIFIERS = {"process", "hydronic", "mechanical", "commercial", "new",
                    "existing", "base bid", "base", "general"}


def norm_trades(v):
    if v is None:
        return None
    if isinstance(v, 
... [994 more characters in the raw transcript]
```

<a id="e204"></a>`event 204`

**Tool result:**

```
The file C:\Users\James\bidtriage\evals\harness\normalize.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

<a id="e205"></a>`event 205`

**Tool call: `Bash`**

```bash
cd ~/bidtriage && ./.venv/Scripts/python.exe -m evals.harness.selftest; echo "EXIT: $?"
```

<a id="e206"></a>`event 206`

**Tool result:**

```
normalizer + scorer selftest: all checks passed
EXIT: 0
```

---

Episode covers transcript events 195-206 of 714 total. Raw transcript: [`traces/`](../).
