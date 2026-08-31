# An instruction that could not be followed, overridden by measurement

> **This is an annotated extract.** The complete, unedited transcript is in [`traces/`](../) as raw JSONL. Nothing here is paraphrased: every block below the annotations is verbatim from that file. Long tool inputs and outputs are truncated with the omitted character count shown.

## Why this episode

The human instructed the agent to pin provider routing to Exacto. The agent checked instead of complying, found that Auto Exacto cannot be pinned at all and would not apply to a toolless baseline, measured three routing configs live, and brought the conflict back as a checkpoint rather than either silently ignoring the instruction or following it into a confounded experiment.

## What to watch for

1. The original instruction is at the top, then a large investigation is elided with the exact count shown.
2. The finding is empirical: three configurations, three runs each, different providers and prices.
3. The agent surfaces the conflict as a question, and the human confirms the override.
4. A live 429 retry is visible in the transcript.

---

<a id="e139"></a>`event 139`

> ### Human instruction
>
> Switching model provider before Step 2. Use OpenRouter, not the Anthropic API.
> 
> - Model: z-ai/glm-5.3-flash. Fallback to z-ai/glm-5.2 (paid) if structured output is unreliable; note any switch in CHANGELOG.md.
> - Pin provider routing to Exacto and record the routing mode and resolved provider in the results JSON for every run.
> - Env var is OPENROUTER_API_KEY. Confirm it is visible to you before running anything.
> - Baseline and every lever must run on the same model and routing config.
> - Update the README tools disclosure, requirements.txt, and REPRODUCE.md. The README currently says the Anthropic API is the only external service, which is now wrong.
> 
> Then proceed with the harness-first sequencing you proposed.


> *[25 transcript events omitted here: the intervening investigation. They are present in the raw JSONL.]*

<a id="e165"></a>`event 165`

**Agent:**

Verified against the live API and docs. **There's a problem with the routing instruction**, and it's worth stopping on before any run. Let me confirm the details empirically first.

<a id="e166"></a>`event 166`

**Tool call: `Bash`**

```bash
cd ~/bidtriage && SP="C:/Users/James/AppData/Local/Temp/claude/C--Users-James/fdfe39b4-2363-48df-b2be-a645f0669109/scratchpad" && ./.venv/Scripts/python.exe - "$SP/ep_flash.json" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))['data']
e = d['endpoints'][0]
print("keys on an endpoint object:")
for k in sorted(e.keys()):
    v = e[k]
    print("   %-24s %s" % (k, str(v)[:90]))
print("\nProviders that DO support structured_outputs, cheapest first:")
rows = []
for e in d['endpoints']:
    sp = e.get('supported_parameters') or []
    if 'structured_outputs' in sp:
        p = e.get('pricing', {})
        rows.append((float(p.get('prompt',0))*1e6, float(p.get('completion',0))*1e6,
                     e.get('provider_name'), e.get('tag') or e.get('name')))
for r in sorted(rows):
    print("   $%-8.4f/$%-8.4f  %-16s tag=%s" % r)
PYEOF
```

<a id="e167"></a>`event 167`

**Tool result:**

```
keys on an endpoint object:
   context_length           1048576
   latency_last_30m         None
   max_completion_tokens    131072
   max_prompt_tokens        None
   model_id                 z-ai/glm-5.3-flash
   model_name               Z.ai: GLM 5.3 Flash
   name                     Relace | z-ai/glm-5.3-flash-20260826
   pricing                  {'prompt': '0.000000075', 'completion': '0.00000025', 'input_cache_read': '0.000000015', '
   provider_name            Relace
   quantization             fp4
   status                   0
   supported_parameters     ['reasoning', 'include_reasoning', 'max_tokens', 'temperature', 'top_p', 'stop', 'frequenc
   supports_implicit_caching False
   supports_tool_choice     {'none': True, 'auto': True, 'required': False, 'function': False}
   supports_voice_cloning   False
   tag                      relace/fp4
   throughput_last_30m      None
   uptime_last_1d           96.035260896848
   uptime_last_30m          98.55831561479023
   uptime_last_5m           99.11111111111111

Providers that DO support structured_outputs, cheapest first:
   $0.0750  /$0.2500    DeepInfra        tag=deepinfra/fp8
   $0.1500  /$0.4999    Modal            tag=modal/fp8
   $0.1500  /$0.4400    Morph            tag=morph/fp8
   $0.1500  /$0.5000    Cloudflare       tag=cloudflare
   $0.1500  /$0.5000    DigitalOcean     tag=digitalocean
   $0.1500  /$0.5000    Fireworks        tag=fireworks
   $0.1500  /$0.5000    Friendli         tag=friendli
   $0.1500  /$0.5000    Parasail         tag=parasail/fp8
   $0.1500  /$0.5000    Phala            tag=phala/fp8
   $0.1500  /$0.5000    Reka             tag=reka/fp8
   $0.1500  /$0.5000    Together         tag=together
   $0.1500  /$0.5000    Venice           tag=venice
   $0
... [45 more characters in the raw transcript]
```

<a id="e168"></a>`event 168`

**Agent:**

DeepInfra is the only structured-output provider at the cheap tier — half the price of the rest. Now a live smoke test to see what's actually reported back.

<a id="e169"></a>`event 169`

**Tool call: `Write`**

```
file: C:\Users\James\AppData\Local\Temp\claude\C--Users-James\fdfe39b4-2363-48df-b2be-a645f0669109\scratchpad\smoke.py

"""Smoke-test OpenRouter routing behaviour. Throwaway; not part of the repo."""
import json
import os
import urllib.request

KEY = os.environ["OPENROUTER_API_KEY"]
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "z-ai/glm-5.3-flash"

TOOL = [{
    "type": "function",
    "function": {
        "name": "emit",
        "description": "Emit the answer.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}]


def call(label, body):
    req = urllib.request.Request(
        URL, method="POST",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("%-34s HTTP %s  %s" % (label, e.code, e.read()[:400].decode()))
        return
    u = d.get("usage", {}) or {}
    ch = (d.get("choices") or [{}])[0]
    msg = ch.get("message", {}) or {}
    tc = msg.get("tool_calls") or []
    print("%-34s provider=%-14s finish=%-12s in=%s out=%s tool_calls=%d"
          % (l
... [1851 more characters in the raw transcript]
```

<a id="e170"></a>`event 170`

**Tool result:**

```
File created successfully at: C:\Users\James\AppData\Local\Temp\claude\C--Users-James\fdfe39b4-2363-48df-b2be-a645f0669109\scratchpad\smoke.py (file state is current in your context — no need to Read it back)
```

<a id="e171"></a>`event 171`

**Tool call: `Bash`**

```bash
cd ~/bidtriage && ./.venv/Scripts/python.exe "C:/Users/James/AppData/Local/Temp/claude/C--Users-James/fdfe39b4-2363-48df-b2be-a645f0669109/scratchpad/smoke.py" 2>&1
```

<a id="e172"></a>`event 172`

**Tool result - contains a rate-limit retry:**

```
=== A. no provider block, NO tools (what a toolless baseline hits) ===
  run 1                            provider=Z.AI           finish=stop         in=24 out=37 tool_calls=0
  run 2                            provider=Z.AI           finish=stop         in=24 out=23 tool_calls=0
  run 3                            provider=Z.AI           finish=stop         in=24 out=46 tool_calls=0

=== B. no provider block, WITH tools (Auto Exacto applies) ===
  run 1                            provider=Together       finish=tool_calls   in=164 out=7 tool_calls=1
                                     args={"city": "Paris"}
  run 2                            provider=Together       finish=tool_calls   in=164 out=7 tool_calls=1
                                     args={"city": "Paris"}
  run 3                            provider=Together       finish=tool_calls   in=164 out=7 tool_calls=1
                                     args={"city": "Paris"}

=== C. pinned: only=[deepinfra], no fallbacks, require_parameters ===
  run 1                            provider=DeepInfra      finish=tool_calls   in=164 out=11 tool_calls=1
                                     args={"city": "Paris"}
  run 2                            provider=DeepInfra      finish=tool_calls   in=164 out=11 tool_calls=1
                                     args={"city": "Paris"}
  run 3                            provider=DeepInfra      finish=tool_calls   in=164 out=11 tool_calls=1
                                     args={"city": "Paris"}

=== D. pinned + json_schema structured output ===
  run 1                            HTTP 429  {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"z-ai/glm-5.3-flash is temporarily rate-limited upstream. Please retry shortly, or add your o
... [232 more characters in the raw transcript]
```

<a id="e173"></a>`event 173`

**Agent:**

Empirically confirmed, and it surfaces a real conflict. Let me retry the structured-output test that hit a transient 429.

<a id="e174"></a>`event 174`

**Tool call: `Bash`**

```bash
cd ~/bidtriage && SP="C:/Users/James/AppData/Local/Temp/claude/C--Users-James/fdfe39b4-2363-48df-b2be-a645f0669109/scratchpad" && ./.venv/Scripts/python.exe - <<'PYEOF'
import json, os, time, urllib.request, urllib.error
KEY=os.environ["OPENROUTER_API_KEY"]
body={"model":"z-ai/glm-5.3-flash","max_tokens":80,
 "messages":[{"role":"user","content":"Capital of France?"}],
 "provider":{"only":["deepinfra"],"allow_fallbacks":False,"require_parameters":True},
 "response_format":{"type":"json_schema","json_schema":{"name":"ans","strict":True,
   "schema":{"type":"object","properties":{"city":{"type":"string"}},
             "required":["city"],"additionalProperties":False}}}}
for attempt in range(1,6):
    req=urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",method="POST",
        data=json.dumps(body).encode(),
        headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=120) as r: d=json.loads(r.read())
        print("attempt %d OK  provider=%s  content=%s" % (attempt, d.get("provider"),
              (d["choices"][0]["message"].get("content") or "")[:100]))
        break
    except urllib.error.HTTPError as e:
        payload=e.read()[:200].decode()
        print("attempt %d HTTP %s %s" % (attempt, e.code, payload[:130]))
        time.sleep(2*attempt)
PYEOF
```

<a id="e175"></a>`event 175`

**Tool result - contains a rate-limit retry:**

```
attempt 1 HTTP 429 {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"z-ai/glm-5.3-flash is temporarily rate-limited upstrea
attempt 2 HTTP 429 {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"z-ai/glm-5.3-flash is temporarily rate-limited upstrea
attempt 3 OK  provider=DeepInfra  content={ "city": "Paris" }
```

<a id="e176"></a>`event 176`

**Agent:**

Everything checks out except the routing instruction, which can't be followed as written. Verified facts:

| Check | Result |
|---|---|
| `OPENROUTER_API_KEY` | visible, 73 chars, `sk-or-v1…`, User scope (both shells) |
| `z-ai/glm-5.3-flash` | exists, 20 providers, 1M context |
| `z-ai/glm-5.2` | exists |
| Structured output on pinned provider | works — but only on attempt 3, after two upstream 429s |

**Auto Exacto is not a mode you can pin.** Per OpenRouter's docs, it "runs by default on every tool-calling request, requiring no configuration" — it's **opt-out**, not opt-in, and it applies *only to requests that include tools*. There's no `provider: {mode: "exacto"}` to set or record.

That creates a direct conflict with your own requirement that baseline and every lever share routing. Measured live, three runs each:

| Config | Resolved provider | Price /M | structured_outputs |
|---|---|---|---|
| No tools (your baseline spec) | **Z.AI** 3/3 | $0.075 / $0.25 | ✗ not supported |
| Tools, unpinned (Exacto active) | **Together** 3/3 | $0.15 / $0.50 | ✓ |
| Pinned `only=[deepinfra]` | **DeepInfra** 3/3 | $0.075 / $0.25 | ✓ |

The baseline is specified as *no tools*, so Auto Exacto never applies to it — it lands on Z.AI while the tool-using solution lands on Together. Different provider, different price, different structured-output support. Every lever delta would then confound my change with a provider change. And Exacto reorders on rolling 32-day live signals, so it isn't stable across days either.

<a id="e177"></a>`event 177`

**Tool call: `AskUserQuestion`**

```
{
  "questions": [
    {
      "question": "Auto Exacto can't be pinned and doesn't apply to the toolless baseline. How should I configure routing so baseline and levers are comparable?",
      "header": "Routing",
      "multiSelect": false,
      "options": [
        {
          "label": "Pin only=[deepinfra], no fallbacks (Recommended)",
          "description": "provider.only=['deepinfra'], allow_fallbacks=false, require_parameters=true. Verified deterministic 3/3, supports structured_outputs, and is the cheapest endpoint at $0.075/$0.25 \u2014 half of what Exacto picked. Identical config for baseline and all 4 levers, so deltas are attributable to my changes alone. Results JSON records routing_mode='pinned', the resolved provider from every response, and auto_exacto='not_applicable'."
        },
        {
          "label": "Leave Auto Exacto on (default) for tool targets",
          "description": "Closest to your literal instruction. Baseline routes price-weighted (Z.AI, no structured-output support); levers route via Exacto (Together today, possibly elsewhere tomorrow). I'd record the resolved provider per call, but lever deltas would be confounded by provider changes and the numbers wouldn't be stably reproducible."
        },
        {
          "label": "Keep Exacto, give the baseline a dummy tool",
          "description": "Forces the baseline through Exacto too, so
... [206 more characters in the raw transcript]
```

<a id="e178"></a>`event 178`

**Tool result:**

```
Your questions have been answered: "Auto Exacto can't be pinned and doesn't apply to the toolless baseline. How should I configure routing so baseline and levers are comparable?"="Pin only=[deepinfra], no fallbacks (Recommended)". You can now continue with these answers in mind.
```

<a id="e179"></a>`event 179`

> ### HUMAN CHECKPOINT (sent mid-turn, while the agent was working)
>
> Confirmed, go with pinned only=[deepinfra], allow_fallbacks=false, require_parameters=true. My Exacto instruction was wrong; your finding overrides it.
> 
> Two additions:
> 1. Add bounded retry with exponential backoff on 429s (cap the attempts), and record per-case retry counts and any failures in the results JSON. With fallbacks off, a rate limit is a hard failure, so this needs to be explicit rather than silent.
> 2. Add a CHANGELOG entry documenting the routing decision: that Exacto cannot be pinned, that it does not apply to a toolless baseline, and that pinning a single provider was required to keep baseline and lever runs comparable and reproducible. This is a reproducibility decision worth showing the judges.
> 
> Then proceed with the harness and baseline.

<a id="e180"></a>`event 180`

**Agent:**

Locked. Verifying one more thing — whether OpenRouter will report **actual charged cost** so I never have to estimate it.

<a id="e181"></a>`event 181`

**Tool call: `Bash`**

```bash
cd ~/bidtriage && ./.venv/Scripts/python.exe - <<'PYEOF'
import json, os, time, urllib.request, urllib.error
KEY=os.environ["OPENROUTER_API_KEY"]
body={"model":"z-ai/glm-5.3-flash","max_tokens":40,
 "messages":[{"role":"user","content":"Capital of France?"}],
 "provider":{"only":["deepinfra"],"allow_fallbacks":False,"require_parameters":True},
 "usage":{"include":True}}
for attempt in range(1,7):
    req=urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",method="POST",
        data=json.dumps(body).encode(),
        headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=120) as r: d=json.loads(r.read())
        print("provider:", d.get("provider"))
        print("usage block:")
        print(json.dumps(d.get("usage"), indent=2))
        break
    except urllib.error.HTTPError as e:
        print("attempt %d HTTP %s" % (attempt, e.code)); time.sleep(2*attempt)
PYEOF
```

<a id="e182"></a>`event 182`

**Tool result:**

```
provider: DeepInfra
usage block:
{
  "prompt_tokens": 16,
  "completion_tokens": 40,
  "total_tokens": 56,
  "cost": 1.12e-05,
  "is_byok": false,
  "prompt_tokens_details": {
    "cached_tokens": 0,
    "cache_write_tokens": 0,
    "audio_tokens": 0,
    "video_tokens": 0
  },
  "cost_details": {
    "upstream_inference_cost": 1.12e-05,
    "upstream_inference_prompt_cost": 1.2e-06,
    "upstream_inference_completions_cost": 1e-05
  },
  "completion_tokens_details": {
    "reasoning_tokens": 4,
    "image_tokens": 0,
    "audio_tokens": 0
  }
}
```

<a id="e183"></a>`event 183`

**Agent:**

Cost is reported exactly (`usage.cost`, actual credits charged) — so cost per task needs no estimation at all. Both your additions are in. Building the harness now.

---

Episode covers transcript events 139-139, 165-183 of 1279 total. Raw transcript: [`traces/`](../).
