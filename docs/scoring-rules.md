# Scoring rules (frozen before measurement)

These definitions were written and committed **before** the baseline was run.
Git history is the proof: this file predates any file in `evals/results/`.

Scoring is fully deterministic. There is no LLM judge anywhere in the harness.

---

## 1. Scored fields

Eight required fields per case, 12 cases -> **96 scored slots**.

| Field | Match rule |
|---|---|
| `client_name` | `normalized_string` |
| `project_title` | `normalized_string` |
| `trade_scope` | `token_set` (closed vocabulary) |
| `location` | `normalized_string` |
| `bid_due_date` | `iso_date` |
| `estimated_project_value` | `currency_interval` |
| `bond_insurance` | `bond_dict` |
| `walkthrough_date` | `iso_date` |

### Match rule definitions

- **`normalized_string`** — casefold, collapse internal whitespace, strip
  leading/trailing punctuation, drop a trailing corporate suffix
  (`inc`, `llc`, `ltd`, `corp`) before comparison. Then exact equality.
  `co` is deliberately NOT a stripped suffix: it is also the Colorado state
  abbreviation, and stripping it truncated `denver, co` to `denver`.
- **`us_city_state`** (`location` only) — reduce to `city, st`, taking the
  trailing `City, ST` match. A target answering "Cascade Ridge Middle School,
  Arvada, CO" has found the right place and named the building too; city+state
  is the unit the radius check keys on, since the profile's distance table is
  keyed exactly that way. Extra site detail neither helps nor hurts.
- **`iso_date`** — both sides parsed to `YYYY-MM-DD`. Accepts ISO datetimes
  (`2026-09-25T14:00:00-06:00`), ISO dates, `September 25, 2026`, `25 September
  2026`, and `9/25/2026`. Time-of-day is carried in gold under
  `extra.time_local` but is **not scored**.
- **`currency_interval`** — normalized to `{low, high, currency}` as integer USD.
  A point estimate is the degenerate interval `low == high`. Exact equality of
  both bounds. `"$1.2M"`, `"1,200,000"`, and `"approximately $1.2 million"` all
  normalize to `1200000`.
- **`token_set`** — set equality against the closed trade vocabulary:
  `hvac`, `plumbing`, `piping`, `sheet_metal`, `controls`, `refrigeration`,
  `fire_protection`. Any token outside the vocabulary makes the field wrong.
- **`bond_dict`** — see section 2.

## 2. `bond_insurance` (compound field, binary score)

Gold stores a **normalized dict**, not formatted tokens:

```json
{"required": true, "bid_bond_pct": 5, "performance_bond_pct": 100,
 "payment_bond_pct": 100, "gl_limit_usd": 2000000}
```

- Extracted values are **parsed and normalized before comparison**, so `"5%"`,
  `"five percent"`, `"5 percent"`, and `5` all compare equal. Likewise
  `"$2M"`, `"2,000,000"`, and `"two million"` for `gl_limit_usd`.
- **"None required" is an explicit assertion.** Where no bonding is required,
  gold is `{"required": false}` and the system must positively state that.
  A `null`, an omitted field, or "not found" scores **wrong** — not abstained.
- Scoring is **all-or-nothing on the full dict**. One wrong GL limit fails the
  field.
- **Key-set convention.** Keys not stated in the source are **omitted** from the
  dict, and the prediction's key set must match gold's **exactly**. If a portal
  notice mentions only a bid bond, gold is `{"required": true, "bid_bond_pct": 5}`
  and nothing else. Asserting a performance bond that the source never mentions
  is a hallucination *inside* the field and fails it. This is deliberate: bond
  requirements are the field an estimator is most likely to assume from habit.
- **Per-subcomponent match results** (each bond type, GL limit) are written to
  the results JSON as diagnostics. The headline metric stays binary per field.

## 3. Per-slot outcomes

Every one of the 96 slots resolves to exactly one outcome:

| Outcome | Condition | Counts as correct? | Counts as asserted? |
|---|---|---|---|
| `correct` | gold present, prediction matches | yes | yes |
| `correct_abstention` | gold absent, prediction `null` | yes | no |
| `incorrect` | gold present, prediction present but differs | no | yes |
| `missed` | gold present, prediction `null` | no | no |
| `hallucinated` | gold absent, prediction non-`null` | no | yes |
| `flagged_for_review` | system flagged low confidence | no | **no** |

`flagged_for_review` is the deliberate tradeoff: abstaining **costs accuracy**
but **protects the hallucination rate**. If flagging were free, the verification
lever would be self-scoring. It is not free.

## 4. Metrics

**Primary — field accuracy** (target >= 90%):

```
(correct + correct_abstention) / 96
```

**Secondary — hallucination rate** (target <= 2%):

```
judged:      (incorrect + hallucinated) / asserted
diagnostic:  (incorrect + hallucinated) / 96
```

The **judged** figure uses asserted fields as the denominator. The fixed /96
figure is logged in the results JSON as a **diagnostic only**, so both views are
auditable. The harness prints **the asserted-field count alongside the rate on
every run**, so a shrinking denominator can never hide behind a falling rate.

**Secondary — minutes per intake:** a transparent proxy, **not** a measured
human time. Constants live in `evals/harness/minutes.py` and are fixed before
measurement. It is reported as a proxy everywhere it appears, and no claim in
this repo asserts observed human time.

**Cost per task:** actual API token counts from response usage objects,
multiplied by published per-token prices. Never estimated.

## 5. Triage scoring (reported separately)

Bid/no-bid is scored against `data/contractor_profile.json` and does **not**
enter the frozen field-accuracy metric. Reported as decision accuracy plus
per-criterion agreement.


---

## 6. Amendments after freezing

Honesty requires listing these rather than editing silently. Both were made
**after a single-case smoke run and before any full run was recorded**, and both
were defects in the *normalizer*, not changes to the metric, its targets, or the
gold values. Both apply identically to every target.

| When | Change | Why |
|---|---|---|
| Before first full run | `iso_date` accepts ISO datetimes | The model returned `2026-09-25T14:00:00-06:00`. A `` in the regex meant this **more precise, correct** answer scored as unparseable. A bug that penalised correctness. |
| Before first full run | `location` uses `us_city_state`, not bare string equality | The model returned `"Cascade Ridge Middle School, Arvada, CO"`. Bare equality called that wrong even though the city is right and is what the radius check consumes. Under-specification, not a metric change. |
| Before first full run | `co` removed from corporate-suffix stripping | It silently truncated every `City, CO` location. Caught by `selftest.py`. |

`project_title` was deliberately **left strict**. The model returned a title with
the bid-package number appended, which strict equality scores wrong. That is
harsh, but there is no principled canonical form to reduce a title to, and the
harshness applies equally to every target, so it does not bias any comparison.
It is called out here rather than quietly softened.
