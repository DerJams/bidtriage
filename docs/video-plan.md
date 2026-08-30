# Solution video: shot list, live command sequence, narration outline

Target length 5 minutes, aiming for about 4:30 so there is room to breathe.

Everything in the live sequence runs **without spending a single API call**,
because the results are committed. That matters on camera: the numbers are
recomputed in front of the viewer from recorded runs rather than read off a
slide. Measured timings are given per command so the pacing is predictable.

The required beats are: problem and baseline, one realistic execution end to
end, the final comparison, the changelog, the biggest contributor, and one
removed experiment. All six are covered below and marked.

---

## Before recording

```bash
cd bidtriage
git pull
export PY=./.venv/Scripts/python.exe     # ./.venv/bin/python on macOS and Linux
clear
```

Terminal at roughly 110 columns so the comparison table does not wrap. Font
large enough that the `verdict` column is readable, since that column is the
point of the whole harness.

---

## Shot list

| # | Time | Shot | What is on screen |
|---|---|---|---|
| 1 | 0:00 to 0:35 | Talking head or slide | The user and the bottleneck. No terminal yet. |
| 2 | 0:35 to 1:05 | Editor, `data/synthetic/emails/case_12.pdf` rendered, or the source text | The hard case. Point at the superseded date and the ALT 1 column. |
| 3 | 1:05 to 1:30 | Terminal, command A | Self-test. Establishes that scoring is deterministic and checked. |
| 4 | 1:30 to 2:15 | Terminal, command B | One case end to end, live. The realistic execution beat. |
| 5 | 2:15 to 2:50 | Terminal, command C | The estimator brief for that same case. The user-facing artifact. |
| 6 | 2:50 to 3:35 | Terminal, command D | The final comparison table. The headline result. |
| 7 | 3:35 to 4:05 | Terminal, command E | Lever 3 verified model-driven, 234 of 239. |
| 8 | 4:05 to 4:30 | Editor, `CHANGELOG.md` | The changelog beat, and the removed experiment. |

---

## Live command sequence

### A. Prove the scoring is deterministic and tested (measured 0.14 s)

```bash
$PY -m evals.harness.selftest
```

One line of output. Say what it covers while it runs: the normalizers, the
scorer outcomes, and the traps.

### B. One realistic execution, end to end (about 60 s, costs about $0.0007)

This is the one command in the sequence that calls the API. It is a single
case, so it is cheap and fast enough to watch.

```bash
BIDTRIAGE_CORPUS=v2 \
BIDTRIAGE_LEVERS=lever2b_verify,lever3_triage,lever4_brief \
  $PY -m evals.run --target solution --cases case_12 --label demo
```

Watch for: `provider=DeepInfra` proving the pin held, the per-case score, the
retry count, and the actual charged cost.

If the network is unreliable on the day, skip B and use the committed run
instead. Nothing downstream depends on B having just executed.

### C. The artifact a person actually receives (instant)

```bash
cat docs/sample-briefs/case_06_no_bid.txt   # from the v1 corpus
```

Scroll slowly. The three things to point at: the **NO BID** recommendation with
the timeline reason spelled out, the **NOT CONFIRMED** marker on the trade
scope line, and the source citations at the bottom.

Say plainly that the marked field is a real mistake the system made and caught,
not a staged example.

### D. The final comparison (measured 1.5 s)

```bash
BIDTRIAGE_CORPUS=v2 \
  $PY -m evals.compare --a baseline --b lever2b_verify+lever3_triage+lever4_brief
```

The single most important frame in the video. Let it sit on screen.

### E. The result checked for hollowness (instant)

```bash
$PY - <<'EOF'
import json, glob, pathlib
runs = [json.loads(pathlib.Path(f).read_text(encoding='utf-8'))
        for f in glob.glob('evals/results/*_solution*.json')
        if 'SUPERSEDED' not in f and 'CONCTEST' not in f]
runs = [r for r in runs if r.get('n_cases') == 30
        and set(r.get('active_levers') or []) == {'lever2b_verify', 'lever3_triage', 'lever4_brief'}]
agree = sum(1 for r in runs for m in r['call_meta'].values()
            if (m.get('triage_audit') or {}).get('model_agreed_with_rule'))
total = sum(1 for r in runs for m in r['call_meta'].values() if m.get('triage_audit'))
print("model agreed with the boolean rule on %d of %d decisions" % (agree, total))
EOF
```

Prints `model agreed with the boolean rule on 234 of 239 decisions`.

---

## Narration outline

### 0:00 Problem and baseline (beat 1 and 2)

> A small commercial mechanical contractor gets five or six shots a year at
> work worth bidding. Every inbound request goes through one operations
> coordinator, who reads it, re-keys eight fields into a spreadsheet, and
> decides whether it is worth an estimator's time. Twenty to forty minutes
> each, and the errors are the expensive part. A missed addendum that moved a
> bid date does not cost you time, it costs you the job.

> Here is the hard case in my eval set. The bid date appears five times on this
> cover sheet and in the page footers. It is wrong. The date that governs is on
> page four, in an addendum. And this quantity column looks like base scope,
> but the zeros mean it is an alternate, for a trade this contractor does not
> even self-perform.

> The baseline is what you would build first: paste the text into one model
> call and ask for the fields. On the full thirty case set **it scores 97
> percent**, and its hallucination rate is one percent. That surprised me. The
> bars I had frozen before measuring were ninety and two, so the obvious
> approach already clears both of them.

### 1:05 The realistic execution (beat 3 and 4)

> Scoring is deterministic. No model grades another model anywhere in this
> harness, and the self-test runs before anything costs money.

> Here is one case, end to end. Extraction, then a verification pass that has
> to produce a quote and have that quote found in the source document, then a
> triage decision against the contractor's actual capacity.

### 2:15 The artifact (beat 5)

> This is what the coordinator receives. No bid, because the construction
> window overlaps a period when all three committed crews are already running.

> And this line matters. The model got the trade scope wrong here. It added
> piping that is not in the document. Verification could not confirm it, so the
> brief marks it NOT CONFIRMED instead of presenting it as fact. That is a real
> error the system caught on itself.

### 2:50 The comparison (beat 6)

> Here is the whole result. Temperature zero is not deterministic on this
> provider, so a single run is not a measurement. Every number here is eight
> runs per arm, and the verdict column is computed by an exact permutation
> test, not by me looking at it.

> Field accuracy went up. Hallucination went down. **Both are reported as
> within noise**, because neither delta clears the run-to-run spread, and I am
> not going to call something an improvement because it points the right way.

> Triage is different. Seventy eight percent to ninety seven and a half, p
> equals zero point zero zero zero one five five. That is the smallest number
> this test can return at eight runs, and it is that small because the two arms
> do not overlap at all. My worst solution run beats my best baseline run.

### 3:35 The biggest contributor, and why I do not trust it yet (beat 7)

> Lever three is the biggest contributor, and it has an obvious way to be
> hollow. The model evaluates the four capacity criteria; my code applies the
> boolean formula. If the formula were doing the work, this number would prove
> nothing.

> So I checked. Across two hundred and thirty nine decisions the model agreed
> with the rule two hundred and thirty four times. The rule corrected it five
> times out of two hundred and thirty nine, so it is not carrying the result.
> The model worked out the at-capacity window itself.

### 4:05 The changelog and the removed experiment (beat 8)

> Everything is in the changelog, including what did not work. Lever one was
> proper PDF parsing with table extraction. I built it and measured it anyway,
> even though the evidence already said it would be flat: the parser finds
> tables in the four clean RFPs, which already score near perfectly, and finds
> **zero** tables in the hard case, because its quantity block is monospace
> text. It could only help where help was not needed.

> The honest summary is that the baseline was already good, the win is in
> triage and in refusing to guess, and it costs about four and a half times
> more per case to get it.

---

## Notes for the edit

- Do not cut the WITHIN NOISE rows out of shot 6. They are the credibility of
  the whole thing.
- If shot 4 runs long because of a rate-limit retry, keep it. A visible retry
  is honest and the client counts them.
- The lever 1 numbers are now measured and can be stated directly: flat on
  every metric, field accuracy p = 0.770, hallucination p = 0.976, triage
  p = 0.643, cost unchanged.
- The brief shown in shot 5 is from the v1 corpus, because it is the one that
  contains a real NOT CONFIRMED marker. The v2 briefs are clean, which is a
  better result and a worse demo. Say which corpus it is from rather than
  glossing it.
- If there is room, the strongest extra beat is lever 2b: the one regression
  the project found in its own work, diagnosed to a single reconciliation rule
  and fixed for a measured 1.83 point gain at no extra cost. It shows the loop
  closing rather than just running.
