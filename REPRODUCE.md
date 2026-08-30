# REPRODUCE

Every command below has been executed by following this file literally in a
clean clone, with nothing inherited from the development environment. Where a
stage has not been measured, it says so and carries no numbers.

> **This file was clean-room tested on 2026-08-30 and several defects were
> found and fixed.** The largest: the venv was created but never activated, so
> every documented command ran under system Python and two of them failed
> outright. All commands below now name the interpreter explicitly. What the
> walkthrough found is listed at the end under "Clean-room test results".

## Environment

| | |
|---|---|
| Python | 3.12.13 (CPython, installed via `uv python install 3.12`) |
| Package manager | `uv` 0.11.16 |
| Dependencies | 9 packages, pinned in `requirements.txt` from a real resolve |
| Tested platform | Windows 11 Pro 26200, Git Bash |
| External services | OpenRouter API only |
| Model under test | `z-ai/glm-5.3-flash` (fallback `z-ai/glm-5.2`) |
| Provider routing | `only=["deepinfra"]`, `allow_fallbacks=false`, `require_parameters=true` |

Key pinned versions: `reportlab==5.0.1`, `pdfplumber==0.11.10`,
`pdfminer-six==20260107`. The API client is stdlib `urllib`, so no vendor SDK
is required.

## 1. Setup

```bash
git clone https://github.com/DerJams/bidtriage.git
cd bidtriage
uv python install 3.12
uv venv --python 3.12 .venv
uv pip install --python ./.venv/Scripts/python.exe -r requirements.txt
```

**Every command in this file uses `./.venv/Scripts/python.exe` explicitly.**
Do not substitute a bare `python`: the venv is never activated, so `python`
resolves to whatever system interpreter is on PATH. On this machine that is
Python 3.14 without the dependencies, and `data.generate_pdfs` fails with
`ModuleNotFoundError: No module named 'reportlab'`.

On Linux and macOS the interpreter is `./.venv/bin/python` throughout. Set a
shell variable once and the rest of this file copies cleanly:

```bash
PY=./.venv/Scripts/python.exe      # Windows
PY=./.venv/bin/python              # Linux and macOS
```

Confirm you have the right interpreter before going further:

```bash
$PY --version          # must print Python 3.12.13
```

`uv python install 3.12` may print `error: Missing expected target directory
for Python minor version link`. This is a benign uv symlink warning on Windows.
The interpreter installs correctly and `uv venv` finds it, which the version
check above confirms.

### API key

Needed from section 3 onward. Sections 2 and 5 make no API calls.

```bash
export OPENROUTER_API_KEY=...
```

If it is missing, any run exits immediately with code 2 and a clear message,
before writing anything.

### Verify the harness before spending anything

```bash
$PY -m evals.harness.selftest
```

No API calls. Exits non-zero on any failure. This is the fastest check that the
checkout is sound.

## 2. Regenerate the eval corpus (no API calls)

The corpus is committed, so this only verifies reproducibility.

```bash
$PY -m data.generate_pdfs         # measured 324 ms
$PY -m data.extract_source_text   # measured 613 ms
$PY -m evals.author_gold          # measured 165 ms
```

`author_gold` exits non-zero if any gold `source_span` cannot be found verbatim
in the extracted text. Expected final lines:

```
TOTAL                                 88       8   (total slots: 96)

All gold spans verified verbatim against extracted source text.
```

### Confirming the PDFs survived the clone

```bash
$PY -m data.generate_pdfs && md5sum data/synthetic/pdfs/*.pdf
```

Expected, and verified from a clean clone:

```
1e83b062b65ffcf4f63c8b0a038b49db  case_06.pdf
01f1fdd4d9e9d04a79e7985b6e883738  case_07.pdf
e75e4713e3ec3f181bfc9f005641dad7  case_08.pdf
f0cf56818602497f136c5c4454b7c977  case_09.pdf
f6e17afea3a02bfdc790b32c90111cc0  case_12.pdf
```

reportlab runs in invariant mode, so regeneration is byte-identical and
`git status` stays clean afterwards. `.gitattributes` marks PDFs binary to
prevent CRLF corruption on checkout. On macOS use `md5 -r` instead of `md5sum`.

## 3. Baseline

```bash
$PY -m evals.run --target baseline
```

Runs all 12 cases, scores them deterministically, and writes a timestamped JSON
file to `evals/results/`. **Measured: 136 s per run, $0.00154 per run
($0.00013 per case).**

Temperature 0 is **not** deterministic on this provider, so one run is not a
measurement. Recorded results use **n=8** per arm:

```bash
for i in 1 2 3 4 5 6 7 8; do $PY -m evals.run --target baseline --label "run-$i"; done
```

A run that hits hard failures exits 1 and is excluded from comparisons.

Flags: `--cases case_01,case_12` for a subset, `--label` to tag a run,
`--model` to override the model id (recorded in the results file).

## 4. Solution levers

Levers are selected with `BIDTRIAGE_LEVERS` and stack. **If the variable is
unset the default is `lever2_verify` alone**, so set it explicitly:

```bash
BIDTRIAGE_LEVERS=lever2_verify $PY -m evals.run --target solution
BIDTRIAGE_LEVERS=lever2_verify,lever3_triage $PY -m evals.run --target solution
BIDTRIAGE_LEVERS=lever2_verify,lever3_triage,lever4_brief $PY -m evals.run --target solution
```

Valid names: `lever1_parse`, `lever2_verify`, `lever2b_verify`,
`lever3_triage`, `lever4_brief`. An unknown name exits with an error rather
than being ignored.

`lever2b_verify` is lever 2 with one reconciliation rule revised after
measurement. It is a separate lever id rather than an edit to `lever2_verify`,
so both are runnable and the recorded results for each remain valid. The final
configuration is `lever2b_verify,lever3_triage,lever4_brief`.

Measured per-run wall clock on the 12-case set: baseline 136 s, lever 2 341 s,
lever 2+3 654 s.

### Running arms concurrently

Arms are I/O bound. Measured: three concurrent workers give a **3.56x** speedup,
with retries rising only from 0.00 to 0.22 per case. Results filenames carry
microseconds and pid, so concurrent runs cannot overwrite one another.

```bash
BIDTRIAGE_LEVERS=lever2_verify $PY -m evals.run --target solution --label a &
BIDTRIAGE_LEVERS=lever2_verify,lever3_triage $PY -m evals.run --target solution --label b &
wait
```

## 5. Comparing arms (no API calls)

Results are committed, so this reproduces every published number without
spending anything:

```bash
$PY -m evals.compare --a baseline --b lever2_verify+lever3_triage
$PY -m evals.compare --a lever2_verify --b lever2_verify+lever3_triage
```

An arm is named by its lever set joined with `+`. The verdict rule is enforced
here rather than by judgement: an exact two-sided permutation test, with an
improvement requiring the delta to clear the larger observed spread **and**
reach p below 0.05. The noise floor is derived from the runs being compared, so
it is always empirical to whatever corpus it is run against. Runs with hard
failures are excluded and the exclusion is printed.

## 6. Corpus selection

```bash
BIDTRIAGE_CORPUS=v1 $PY -m evals.run --target baseline    # default
BIDTRIAGE_CORPUS=v2 $PY -m evals.run --target baseline
```

**v1** is the frozen 12-case set (96 scored slots) that the v1 results were
measured on. **v2** is the revised and expanded set: 30 cases, 240 scored slots,
18 document formats, including multi-part platform cases. Both are kept and both
sets of results are reported; v2 does not replace v1.

The corpus version also selects the bond field shape, because v2 splits general
liability into per-occurrence and aggregate limits, and it selects the gold and
source directories. v1 therefore stays exactly reproducible.

Rebuild and validate the v2 corpus with:

```bash
BIDTRIAGE_CORPUS=v2 $PY -m data.v2.build
```

That renders every document, extracts the text, authors the gold keys, and
validates every span against the assembled document. It exits non-zero if any
span cannot be located or any normalized value is not reproducible.

## 7. Sample briefs

Three exported examples covering bid, no-bid and insufficient-information are
committed under `docs/sample-briefs/` and need no API call to read. To export
your own from a run that had `lever4_brief` active:

```bash
$PY scripts/export_briefs.py evals/results/<file>.json
```

## 8. Trace capture

```bash
$PY scripts/capture_traces.py --list
$PY scripts/capture_traces.py --project <project-dir> <session-id>
```

Requires explicit session ids. There is no copy-all flag: the Claude Code
project directory also holds unrelated sessions and `traces/` is public.
Transcripts are redacted for credential-shaped strings; see
`traces/REDACTIONS.md`. If more than one project directory exists the script
lists them and asks rather than guessing.

## Runtime and cost

All figures below are measured. Cost is the amount actually charged.

**Corpus v1, 12 cases per run:**

| Stage | Runtime | API cost |
|---|---|---|
| Corpus regeneration | 1.1 s total | none |
| Harness selftest | under 1 s | none |
| Comparing arms | under 2 s | none |
| Baseline, one run | 136 s | $0.00154 |
| Lever 2, one run | 341 s | $0.00480 |
| Lever 2+3, one run | 654 s | $0.00720 |

**Corpus v2, 30 cases per run:**

| Arm | Runs recorded | Runtime per run | API cost per run |
|---|---|---|---|
| baseline | 8 | 345 s | $0.00368 |
| `lever1_parse` | 6 | 347 s | $0.00371 |
| `lever2_verify` | 5 | 733 s | $0.01122 |
| `lever2b_verify` | 5 | 663 s | $0.01130 |
| `lever2_verify,lever3_triage,lever4_brief` | 5 | 1108 s | $0.01739 |
| `lever2b_verify,lever3_triage,lever4_brief` (final) | 8 | 1065 s | $0.01747 |

Total API spend across every recorded v2 run: **$0.39**. Running the full v2
measurement from scratch costs well under a dollar. Wall clock is about 90
minutes with six concurrent streams, or about 5 hours sequentially.

Cost is read from OpenRouter's `usage.cost` on each response, the amount
actually charged. It is never computed from a price table and never estimated.

### Upstream rate limits

With `allow_fallbacks: false` a 429 is a hard failure rather than something
OpenRouter reroutes around. The client retries with exponential backoff, capped
at 6 attempts, and records every retry with its reason plus any hard failure in
the results file. Observed: 2 to 11 retries per 12-case run, **0 hard
failures** across every recorded v1 run, and 0 across the 16 runs of the two
v2 headline arms.

One further retry class was added after v2 exposed it: a structured-output
request that returns unparseable content is retried as a malformed **response**,
the same way a 429 is. It is not a semantic retry, so the baseline still gets
exactly one attempt at the task. Retries are logged with status
`malformed_json`.

---

## Clean-room test results

Performed 2026-08-30 by cloning into an empty directory and following this file
literally, using nothing from the development environment.

| # | Severity | Finding | Status |
|---|---|---|---|
| 1 | **Blocker** | The venv was created but never activated, so every `python` command ran under system Python 3.14. `data.generate_pdfs` and `data.extract_source_text` failed with `ModuleNotFoundError`. Worse, `selftest` and `author_gold` **passed anyway**, because they import no third-party packages, so the guide appeared to work right up until it did not. | Fixed: every command names the interpreter explicitly, with a version check. |
| 2 | **Blocker** | A run with no API key completed, scored every field as missed, **exited 0**, and wrote a results file that looked like a legitimate 0% measurement. `compare.py` filtered only on case count, so a full 12-case keyless run would have been ingested as a real arm. | Fixed: preflight exits 2 before writing anything; runs with failures exit 1; `compare.py` excludes failed runs and says so. |
| 3 | Portability | `capture_traces.py` hardcoded one developer's username in the project path, making it unusable on any other machine. | Fixed: resolves from the repo path, falls back to the sole directory with transcripts, and asks via `--project` when ambiguous. |
| 4 | Gap | The PDF verification step said "compare against a fresh clone" but gave no expected values. | Fixed: expected md5s listed. |
| 5 | Gap | `BIDTRIAGE_LEVERS` silently defaults to `lever2_verify`, so `--target solution` with no variable set runs a different arm than a reader would assume. | Fixed: default and valid names documented. |
| 6 | Stale | Said "use n>=3" and "n=4 protocol" after the protocol moved to n=8, and listed solution runtime and cost as "pending" after both were measured. | Fixed with measured figures. |
| 7 | Gap | `md5sum` does not exist on macOS. | Fixed: `md5 -r` noted. |
| 8 | Gap | `export_briefs.py <results.json>` gave no runnable example and did not say the committed samples need no API call. | Fixed. |

What worked without modification: the clone, `uv` setup, dependency install,
byte-identical PDF regeneration with a clean `git status` afterwards, gold
validation, `compare` reproducing every published number from committed results
with no API spend, and a full end-to-end run once the correct interpreter was
used.
