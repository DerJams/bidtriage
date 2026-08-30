# Corpus v2 design (proposal, not yet built)

Revision and expansion of the eval set from 12 cases to about 30, driven by
research on how real bid solicitations actually arrive. Written before any case
is authored so the design can be corrected cheaply.

**Measurement discipline for this phase.** The corpus revision and the lever
work are separate causes with separate effects. Both sets of numbers are
reported: the v1 (12-case) results stay in the repository exactly as measured,
and the v2 results are reported alongside them rather than replacing them. A
changelog row that showed only post-expansion numbers would conflate "the eval
set changed" with "the lever worked".

---

## 0. Provenance

Three parts of this design come from **researched industry sources**, not from
assumption or from what seemed plausible while writing synthetic data:

1. **Platform invitation structure.** That BuildingConnected-style invitations
   are system-generated from structured project fields, with a fixed sender, a
   templated subject, and a body carrying project name, bid package, due date,
   location, and lead contact, and that the ambiguity in platform-sourced work
   lives in the attached scope documents rather than in the notification email.
2. **Bonding and insurance conventions.** Bid bonds of 5 to 10% on private and
   municipal work and up to 20% on federal Miller Act work; performance and
   payment bonds at 100% of contract price; and commercial general liability at
   2M per occurrence and 4M aggregate for HVAC and plumbing, those being
   classified as higher-risk trades, rather than the 1M/2M baseline.
3. **Decline-reason criteria.** That project size, workload, and geography are
   the dominant real drivers when a contractor declines to bid, and that 80% of
   accepted bids fall within 55 miles. This is peer-reviewed work, and it is why
   the four capacity criteria are being kept unchanged rather than revised.

This matters for reading the eval set. The corpus is entirely synthetic, but its
*shape* is not invented: the document structures, the commercial terms, and the
triage criteria follow documented practice. A corpus whose conventions were
guessed would measure how well a model handles my guesses.

> **Citations pending.** The specific sources are to be added here verbatim. They
> are deliberately not paraphrased or named from memory in the meantime, because
> a plausible-looking citation that turns out to be wrong is worse than an
> acknowledged gap. Until this block is filled in, treat the three items above as
> sourced but uncited.

## 1. What the research changes

### 1.1 Portal cases model the wrong thing

Platform invitations (BuildingConnected and similar) are system-generated from
structured project fields. They have a fixed sender, a templated subject, and a
body carrying project name, bid package, due date, location, and lead contact.
They are consistent and field-rich, not sparse.

The current cases 10 and 11 treat the notification itself as the ambiguous
artifact. That is backwards. In platform-sourced work the ambiguity lives in the
attached scope documents.

**Change.** Rewrite platform cases as structured and complete, and push the
missing or ambiguous information into an attachment. Human-authored GC emails
remain the variable, omission-prone channel.

**Consequence: multi-document cases.** A platform case is now an email plus an
attachment. The harness currently passes exactly one document per case. This
needs a real change:

- gold gains `sources: [...]` (ordered) alongside the existing single `source`
- `evals/run.py` assembles them with explicit delimiters, so the model can tell
  the invitation from the attachment
- `author_gold.py` span validation checks a span against the concatenation
- lever 1's parser handles a mixed email plus PDF case

### 1.2 Commercial terms need aligning

| Term | Current corpus | Documented convention |
|---|---|---|
| Bid bond, private and municipal | flat 5% everywhere | 5 to 10% |
| Bid bond, federal (Miller Act) | absent | up to 20% |
| Performance bond | 100% | 100% of contract price |
| Payment bond | 100% | 100% of contract price |
| CGL, HVAC and plumbing | single limit, 1M to 5M | **2M per occurrence / 4M aggregate** as the floor, these being higher-risk trades |

**Consequence: the bond field shape changes.** `gl_limit_usd` is a single
number and cannot express per-occurrence and aggregate. It becomes:

```json
{"required": true, "bid_bond_pct": 5, "performance_bond_pct": 100,
 "payment_bond_pct": 100,
 "gl_per_occurrence_usd": 2000000, "gl_aggregate_usd": 4000000}
```

This is an amendment to a frozen rule and goes in the amendments table in
`scoring-rules.md` with its reason, not silently. It touches the normalizer, the
output schema, all gold keys, and the selftest. The key-set rule still applies:
a source stating only a per-occurrence limit yields a dict without the aggregate
key, and inventing the aggregate remains a hallucination inside the field.

Bid bonds stop being a flat 5% and vary across 5, 10, and 20% by procurement
type, so the field stops being guessable from a single memorised value.

### 1.3 Addenda deserve more than one case

Roughly 20% of significant scope gaps are attributed to unincorporated or
partially incorporated addenda. Case 12's trap is well founded, and one case is
too thin a basis for a failure mode that common.

**Change.** At least one more case where an addendum changes a **material term**
rather than a date. Candidates: bonding requirement changed, a scope item moved
from alternate into base bid, or a quantity revised.

### 1.4 Capacity criteria stay as they are

Project size, workload, and geography are the dominant real decline drivers, and
80% of accepted bids fall within 55 miles. The four criteria (trade fit, radius,
size band, timeline conflict) are validated. No change.

---

## 2. Adversarial proportion

v1 has 1 adversarial case in 12. Holding that proportion, v2 should carry about
2 to 3, not a corpus of traps. Proposed: 3 in 30, which is 1 in 10.

| Case | Trap |
|---|---|
| existing case 12 | addendum supersedes bid date, plus alternates read as base scope |
| new | addendum changes a material term |
| new | a later email in a thread supersedes an earlier stated date, with no addendum involved |

Everything else is ordinary work that happens to be messy in realistic ways.

---

## 3. Proposed case inventory

Expansion introduces new document **shapes** and **failure modes** rather than
new values in existing templates. A case that only changes names and numbers
adds slots without adding information.

### Revised from v1 (12)

| Case | Change |
|---|---|
| 01 to 09 | commercial terms aligned; CGL split to per-occurrence and aggregate; bid bond varied by procurement type |
| 10, 11 | **rewritten**: structured, complete platform invitations plus an attachment carrying the ambiguity |
| 12 | kept; commercial terms aligned |

### New (18)

| # | Shape | Failure mode probed |
|---|---|---|
| 13 | platform invitation + scope attachment | scope stated only as CSI divisions (22, 23, 25) |
| 14 | RFP PDF with addendum | **addendum changes a material term** (bond requirement) |
| 15 | federal solicitation | Miller Act bonding, 20% bid bond |
| 16 | municipal public works | prevailing wage, 10% bid bond |
| 17 | email thread | **later reply supersedes an earlier due date**, no addendum |
| 18 | GC scope sheet | fixed-width bid form in the email body |
| 19 | design-build RFP | allowances, and a not-to-exceed rather than a range |
| 20 | RFP PDF | walk-through is optional, not mandatory |
| 21 | platform invitation + attachment | two locations, site versus owner HQ |
| 22 | email | value appears only in an attached bid form |
| 23 | RFP PDF | multi-phase project, phased construction windows |
| 24 | email | walk-through "by appointment", no date, an abstention test |
| 25 | platform invitation | alternates-only pricing request |
| 26 | RFP PDF | negotiated work, no bonding and no bid date |
| 27 | email | very short turnaround, terse and urgent |
| 28 | RFP PDF | value given as a not-to-exceed ceiling |
| 29 | platform invitation + attachment | trade scope split across invitation and attachment |
| 30 | email | owner and GC named separately, which is the client |

Distribution: about 11 email, about 9 PDF, about 6 platform-plus-attachment,
plus the revised originals. Triage outcomes rebalanced so each of the four
criteria still fails in more than one case, and `insufficient_information`
remains reachable.

---

## 4. Effect on measurement

30 cases at 8 fields is **240 slots**, up from 96.

This should *help*. Per-run variance falls roughly with the square root of slot
count: observed sd of 0.86pp at 96 slots scales to about **0.54pp at 240 slots**.
A smaller noise floor is exactly what the lever comparisons need, since lever 2's
1.43pp effect currently sits below a 2.08pp floor.

Measured cost per run, from completed arms:

| Arm | s/case measured | 30 cases, one run | n=8 |
|---|---|---|---|
| baseline | 11.3 | 5.7 min | 45 min |
| lever 1 | about 12 | 6 min | 48 min |
| lever 2 | 28.4 | 14.2 min | 114 min |
| lever 2+3 | 65 | 32.5 min | 260 min |

About 7.8 hours sequential for four arms at n=8, before lever 4 adds a call.

---

## 5. Sample size and concurrency (measured, decided)

**n=5 on 30 cases**, not n=8. A 240-slot corpus should cut per-run variance
relative to 96 slots, so n=5 on the expanded set should resolve lever effects at
least as well as n=8 did on the small one, at about 60% of the run time. This is
a visible measurement decision, recorded here and in `CHANGELOG.md` rather than
quietly applied.

**The noise floor will be measured on the new corpus, not carried over.** The
2.08pp figure belongs to the 12-case set and governs nothing here. The predicted
0.54pp is a prediction and is not used either. `evals/compare.py` derives the
floor from the observed spreads of the two arms actually being compared, so it
is empirical on whatever set it is run against.

### Concurrency: measured, not assumed

The 7.8 hour figure assumed arms run one after another. They do not have to.
These are I/O-bound API calls, so the question is whether parallel streams
multiply throughput or simply collide with rate limiting.

First, what the slowdown is NOT. Retry rate per call is essentially constant
across arms: 0.312, 0.318, 0.287 retries per call for baseline, lever 2, and
lever 2+3. Backoff is not compounding. Latency tracks tokens per call at roughly
0.010 s/token in every arm, so the per-call cost is throughput-bound. Retries
account for only about 6 to 7% of wall clock.

Measured with three worker processes on an identical 6-case subset:

| | s/case | retries/case |
|---|---|---|
| solo | 12.14 | 0.00 |
| 3 concurrent | **3.41** | 0.22 |

**3.56x speedup at 3 workers.** Concurrency raises the retry rate slightly and
nowhere near enough to matter. Revised estimate for the full v2 phase at n=5
with concurrent arms: roughly **1.5 to 2 hours** rather than 4.9 sequential.

### A bug this test found

The first concurrency attempt silently lost a run. Results filenames were built
from a second-resolution timestamp, so two processes starting in the same second
produced the same filename and one overwrote the other. Fixed with microseconds
plus pid plus an exists() guard. Worth recording because the failure mode is
silent: the arm would simply have contained fewer runs than the label claimed,
with nothing in any log to say so.
