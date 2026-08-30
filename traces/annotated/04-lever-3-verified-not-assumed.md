# Lever 3 reaches 100 percent, and the agent checks whether that is hollow

> **This is an annotated extract.** The complete, unedited transcript is in [`traces/`](../) as raw JSONL. Nothing here is paraphrased: every block below the annotations is verbatim from that file. Long tool inputs and outputs are truncated with the omitted character count shown.

## Why this episode

Lever 3 took triage from 90.62 percent to 100.00 percent with zero variance across 8 runs. The design splits work so the model evaluates four capacity criteria and code applies only a published boolean formula. If the formula were carrying the score, the result would prove nothing, so the agent immediately tested exactly that rather than reporting the headline.

## What to watch for

1. The result arrives first, and the agent does not stop there.
2. The follow-up query asks whether the rule ever corrected the model.
3. Answer: the model agreed with the rule on 96 of 96 decisions and the rule corrected it zero times, so the formula contributed nothing to the number.
4. The model derived the at-capacity window itself, quoted verbatim in the output.

---

<a id="e570"></a>`event 570`

**Agent:**

Lever 3 is done. Running both comparisons.

<a id="e571"></a>`event 571`

**Tool call: `Bash`**

```bash
cd ~/bidtriage && echo "=== lever2+lever3 vs BASELINE ===" && ./.venv/Scripts/python.exe -m evals.compare --a baseline --b lever2_verify+lever3_triage 2>&1 | tail -12 && echo && echo "=== lever2+lever3 vs LEVER 2 alone (incremental effect of lever 3) ===" && ./.venv/Scripts/python.exe -m evals.compare --a lever2_verify --b lever2_verify+lever3_triage 2>&1 | tail -12
```

<a id="e572"></a>`event 572`

**Tool result:**

```
=== lever2+lever3 vs BASELINE ===
B = lever2_verify+lever3_triage n=8
verdict rule: improvement requires |delta| >= noise floor AND p < 0.05

metric                     A mean [min-max]       B mean [min-max]           delta     floor        p  verdict
----------------------------------------------------------------------------------------------------------------------------
field accuracy %           95.31 [93.75-95.83]    96.88 [95.83-97.92]         1.56      2.08    0.003  WITHIN NOISE
hallucination % (judged)   2.87 [2.30-4.60]       2.02 [1.15-2.33]           -0.86      2.30    0.061  WITHIN NOISE
triage accuracy %          90.62 [83.33-91.67]    100.00 [100.00-100.00]      9.38      8.33    0.000  IMPROVEMENT
cost per case $            0.00013 [0.00013-0.00013] 0.00060 [0.00059-0.00066]   0.00048   0.00007    0.000  REGRESSION
minutes/intake (proxy)     2.83 [2.71-3.21]       2.43 [2.21-2.58]           -0.41      0.50    0.000  WITHIN NOISE

wrote evals\results\comparison_baseline_vs_lever2_verify+lever3_triage.json

=== lever2+lever3 vs LEVER 2 alone (incremental effect of lever 3) ===
B = lever2_verify+lever3_triage n=8
verdict rule: improvement requires |delta| >= noise floor AND p < 0.05

metric                     A mean [min-max]       B mean [min-max]           delta     floor        p  verdict
----------------------------------------------------------------------------------------------------------------------------
field accuracy %           96.74 [95.83-97.92]    96.88 [95.83-97.92]         0.13      2.08    1.000  WITHIN NOISE
hallucination % (judged)   1.88 [1.15-2.33]       2.02 [1.15-2.33]            0.14      1.18    0.840  WITHIN NOISE
triage accuracy %          89.58 [83.33-91.67]    100.00 [100.00-100.00]     10.42      8.33   
... [341 more characters in the raw transcript]
```

<a id="e573"></a>`event 573`

**Agent:**

**Triage 100.00% across all 8 runs, zero variance.** That's +9.38pp over baseline (p=0.000) and it **clears the noise floor** — the first lever to do so under the rule. Let me verify it's real and not the rule doing the model's work.

<a id="e574"></a>`event 574`

**Tool call: `Bash`**

```bash
cd ~/bidtriage && ./.venv/Scripts/python.exe - <<'PYEOF'
import json, glob, pathlib, collections
runs=[]
for f in glob.glob('evals/results/*_solution*.json'):
    n=pathlib.Path(f).name
    if 'SUPERSEDED' in n or 'CONCTEST' in n: continue
    r=json.loads(pathlib.Path(f).read_text(encoding='utf-8'))
    if r.get('n_cases')==12 and set(r.get('active_levers') or [])=={'lever2_verify','lever3_triage'}:
        runs.append(r)
print("lever3 runs:", len(runs))
agree=dis=0; disagreements=[]
for r in runs:
    for cid,m in r['call_meta'].items():
        ta=m.get('triage_audit')
        if not ta: continue
        if ta.get('model_agreed_with_rule'): agree+=1
        else:
            dis+=1
            disagreements.append((cid, ta.get('model_decision'), ta.get('rule_decision')))
print("model agreed with rule: %d/%d (%.1f%%)" % (agree, agree+dis, 100*agree/(agree+dis)))
if disagreements:
    c=collections.Counter(disagreements)
    print("disagreements (case, model, rule):")
    for k,v in c.most_common(): print("   %s  x%d" % (k,v))
print()
print("case_06 timeline_conflict evaluated correctly per run:")
ok=0
for r in runs:
    ta=r['call_meta']['case_06'].get('triage_audit',{})
    v=(ta.get('criteria') or {}).get('timeline_conflict')
    if v is True: ok+=1
print("   %d/%d runs found the conflict" % (ok,len(runs)))
print("   sample reason:", ((runs[0]['call_meta']['case_06'].get('t
... [804 more characters in the raw transcript]
```

<a id="e575"></a>`event 575`

**Tool result:**

```
lever3 runs: 8
model agreed with rule: 96/96 (100.0%)

case_06 timeline_conflict evaluated correctly per run:
   8/8 runs found the conflict
   sample reason: All three committed projects run concurrently from 2026-10-01 (Foothills start) to 2026-12-10 (Clear Creek end), which is the maximum of 3. The new window (2026-11-01 to 2027-02-28) overlaps that period, e.g., throughout

cases where rule CORRECTED the model (rule right, model wrong):
   none
```

<a id="e576"></a>`event 576`

**Agent:**

Decisive: **the model agreed with the rule on all 96 decisions, and the rule corrected the model zero times.** The boolean formula contributed nothing to the score. The 100% is entirely model-driven, and case_06's conflict was found in 8/8 runs with the at-capacity window derived correctly each time.

---

Episode covers transcript events 570-576 of 838 total. Raw transcript: [`traces/`](../).
