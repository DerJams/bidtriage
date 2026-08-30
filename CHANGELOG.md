# CHANGELOG

Every row is backed by a real run. No number in this table is estimated,
projected, or remembered — each links to a results file in `evals/results/`.

| Stage | What I tried and why | Evidence | Decision / Learning |
|---|---|---|---|
| Step 0 — Repo setup | Public repo, pinned toolchain, scaffold matching the submission requirements. Git initialized in `~/bidtriage` rather than `~` (home dir contains `.ssh`, `.claude`, and browser profiles; a repo rooted there would publish credentials). | [Initial commit](https://github.com/DerJams/bidtriage/commits/main) | Repo hygiene fixed before any data exists. |

| Step 1 — Eval set first | Built 12 synthetic cases and gold keys **before** writing any agent, so the target could not be fitted to whatever the first attempt happened to produce. Froze scoring rules in `docs/scoring-rules.md` in an earlier commit than any result file. | [`evals/gold/`](evals/gold/), [`docs/scoring-rules.md`](docs/scoring-rules.md), `python -m evals.author_gold` exits 0 | 96 slots: 88 present, 8 legitimately absent. Absence is a gold value, which is what makes the hallucination metric meaningful rather than decorative. |
| Step 1a — Gold spans validated, not trusted | Wrote a validator asserting every non-null `source_span` appears verbatim in the extracted text. Cheaper to build than to debug a gold key that cites text which was never in the document. | `evals/author_gold.py`, all 88 spans pass | Caught nothing on the first run, which is the point: the guarantee is now mechanical rather than a claim. Also constrains the Step-4 verification lever — it must cite spans that actually exist. |
| Step 1b — Triage derived, not asserted | Derived each case's bid/no-bid from `contractor_profile.json` rules instead of hand-writing it, so gold triage cannot drift from published criteria. | `derive_triage()` in `evals/author_gold.py` | Forced the capacity model to be explicit and falsifiable. Surfaced that sparse portal cases have no honest bid/no-bid answer, so `insufficient_information` was added as a third decision value. |
| Step 1c — PDF corruption caught pre-submission | Commit warnings showed Git applying CRLF conversion to generated PDFs, which corrupts them on clone. Added `.gitattributes` marking PDFs binary. | Clean clone verified byte-identical to locally generated (md5 match) | A reproducibility bug that would have shipped silently and broken the corpus for anyone cloning. Verified by clone, not by assumption. |
| Step 1d — Trace capture scoped down | The Claude Code project directory holds 10 sessions / 28 MB, only one of them BidTriage. Wrote a capture script requiring explicit session ids with **no copy-all flag**, plus a credential redactor. | [`scripts/capture_traces.py`](scripts/capture_traces.py), [`traces/REDACTIONS.md`](traces/REDACTIONS.md) | A `cp -r` would have published unrelated transcripts to a public repo. First redactor version over-matched and ate the fictional `.example` addresses — fixed by moving the lookahead to the TLD. |

<!-- Baseline row lands at Step 2. No performance numbers exist yet. -->
