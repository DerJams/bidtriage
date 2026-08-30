# BidTriage

An agent that ingests inbound project requests for small commercial mechanical
contractors, extracts structured bid data, verifies every field against the
source document, and produces a go/no-go triage decision plus an
estimator-ready brief.

Entry for the **micro1 Frontier Engineering Challenge 2026**.

---

## The user and the bottleneck

**Who.** The sole operations coordinator at a small commercial mechanical
contractor (HVAC/plumbing). The firm runs five or six overlapping projects a
year. She is the only person who touches inbound work before it reaches an
estimator.

**What arrives.** Emails with the scope buried in prose, which is where most of
the ambiguity lives, because a general contractor writing one by hand includes
whatever they remember to include. RFP PDFs with spec tables and addenda.
Platform invitations from bid-management systems, which are the opposite: they
are generated from structured project fields and are consistently complete, so
the ambiguity sits in the scope documents attached to them rather than in the
notification itself.

That distinction is not an assumption. It is drawn from platform documentation
and corroborated independently, and it is why the v2 corpus models platform
invitations as structured and complete with the missing information pushed into
an attachment. The v1 corpus modelled them as sparse notifications, which the
research overturned. See [`docs/corpus-v2-design.md`](docs/corpus-v2-design.md).

**What she does today.** Reads each one manually. Re-keys client, project
title, trade scope, location, bid due date, estimated value, bonding and
insurance requirements, and walk-through date into a spreadsheet. Then decides
whether it is worth the estimator's time at all.

**The cost.** Each intake takes 20 to 40 minutes. The errors are the expensive
part: a missed addendum that moves a bid date, a quantity read out of the wrong
column, an alternate priced as base scope. Any one of them loses a bid
opportunity outright, and the firm only gets five or six shots a year.

**Why an agent, specifically.** This is not a parsing problem. Getting a date
out of a PDF is easy. The hard part is knowing *which* date is controlling when
the cover sheet, four page footers, and page 4's addendum disagree, and being
willing to say "I am not sure, look at this one" instead of guessing. That is
judgment under uncertainty over messy documents, which is what an agent is for
and what a regex is not.

## What "good" means (defined before measuring)

Frozen in [`docs/scoring-rules.md`](docs/scoring-rules.md), committed **before**
any result existed. Git history is the proof: that file predates every file in
`evals/results/`.

| Metric | Target |
|---|---|
| Field-level extraction accuracy (primary) | at least 90% |
| Hallucination rate (asserted-field denominator) | at most 2% |
| Estimator brief | forwardable without edits |

Scoring is fully deterministic. There is no LLM judge anywhere in the harness.

## Eval set

There are two corpora and both are kept. **v1** is the original 12 cases and 96
scored slots, described below. **v2** is the revised and expanded set used for
the final measurement: 30 cases, 240 scored slots, 18 document formats,
including multi-part platform cases. See
[`docs/corpus-v2-design.md`](docs/corpus-v2-design.md) for what changed and why,
and the v2 results section for its numbers.

### Corpus v1, 12 cases and 96 scored slots

| Format | Cases | Notes |
|---|---|---|
| Email RFP requests | 01 to 05 | varying verbosity: sectioned, conversational, forwarded thread with quoted history, terse, fixed-width tabular |
| RFP PDFs | 06 to 09 | generated with realistic spec-table layouts |
| Bid-portal notifications | 10, 11 | terse and link-style; most fields genuinely absent |
| Hard case | 12 | see below |

**88 slots are present in source; 8 are legitimately absent.** Absence is a
first-class gold value: for the portal cases the correct output is `null`, and
asserting a value there is what the hallucination metric counts.

**Case 12** is the deliberately hard one. Three traps, each a real intake
failure mode:

1. The superseded bid date appears **five times** (cover sheet plus every page
   footer); the controlling Addendum No. 2 date appears **once**, on page 4.
2. Fire-protection work sits in an `ALT 1` column with a base-bid quantity of
   zero. Reading it as base scope pulls in a trade the contractor does not
   self-perform, which flips the triage decision.
3. The engineer's estimate is a range, not a point value.

Case 12 is **layout-degraded, not a true scan.** A real scan would need an OCR
system dependency (tesseract) that would break clean-environment
reproducibility, so the structural failure modes are reproduced without it.
This is a deliberate, disclosed deviation from "scanned-looking."

Triage gold is **derived** from [`data/contractor_profile.json`](data/contractor_profile.json)
rather than hand-asserted, so it cannot silently disagree with the published
criteria. The mix is 6 bid, 4 no-bid, and 2 insufficient-information, and each
no-bid is driven by a **different** failing criterion, so all four triage rules
are exercised.

### Corpus v2, 30 cases and 240 scored slots

The set used for the final measurement. **230 slots are present in source; 10
are legitimately absent.** Composition by channel:

| Channel | Cases | Notes |
|---|---|---|
| RFP PDFs, single document | 13 | standard ITBs, a federal Miller Act solicitation, a municipal notice, design-build, multi-phase, negotiated work |
| Emails, single document | 11 | the omission-prone channel: forwarded threads, GC scope sheets, urgent short-turnaround, owner and GC named separately |
| Platform invitations plus attachment | 6 | structured invitation, ambiguity in the attached scope document |

Across 18 distinct document formats. **Three cases are adversarial**, which is
1 in 10, close to v1's 1 in 12 rather than a corpus of traps:

| Case | Trap |
|---|---|
| `case_12` | an addendum supersedes the bid date, which is quoted five times against the correct date once, and fire protection sits in an ALT column that is not base scope |
| `case_14` | an addendum changes a **material term**, raising the bid bond and liability limits, with the superseded figures appearing first |
| `case_17` | a later reply in an email thread supersedes the date stated in the quoted original below it |

All four triage criteria drive a no-bid somewhere: trade fit 2 cases, service
radius 2, size band 3, timeline conflict 2. The final configuration solves all
three adversarial cases 5 times out of 5.

### Corpus provenance

The corpus is entirely synthetic, but its shape is not invented. The document
structures, the commercial terms (bonding percentages and liability limits), and
the triage criteria follow documented industry practice rather than assumption.
A corpus whose conventions were guessed would measure how well a model handles
those guesses. See [`docs/corpus-v2-design.md`](docs/corpus-v2-design.md) for
what was sourced, with citations, and for what is deliberately **not** sourced.

Source quality is graded there rather than flattened. Platform invitation
structure and bonding conventions are well documented, from BuildingConnected's
own documentation and FAR Part 28 respectively. The decline-reason criteria are
partly peer-reviewed (project size, capital, payment timeliness, workload,
overhead) and partly vendor-derived: the frequently quoted figure that 80% of
accepted bids fall within 55 miles comes from a vendor toolkit with no published
methodology, so it is treated as directional rather than as a constant.

### Data integrity

- **Everything is synthetic.** "Summit Peak Mechanical", every client, every
  person, and every document are fictional. All email domains use the reserved
  `.example` TLD (RFC 6761). Colorado place names are real geography used for
  realism; they identify no person or organization.
- **Drive distances are declared operating parameters,** not geocoded
  measurements, and are labelled as such in the profile. They exist to make
  triage deterministic and auditable.
- **Every gold citation is verified.** `evals/author_gold.py` asserts that each
  non-null `source_span` appears verbatim (whitespace-normalized) in the
  extracted source text. A span that cannot be located is a hard failure, not a
  warning. Gold citations therefore cannot be things that merely seemed to be in
  the document.

## Status

| Step | State |
|---|---|
| 0. Repo setup | done |
| 1. Synthetic eval set and gold keys | done |
| 2. Baseline | done, measured over 8 runs |
| 3. Eval harness | done |
| 4. Solution levers | all four built and measured. Lever 1 measured flat and is the removed experiment |
| 5. Corpus v2 | done: 30 cases, 240 slots. Headline arms measured at n=8, intermediate arms at n=5 |

## System design and measured results

![BidTriage inputs and the two paths: twelve cases feed a baseline path and a verified solution path](docs/system-design-paths.png)

*Inputs and the two paths.* Source:
[`docs/system-design-paths.excalidraw`](docs/system-design-paths.excalidraw)

![BidTriage evaluation harness: gold keys, deterministic normalizers, scoring, permutation test, and the measured results](docs/system-design-evaluation.png)

*Evaluation harness and results.* Source:
[`docs/system-design-evaluation.excalidraw`](docs/system-design-evaluation.excalidraw)

> Both diagrams open at [excalidraw.com](https://excalidraw.com) from the
> sources above. Every figure in the second diagram is also written out as a
> table below, so the numbers stay readable however the image scales.

**What the pipeline does.** Synthetic cases across several input shapes (email
RFPs, RFP PDFs, platform invitations with attachments, and deliberately hard
documents) feed two paths. The diagrams show the v1 set of twelve; the final
measurement uses the v2 set of thirty. The **baseline** pastes the raw document text into a single model call
with no tools, no retry logic, and no verification. The **solution** runs an
extraction call, then a verification call, then a triage call, adding one lever
at a time. Both paths emit the same fixed prediction schema and are scored by
the same harness over the same slots, 96 on v1 and 240 on v2, so the comparison
is like-for-like and neither path can win on output formatting.

**How verification works (lever 2).** A second pass re-reads the source and
returns, for every field, a status and a quote it claims supports that value.
Reconciliation then searches the actual document for that quote: a model
asserting it checked is worth nothing, but a quote that must be found
character-for-character is a checkable claim. A field whose claimed span cannot
be located drops to a human review queue instead of being believed, and the
whole reconciliation is deterministic, so no model call decides a final outcome.

**How triage works (lever 3).** The contractor capacity rules are rendered into
criteria the model can check: self-performed trades, a declared drive-distance
table, the size band, and the three already-committed projects with a
three-project concurrency limit. The model evaluates each criterion and says
why; code applies only the published boolean formula to the model's own answers.
The gold generator's computation is deliberately not ported into the solution,
because scoring it against itself would prove nothing.

### Corpus v1 results, n = 8 runs per arm, 12 cases and 96 slots

Levels first. Every figure comes from a run recorded in `evals/results/`.
Nothing is estimated, and cost is the amount OpenRouter actually charged.

| Metric | Target | Baseline | Lever 2 | Lever 2+3 |
|---|---|---|---|---|
| Field accuracy | at least 90% | 95.31% | 96.74% | 96.88% |
| Hallucination (asserted denom.) | at most 2% | 2.87% | 1.88% | 2.02% |
| Triage decision accuracy | n/a | 90.62% | 89.58% | **100.00%** |
| Cost per case | n/a | $0.00013 | $0.00040 | $0.00060 |
| Hard failures | n/a | 0 | 0 | 0 |

Verdicts against the baseline, under the rule enforced in
[`evals/compare.py`](evals/compare.py):

| Metric | Delta | Noise floor | p | Verdict |
|---|---|---|---|---|
| Field accuracy | 1.56pp higher | 2.08 | 0.003 | within noise |
| Hallucination | 0.86pp lower | 2.30 | 0.061 | within noise |
| Triage accuracy | **9.38pp higher** | 8.33 | 0.000 | **improvement** |
| Cost per case | 4.6x higher | n/a | 0.000 | **regression** |

Lever 3's own incremental contribution, measured against lever 2 rather than
against the baseline, so it is not credited with lever 2's work:

| Metric | Lever 2 | Lever 2+3 | Delta | p | Verdict |
|---|---|---|---|---|---|
| Triage accuracy | 89.58% | **100.00%** | 10.42pp higher | 0.000 | **improvement** |
| Field accuracy | 96.74% | 96.88% | 0.13pp | 1.000 | within noise |
| Hallucination | 1.88% | 2.02% | 0.14pp higher | 0.840 | within noise |
| Cost per case | $0.00040 | $0.00060 | 1.5x higher | 0.000 | regression |

**Lever 3 is the first lever to clear the bar.** Triage reaches 100.00% on every
one of the 8 runs, with zero variance, against a baseline that sat at 90.62%
with an 8.33 point spread. It leaves field accuracy and hallucination untouched,
which is what lever isolation should look like: it was built to fix triage and
it moved triage.

That result was checked for the obvious way it could be hollow. Lever 3 splits
the work so the model evaluates the four capacity criteria and code applies only
the published boolean formula. If the formula were carrying the score, the
result would prove nothing. Across all 96 case-decisions the model's own
decision agreed with the rule **96 out of 96 times**, and the rule corrected the
model on **zero** occasions. The formula contributed nothing to the number. On
case_06, the systematic timeline-conflict failure that neither the baseline nor
lever 2 ever gets right, the model derived the at-capacity window itself in 8
runs out of 8:

> "All three committed projects run concurrently from 2026-10-01 (Foothills
> start) to 2026-12-10 (Clear Creek end), which is the maximum of 3. The new
> window (2026-11-01 to 2027-02-28) overlaps that period."

That window matches what `derive_triage()` computes, and it was reached without
being given it.

**Lever 2 is still not reported as an improvement.** Its two headline deltas
remain smaller than the run-to-run spread even though the permutation test now
puts both at p below 0.05. The rule requires a delta to clear the spread, and it
is applied as written rather than relaxed once the numbers became suggestive.
One statement about levels rather than deltas, which the rule does not cover:
lever 2's mean hallucination of 1.88% is under the 2% target and the baseline's
2.87% is not, at 3 of 8 runs versus 0 of 8.

### Corpus v2 results, 30 cases and 240 slots (headline arms n = 8, others n = 5)

v1 results above are kept exactly as measured. These are reported alongside
them, never replacing them, because the corpus changed and a lever effect must
not be confused with that change. The noise floor below is measured on v2, not
carried over from v1.

The two headline arms are measured at **n=8**; the intermediate arms at n=5.

| Metric | Target | Baseline (n=8) | Lever 1 | Lever 2 | Lever 2b | 2+3+4 | **2b+3+4 final (n=8)** |
|---|---|---|---|---|---|---|---|
| Field accuracy | at least 90% | 96.98% | 96.67% | 95.25% | 97.25% | 95.67% | **97.45%** |
| Hallucination | at most 2% | 1.00% | 1.04% | 0.89% | 0.89% | 0.89% | **0.89%** |
| Triage accuracy | n/a | 77.92% | 80.00% | 80.00% | 76.67% | 98.00% | **97.50%** |
| Cost per case | n/a | $0.00012 | $0.00012 | $0.00037 | $0.00038 | $0.00058 | **$0.00058** |
| Hard failures | n/a | 0 | 1 | 0 | 0 | 0 | **0** |

**The headline, at n=8 per arm:** triage 77.92% to **97.50%**, 19.58 points
higher, against a measured noise floor of 10.00, at **p = 0.000155**. That is
the minimum p this test can return at n=8, because the two arms do not overlap
at all: the baseline ranges 73.33 to 83.33 across its eight runs and the final
configuration ranges 93.33 to 100.00 across its eight. Not a single baseline
run reaches a single solution run.

Lever 2b is lever 2 with one reconciliation rule revised after measurement. It
is a separate arm rather than an edit, so the lever 2 numbers above are the
originals rather than being quietly replaced.

Verdicts against the baseline:

| Arm | Metric | Delta | Floor | p | Verdict |
|---|---|---|---|---|---|
| Lever 1 | field accuracy | +0.25pp | 2.50 | 0.770 | within noise |
| Lever 1 | hallucination | 0.00pp | 0.47 | 0.976 | within noise |
| Lever 1 | triage | +2.00pp | 10.00 | 0.643 | within noise |
| Lever 1 | cost | none | n/a | 0.103 | within noise |
| Lever 2 | field accuracy | **1.58pp lower** | 1.25 | 0.008 | **regression** |
| Lever 2 | hallucination | 0.18pp lower | 0.45 | 0.063 | within noise |
| Lever 2 | cost | 3.1x higher | n/a | 0.008 | regression |
| Levers 2+3+4 | triage | **20.00pp higher** | 10.00 | 0.008 | **improvement** |
| Levers 2+3+4 | field accuracy | 1.17pp lower | 1.25 | 0.024 | within noise |
| Levers 2+3+4 | cost | 4.8x higher | n/a | 0.008 | regression |
| **2b+3+4 final, n=8** | triage | **19.58pp higher** | 10.00 | **0.000155** | **improvement** |
| **2b+3+4 final, n=8** | field accuracy | 0.47pp higher | 1.67 | 0.175 | within noise |
| **2b+3+4 final, n=8** | hallucination | 0.11pp lower | 0.89 | 0.199 | within noise |
| **2b+3+4 final, n=8** | cost | 4.8x higher | n/a | 0.000155 | regression |
| **2b vs 2**, full stack | field accuracy | **1.83pp higher** | 1.25 | 0.008 | **improvement** |
| **2b vs 2**, full stack | cost | none | n/a | 0.944 | within noise |

Lever 3's own incremental contribution, measured against lever 2 so it is not
credited with lever 2's work: triage 80.00% to 98.00%, **18.00pp higher**,
floor 6.67, p = 0.008, **improvement**.

**Lever 1 is the removed experiment.** Every metric is within noise, including
cost, which is what a parser that changes nothing should look like. This was
predicted from the parser's own behaviour, since pdfplumber finds tables in the
clean RFPs that already score well and finds zero in the hard case whose
quantity block is monospace text, but it was built and measured anyway rather
than dropped on a prediction. The prediction being right is not the same as
having checked.

**Lever 3 replicates, and larger.** On v1 it moved triage 9.38pp. On v2, where
the baseline triage is much weaker at 78%, it moves it 20.00pp. The harder
corpus exposes more of the capacity reasoning the baseline never does. Checked
for hollowness again. Across the final arm's eight runs the model agreed with
the boolean rule on **234 of 239** case-decisions, so the rule corrected it 5
times in 239. The formula is contributing almost nothing to the number rather
than carrying it.

**The lever 2 regression was diagnosed and fixed, and the fix is a measured
improvement.** 40 of lever 2's 42 flags were `SUPPORTED` with a null value,
which the reconciliation treated as a self-contradiction. In almost every case
the document had said plainly that there is no value, for example "the Owner
has not released a construction budget". Lever 2b abstains when the verifier
marks a field supported, returns null, **and** produces a span that is located
in the source; without a locatable span it still flags, so an unsupported claim
is not rewarded. Measured against lever 2 in the full stack: field accuracy
95.67% to **97.50%**, 1.83pp higher, p = 0.008, **improvement**, at no extra
cost (p = 0.944). That is the loop closing: measure, diagnose, revise,
re-measure, and keep both numbers.

**The original lever 2 regression, for the record.** Counting outcomes across all five runs, the baseline produces 12
incorrect and 26 missed slots, while lever 2 produces 10 incorrect, 5 missed
and 42 flagged. It converts misses into flags, and a flag counts as not correct
by the rule frozen before any measurement. The hallucination rate falls in
exchange. On v2 that trade is a bad one, because the flags cluster on fields
that are genuinely absent, where confident abstention would have scored as
correct: `case_13`, `case_25` and `case_26` estimated value account for most of
them. The verifier is reaching for "uncertain" where the honest answer is
"the document does not say".

**What the queue looks like once 2b is in.** Across the final arm's eight runs
the human review queue fires **3 times in 1,920 scored slots, 0.156%**, on
**2 distinct slots**: `case_04.trade_scope` twice and `case_06.trade_scope`
once. Lever 2 on its own flagged **42 times in 1,200 slots, 3.50%**, spread over
13 distinct slots, 30 of which were `estimated_project_value`. That is the
contrast: 2b removed the over-flagging on supported nulls, so the queue is rare
by design rather than decorative, and what reaches a human is genuine
uncertainty on one field in two cases rather than a pile of absent values the
document had already accounted for.

**The final configuration solves all three adversarial cases.** Across five
runs, every trap field scores correct 5 times out of 5, and triage is correct
5/5 on each:

| Case | Trap | Result |
|---|---|---|
| `case_12` | addendum supersedes the bid date, quoted 5 times against the correct date once | 5/5 correct |
| `case_12` | fire protection sits in an ALT column and is not base scope | 5/5 correct |
| `case_14` | addendum raises the bid bond and liability limits, superseded figures appear first | 5/5 correct |
| `case_17` | a later reply in an email thread supersedes the date in the quoted original | 5/5 correct |

Exported briefs for all three are in [`docs/sample-briefs/`](docs/sample-briefs/).

**On v2 the baseline already meets both frozen targets**, 96.98% accuracy
against 90% and 1.00% hallucination against 2%, both at n=8. The remaining
headroom is
almost entirely triage, which is where lever 3 delivers.

### Lever verdicts, across both corpora

Each row names the corpus its evidence comes from, because the same lever does
not always give the same answer on both.

| Lever | Measured on | Verdict |
|---|---|---|
| **1. Document parsing** | v2, n=8 vs 5 | **Removed experiment.** Flat on every metric: field accuracy p=0.770, hallucination p=0.976, triage p=0.643, cost unchanged p=0.103. Predicted flat and measured anyway, which mattered, because the prediction had already been wrong once about whether the lever was wired at all. |
| **2. Verification with span checking** | v1, n=8; v2, n=5 | **Superseded by 2b.** On v1 both headline deltas were within noise. On v2 it **regressed** field accuracy by 1.58pp (p=0.008), by converting 26 missed slots into 42 flagged ones. Kept as an arm so the before and after remain comparable. |
| **2b. Verification, revised** | v2, n=5 standalone and n=8 in the final stack | **Improvement over lever 2.** Abstains when the verifier marks a field supported, returns null, and produces a span that locates in the source. Field accuracy 95.67% to 97.50% in the full stack, +1.83pp, p=0.008, at no extra cost (p=0.944). |
| **3. Structured triage** | v1, n=8; v2, n=8 | **The win, and it replicates.** v1 triage +9.38pp; v2 +19.58pp at p=0.000155 with the two arms completely disjoint. Verified model-driven both times: the model agreed with the boolean rule on 96 of 96 decisions on v1 and 234 of 239 on v2. |
| **4. Estimator brief** | v2, in the final stack | **No measurable effect on the field metrics by construction**, since it renders already-verified fields and makes no model call. Judged as an artifact instead: see [`docs/sample-briefs/`](docs/sample-briefs/). |

### Two findings from corpus v1 that shaped the project

Both were measured on v1. The second held on v2; the first got stronger.

**The baseline already clears the field-accuracy bar.** The 90% target, frozen
before measurement, is met by a single untooled call. On v1 the bar it *missed*
was hallucination, at 2.87% against a 2% target, which is what pointed the work
at abstention discipline and triage. **On v2 the baseline clears that bar too**,
at 1.00%, so by the final corpus the only bar left unmet is one the frozen
targets never set: triage.

**Temperature 0 is not deterministic here.** Re-running the identical config
spread v1 field accuracy by 2.08 percentage points (2 slots, sd 0.86), so any
lever delta below roughly 2pp is indistinguishable from noise at n=1. That
2.08pp figure is the **v1** floor and governs nothing on v2, where the floor is
measured separately per comparison and came out at 1.67pp for field accuracy
and 10.00pp for triage. Comparisons use n=8 per arm on both corpora's headline
results. Triage is noisier than accuracy on both: on v1 it held at 91.67%
across five baseline runs before a sixth returned 83.33%, so the earlier claim
that baseline triage had zero variance did not survive the larger sample.

### What lever 2 changed on corpus v1

Across 752 field verifications: 90.4% were kept with a span found verbatim in
the source, 6.4% abstained because the source was silent, 2.8% abstained
because the source explicitly said the thing does not exist, and 0.4% were
flagged as supported but null.

| Slot | Baseline | Lever 2 | Effect |
|---|---|---|---|
| `case_08.bond_insurance` | 8/8 failed | 0/8 | fixed |
| `case_10.trade_scope` (the hallucination) | 8/8 failed | 0/8 | fixed |
| `case_02.estimated_project_value` | 7/8 failed | 5/8 | improved |
| `case_02.bond_insurance` | 1/8 failed | 0/8 | fixed |
| `case_06.trade_scope` | 1/8 failed | 0/8 | fixed |
| `case_04.project_title` | 8/8 failed | 8/8 | unchanged |
| `case_05.project_title` | 3/8 failed | 5/8 | **worse** |
| `case_12.walkthrough_date` | 0/8 failed | 7/8 | **introduced** |

The `EXPLICITLY_NONE` status added to fix case 08 is over-applied. Addendum 2.2
of case 12 says the walk-through "held September 30, 2026 is not rescheduled.
No additional walk-through will be held." The verifier reads the second
sentence and nulls the field, but the walk-through did happen, on the date gold
records. The fix that gained one point systematically costs another. That is
most of why the accuracy gain stays inside the noise band, and it is being
addressed as a separately measured revision rather than folded in silently.

`case_04.project_title` fails in every run of both arms: the model appends the
bid-package code to the title. It is scored strictly and documented as harsh
rather than quietly softened.

The human-review path fired on one field in three of eight runs
(`case_02.estimated_project_value`). It is a real checkpoint and it appears in
the traces, but it is rarer than the design implies.

Notably, the baseline **passed both headline traps in case 12**: it found the
Addendum No. 2 date rather than the five copies of the superseded one, and kept
fire protection out of the base scope.

## Tools disclosure

| Tool | Used for |
|---|---|
| Claude Code (Opus 5) | all development in this repo, driven interactively |
| **OpenRouter API** | the agent itself (baseline and solution). The only external service the agent calls. |
| **`z-ai/glm-5.3-flash`** | the model under test, via OpenRouter |
| Python 3.12 via `uv` | pinned runtime, exact versions in `requirements.txt` |
| `reportlab` | generating the synthetic RFP PDFs |
| `pdfplumber` | PDF text extraction |
| `gh` CLI | repo creation |

The agent client is stdlib `urllib`. There is no vendor SDK, no vector database,
and no orchestration framework. Nine pinned packages total.

### Model and routing

| | |
|---|---|
| Model | `z-ai/glm-5.3-flash` (fallback `z-ai/glm-5.2` if structured output proves unreliable; any switch is logged in `CHANGELOG.md`) |
| Routing | `provider.only=["deepinfra"]`, `allow_fallbacks=false`, `require_parameters=true` |
| Auto Exacto | not applicable, because the provider is pinned |
| Temperature | 0 |

Routing is pinned to a single provider so the baseline and every lever run on
identical infrastructure. **Auto Exacto cannot be pinned**: OpenRouter's docs
state it runs by default on every tool-calling request and is opt-out, and it
applies only to requests that include tools, so it would never have applied to
the toolless baseline. Measured live, an unpinned toolless call routed to Z.AI
(no structured-output support) while an unpinned tool call routed to Together at
double the price. Pinning removes that confound. Full reasoning in
`evals/config.py` and `CHANGELOG.md`. The client verifies the resolved provider
against the pin on every call rather than assuming it.

## What pre-existed vs. what was built during the event

**Pre-existed:** nothing. The repository was initialized empty at the start of
the event. See the initial commit.

**Built during the event:** all of it. The eval corpus and its generators, the
gold answer keys and their validator, the scoring rules, the contractor
capacity model, the baseline, the harness, and the solution.

The only carried-in assets are general knowledge of how commercial mechanical
bidding works (bid bonds, spec sections, alternates, addenda) and standard
open-source libraries, both listed above.

## Traces

`traces/` holds the complete Claude Code session transcripts as raw JSONL.
Those are the authoritative record and are kept unmodified.

**[`traces/annotated/`](traces/annotated/) is a readable subset of those same
transcripts**, not a replacement for them and not a separate record. The raw
JSONL is roughly 5 MB of session events, which no reader can realistically
follow from an instruction through to a result, so four episodes are extracted
and annotated:

| Episode | What it shows |
|---|---|
| [Human checkpoint: freezing the scoring rules](traces/annotated/01-human-checkpoint-scoring-rules.md) | The agent stops and asks before any number exists, then folds in four mid-turn refinements |
| [An instruction overridden by measurement](traces/annotated/02-instruction-overridden-by-measurement.md) | An instruction that could not be followed, checked rather than obeyed, with a live 429 retry visible |
| [The loop catching its own error](traces/annotated/03-the-loop-catching-its-own-error.md) | A self-test failing and catching a defect that would have failed every location field |
| [Lever 3 verified, not assumed](traces/annotated/04-lever-3-verified-not-assumed.md) | A 100% result, then the agent testing whether its own rule was carrying the score |

Nothing in an episode is paraphrased. Everything outside a clearly marked
annotation is verbatim, long tool inputs and outputs are truncated with the
omitted character count shown, and where events are skipped inside an episode
the exact number omitted is printed. The bug episode is included deliberately:
a trajectory set showing only successes would misrepresent how the work went.

Episodes are regenerated from the raw transcript with
`python scripts/build_trace_episodes.py`, so they cannot drift from it.

Transcripts are copied by [`scripts/capture_traces.py`](scripts/capture_traces.py),
which requires session ids to be named explicitly and has **no copy-all flag by
design**: the Claude Code project directory on the development machine also
holds unrelated sessions, and `traces/` is public. Every transcript is passed
through a credential-shaped-string redactor first; what was replaced is recorded
in [`traces/REDACTIONS.md`](traces/REDACTIONS.md) so redaction is auditable
rather than silent.

## Reproducing

See [`REPRODUCE.md`](REPRODUCE.md). Commands are added there only after they
have actually been run.
