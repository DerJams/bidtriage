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

Three parts of this design come from researched industry sources rather than
from assumption. Source quality varies a great deal between them, and that is
recorded here rather than flattened, because a corpus built on a vendor blog
post and one built on a peer-reviewed study should not be presented as equally
grounded.

### 0.1 Platform invitation structure

**Well documented.** BuildingConnected's own support documentation specifies
that every invitation is sent from the single fixed address
`team@buildingconnected.com` with only the display name varying, that the
subject follows a fixed template (`Bid Invite: [Project Name] Project`), and
that the body is generated from structured project-setup fields: GC logo,
project lead name, GC company, project name, the specific bid package, a View
RFP link, accept/decline buttons, location, bid due date, description, and a
client-details block with the lead contact's name, title and phone.[^bc-invite]
[^bc-notify][^bc-gc] A GC-side outreach guide corroborates this independently,
including that a separate invitation arrives per bid package.[^southpoint]

The contrast with human-authored email is the load-bearing point. A GC-facing
estimating guide lists the fields a GC *should* remember to include in a
freehand invitation.[^meltplan] A checklist of that kind would be unnecessary
if the fields were guaranteed. BuildingConnected also ships a manual
"type an email" fallback that requires a subcontractor to re-key a freehand
invite into structured fields, a workaround that exists precisely because
direct email does not carry that structure natively.[^bc-forward]

This is why v2 rewrites the platform cases as structured and complete and
pushes the ambiguity into the attachment.

### 0.2 Bonding and insurance conventions

**Well documented, with one correction to the corpus.** Federal work under the
Miller Act requires performance and payment bonds above $150,000, with the bid
guarantee at a minimum of 20% of the bid price capped at $3M.[^far28] State and
local equivalents commonly set the bid bond at a flat 5%, with performance and
payment bonds each at 100% of contract price.[^mrsc][^scose] Surety-industry
sources converge on 5% to 10% as typical for private and municipal commercial
work.[^scalabid][^trucordia]

On liability, the widely applied **baseline is $1M per occurrence / $2M
aggregate**. The $2M/$4M figure is not a universal floor: it is what GC-facing
insurance guides specifically recommend or require for HVAC and plumbing,
because those are classified as moderate-to-higher-risk trades alongside
roofing, electrical and excavation.[^grit][^grit26][^docutrax] That distinction
is worth keeping straight, since v2 uses $2M/$4M *because the corpus is
mechanical and plumbing work*, not because it is the general standard.

### 0.3 Decline-reason criteria

**Mixed quality, and the two halves should not be cited as one thing.**

The strong half is peer-reviewed: a study of bid/no-bid decision factors finds
that small contractors rank **project size, availability of capital, client
payment timeliness, current workload, and general overhead** as the five most
critical factors.[^bidnobid] That directly supports keeping size-band and
timeline-conflict as criteria.

The geographic half is weaker. The frequently quoted figures that 80% of
accepted bids fall within 55 miles and 87.1% within 100 miles come from a
vendor bid-response toolkit citing "research on 60,000 live construction bids",
with no published methodology and no independent replication.[^itbkit] It is
directional support for geography mattering, not a measured constant, and it is
**not** peer-reviewed. The service radius in this corpus is a declared
operating parameter regardless, so nothing depends on that number being exact.

Industry bid/no-bid checklists converge on the same four filters used here:
trade or scope mismatch, geography, capacity or schedule conflict, and project
size.[^bidintell][^quantify] The four capacity criteria are therefore kept
unchanged.

### 0.4 Addenda as a failure mode

The one quantified figure available attributes roughly **20% of significant
scope gaps and pricing errors to unincorporated or partially incorporated
addenda, RFI responses, or drawing revisions**, from an internal analysis of
over 12,000 estimate QA reviews.[^mepusa] This is a single vendor's proprietary
dataset rather than an independently replicated study, so it is treated as a
directional prior. It is enough to justify a second addendum case; it is not
enough to justify making addenda a majority of the corpus, which is why the
adversarial proportion stays near 1 in 10.

Bid-date extension by addendum is separately documented as a routine
procedural event rather than an edge case.[^lacity][^pelles] The alternates
mistaken-for-base-scope failure is documented through case law showing the
mechanism and its consequences, though no source quantifies its incidence.[^cc]
[^gao]

### 0.5 What is not sourced

Deliberately recorded so the corpus is not read as more grounded than it is:

- **Channel mix** (platform vs direct email vs phone) for small mechanical
  subcontractors specifically was not found. Available figures are vendor-cited
  and do not isolate this segment.
- **Base rate for how often addenda change bid dates** was not quantified
  anywhere reviewed. The evidence is qualitative only.
- **Frequency of the alternates error** is undocumented; only the mechanism is.
- **Private-sector engineer's-estimate disclosure practice** is essentially
  absent from the literature, so how often a private GC shares a budget with
  mechanical bidders is unknown. The corpus varies this rather than asserting a
  rate.

The practical consequence: structural and qualitative findings (template
consistency, CSI division scoping, bond and insurance percentage ranges) are
weighted heavily in the corpus design, and the thinner quantitative claims
about failure-mode frequency are treated as directional priors only.

### References

[^meltplan]: [How to Send Bid Invitations to Subcontractors, a GC's Step-by-Step ITB Guide](https://www.meltplan.com/blogs/how-to-send-bid-invitations-to-subcontractors-a-gc-s-step-by-step-itb-guide)
[^bc-invite]: [I received an invitation to bid. What should I do?](https://support.buildingconnected.com/hc/en-us/articles/360021597733-I-received-an-invitation-to-bid-What-should-I-do)
[^bc-notify]: [What do bid invitations look like when sent from BuildingConnected?](https://support.buildingconnected.com/hc/en-us/articles/360022100314-What-do-bid-invitations-look-when-they-are-sent-from-BuildingConnected)
[^bc-gc]: [What emails will my bidders receive? (General Contractor)](https://support.buildingconnected.com/hc/en-us/articles/360014617594-What-emails-will-my-bidders-receive-General-Contractor)
[^bc-forward]: [How to write an email to forward a bid into BuildingConnected](https://support.buildingconnected.com/hc/en-us/articles/360047668673-How-to-write-an-email-to-forward-a-bid-into-BuildingConnected-Bid-Board-Pro)
[^southpoint]: [Diverse Subcontractor and Supplier Outreach, Navigating BuildingConnected](https://southpointconstructors.com/wp-content/uploads/2022/11/SPC_SE-Connector-Navigating-BuildingConnected_221117.pdf)
[^far28]: [FAR Part 28, Bonds and Insurance](https://www.acquisition.gov/far/part-28)
[^mrsc]: [Guarantees, Bonds, and Retainage, MRSC](https://mrsc.org/explore-topics/procurement/contract-administration/guarantees-bonds-retainage)
[^scose]: [Guide to Bid, Payment, and Performance Bonds, SC Procurement](https://procurement.sc.gov/files/ose/Guide_to_Bid,_Payment,_and_Performance_Bonds_0.pdf)
[^scalabid]: [Bid Bond vs Performance Bond: When Each Is Required](https://www.scalabid.com/resources/bid-bond-vs-performance-bond-when)
[^trucordia]: [Understanding Bid, Performance, and Payment Bonds for Contractors](https://www.trucordia.com/blog/understanding-bid-performance-and-payment-bonds-for-contractors)
[^grit]: [Subcontractor Insurance Requirements (What GCs Must Verify)](https://gritinsurance.com/blog/subcontractor-insurance-requirements-what-general-contractors-gcs-and-subcontractors-must-know)
[^grit26]: [Subcontractor Insurance Requirements, What GCs Are Demanding](https://gritinsurance.com/blog/subcontractor-insurance-requirements-2026?hs_amp=true)
[^docutrax]: [Subcontractor Insurance Requirements: A GC's Guide](https://www.docutrax.com/resources/guides/subcontractor-insurance-requirements)
[^bidnobid]: [Critical Factors Influencing the Bid/no-Bid Decisions of Contractors](https://www.tandfonline.com/doi/abs/10.1080/15578771.2024.2332237) (peer-reviewed)
[^itbkit]: [ITB Response Kit 2026](https://constructionbids.ai/kits/itb-response-scope-letter) (vendor toolkit, methodology not published)
[^bidintell]: [Bid No Bid Checklist for Specialty Subcontractors](https://bidintell.ai/bid-no-bid-checklist)
[^quantify]: [Bid No-Bid Decision Criteria: A Contractor's Framework](https://quantifyna.com/bid-no-bid-decision-criteria/)
[^mepusa]: [How Estimators Handle Drawing Revisions, Addenda, RFIs](https://mepestimationusa.com/guides/drawing-revisions/) (single vendor's proprietary dataset)
[^lacity]: [Responding to Inquiries and Issuing Addenda, LA Project Delivery Manual](https://projectdeliverymanual.engineering.lacity.gov/chapter-13-advertising-project-bids/135-responding-inquiries-and-issuing-addend)
[^pelles]: [Estimating from Addenda, MEP Bid Process](https://www.pelles.ai/university/articles/estimating-from-addenda)
[^cc]: [Mistake in bid price renders bid non-compliant](https://canada.constructconnect.com/joc/news/others/2008/01/mistake-in-bid-price-although-compliant-renders-bid-non-compliant)
[^gao]: [Herman Construction Group, Inc., GAO B-415480](https://www.gao.gov/products/b-415480)

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
