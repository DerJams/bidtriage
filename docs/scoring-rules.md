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
  (`inc`, `llc`, `ltd`, `co`, `corp`) before comparison. Then exact equality.
- **`iso_date`** — both sides parsed to `YYYY-MM-DD`. Time-of-day is carried in
  gold under `extra.time_local` but is **not scored**.
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
