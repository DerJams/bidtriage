"""Render a readable, annotated subset of the raw session transcript.

    python scripts/build_trace_episodes.py

The raw JSONL in traces/ is the authoritative record and is not modified. This
produces traces/annotated/, a small set of episodes a reader can follow from an
instruction through to a result, with tool calls, tool responses, retries and
human checkpoints visible.

Two rules keep the curation honest:

* Episodes are contiguous spans of the transcript, located by text anchors.
  Where a span is skipped inside an episode, the exact number of omitted events
  is printed rather than the gap being closed silently.
* Annotations are clearly marked as commentary and never replace transcript
  content. Everything outside an annotation block is verbatim.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from trace_lib import (  # noqa: E402
    ASSISTANT_TEXT,
    MIDTURN_HUMAN,
    THINKING,
    TOOL_RESULT,
    TOOL_USE,
    USER_TEXT,
    default_trace,
    load_events,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "traces" / "annotated"

MAX_TOOL_INPUT = 1400
MAX_TOOL_RESULT = 1800
MAX_TEXT = 2200
MAX_THINKING = 900

# Mid-turn human messages arrive inside tool results rather than as their own
# events. These markers let the renderer surface them as the checkpoints they
# are instead of burying them in a tool response.
MIDTURN_MARKER = "The user sent a new message while you were working:"


EPISODES = [
    {
        "slug": "01-human-checkpoint-scoring-rules",
        "title": "Human checkpoint: freezing the scoring rules before any measurement",
        "why": (
            "The metric had to be fixed before any number existed, otherwise the target "
            "could be fitted to whatever the first attempt happened to produce. Two "
            "decisions could not be made from the code alone, so the agent stopped and "
            "asked rather than picking a convenient default. The human answered, then "
            "sent four refinements mid-turn, which the agent folded in before "
            "continuing. This is the loop working at design time, before anything was "
            "measurable."
        ),
        "watch": [
            "The agent asks rather than assuming, and says which option it recommends.",
            "The human's answer arrives as a tool result, then four further refinements "
            "arrive mid-turn and change the design again.",
            "Nothing has been measured yet at this point. That is the whole reason for "
            "the checkpoint.",
        ],
        "anchors": [("Here's what I'm proposing for Step 1",
                     "Refinements noted and folded in")],
    },
    {
        "slug": "02-instruction-overridden-by-measurement",
        "title": "An instruction that could not be followed, overridden by measurement",
        "why": (
            "The human instructed the agent to pin provider routing to Exacto. The agent "
            "checked instead of complying, found that Auto Exacto cannot be pinned at all "
            "and would not apply to a toolless baseline, measured three routing configs "
            "live, and brought the conflict back as a checkpoint rather than either "
            "silently ignoring the instruction or following it into a confounded "
            "experiment."
        ),
        "watch": [
            "The original instruction is at the top, then a large investigation is elided "
            "with the exact count shown.",
            "The finding is empirical: three configurations, three runs each, different "
            "providers and prices.",
            "The agent surfaces the conflict as a question, and the human confirms the "
            "override.",
            "A live 429 retry is visible in the transcript.",
        ],
        "anchors": [("Switching model provider before Step 2", "Switching model provider before Step 2"),
                    ("There's a problem with the routing instruction", "Cost is reported exactly")],
    },
    {
        "slug": "03-the-loop-catching-its-own-error",
        "title": "The loop catching its own error before it corrupted any result",
        "why": (
            "The agent wrote a self-test for its scorer before trusting the scorer with a "
            "paid run. The test failed immediately and caught two real defects. The "
            "serious one: the corporate-suffix stripper treated 'co' as a company suffix "
            "and silently truncated 'denver, co' to 'denver', which would have failed "
            "every location field in the corpus while the gold keys still looked correct."
        ),
        "watch": [
            "The self-test is written before it is needed, not after a failure.",
            "It fails on the first run and names both defects precisely.",
            "The fix carries a comment explaining why 'co' must stay out, so the bug "
            "cannot be reintroduced by someone tidying the list.",
            "The test is re-run and passes. Nothing was measured while the bug was live.",
        ],
        "anchors": [("let me prove the normalizers actually work",
                     "normalizer + scorer selftest: all checks passed")],
    },
    {
        "slug": "04-lever-3-verified-not-assumed",
        "title": "Lever 3 reaches 100 percent, and the agent checks whether that is hollow",
        "why": (
            "On corpus v1, lever 3 took triage from 90.62 percent to 100.00 percent with "
            "zero variance across 8 runs. The design splits work so the model evaluates four capacity "
            "criteria and code applies only a published boolean formula. If the formula "
            "were carrying the score, the result would prove nothing, so the agent "
            "immediately tested exactly that rather than reporting the headline."
        ),
        "watch": [
            "The result arrives first, and the agent does not stop there.",
            "The follow-up query asks whether the rule ever corrected the model.",
            "Answer: on v1 the model agreed with the rule on 96 of 96 decisions and the "
            "rule corrected it zero times, so the formula contributed nothing. The same "
            "check on corpus v2 gives 234 of 239.",
            "The model derived the at-capacity window itself, quoted verbatim in the "
            "output.",
        ],
        "anchors": [("Lever 3 is done. Running both comparisons",
                     "the rule corrected the model zero times")],
    },
]


def _fence(text: str, lang: str = "") -> str:
    text = text.replace("\r\n", "\n").rstrip()
    if "```" in text:
        text = text.replace("```", "'''")
    return "```%s\n%s\n```" % (lang, text)


def _clip(text: str, limit: int) -> str:
    text = (text or "").rstrip()
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... [%d more characters in the raw transcript]" % (len(text) - limit)


def _tool_input(ev: dict) -> str:
    inp = ev.get("input") or {}
    for key in ("command", "content", "new_string", "file_path", "pattern"):
        if key in inp and isinstance(inp[key], str):
            body = inp[key]
            prefix = ""
            if key != "command" and inp.get("file_path"):
                prefix = "file: %s\n\n" % inp["file_path"]
            return _clip(prefix + body, MAX_TOOL_INPUT)
    import json as _json
    return _clip(_json.dumps(inp, indent=2), MAX_TOOL_INPUT)


def _looks_like_retry(text: str) -> bool:
    low = (text or "").lower()
    return "429" in low or "retries=" in low or "rate-limited" in low


def render_event(ev: dict) -> str:
    k = ev["kind"]
    if k == USER_TEXT:
        text = ev["text"]
        if MIDTURN_MARKER in text:
            body = text.split(MIDTURN_MARKER, 1)[1]
            return ("> ### Human checkpoint (sent mid-turn)\n>\n"
                    + "\n".join("> " + l for l in _clip(body, MAX_TEXT).splitlines()))
        if text.startswith("<task-notification"):
            return "*(background task finished; the agent was re-invoked)*"
        return ("> ### Human instruction\n>\n"
                + "\n".join("> " + l for l in _clip(text, MAX_TEXT).splitlines()))
    if k == MIDTURN_HUMAN:
        if ev["text"].startswith("<task-notification"):
            return "*(background task finished; the agent was re-invoked)*"
        return ("> ### HUMAN CHECKPOINT (sent mid-turn, while the agent was working)\n>\n"
                + "\n".join("> " + l for l in _clip(ev["text"], MAX_TEXT).splitlines()))
    if k == ASSISTANT_TEXT:
        return "**Agent:**\n\n" + _clip(ev["text"], MAX_TEXT)
    if k == THINKING:
        return ("<details><summary>Agent reasoning (click to expand)</summary>\n\n"
                + _clip(ev["text"], MAX_THINKING) + "\n\n</details>")
    if k == TOOL_USE:
        return ("**Tool call: `%s`**\n\n" % ev.get("name")) + _fence(_tool_input(ev), "bash"
                if ev.get("name") in ("Bash", "PowerShell") else "")
    if k == TOOL_RESULT:
        head = "**Tool result"
        if ev.get("is_error"):
            head += " (ERROR)"
        if _looks_like_retry(ev.get("text")):
            head += " - contains a rate-limit retry"
        head += ":**"
        return head + "\n\n" + _fence(_clip(ev["text"], MAX_TOOL_RESULT))
    return ""


def resolve_ranges(events: list, ep: dict) -> list:
    """Turn (start_anchor, end_anchor) pairs into concrete index ranges.

    Anchors rather than fixed indices, because the parser changed once already
    (mid-turn human checkpoints were originally invisible) and every hardcoded
    range silently shifted by six.
    """
    ranges, cursor = [], 0
    for start_anchor, end_anchor in ep["anchors"]:
        s_i = e_i = None
        for ev in events[cursor:]:
            # Match message text only, never tool INPUT. Episode 3's end anchor
            # is a line the self-test prints, and matching tool inputs made it
            # hit the source of selftest.py where that string is defined,
            # ending the episode before the test had even run.
            blob = ev.get("text") or ""
            if s_i is None:
                if start_anchor.lower() in blob.lower():
                    s_i = ev["i"]
                    if start_anchor == end_anchor:  # single-event range
                        e_i = ev["i"]
                        break
                continue
            if end_anchor.lower() in blob.lower():
                e_i = ev["i"]
                break
        if s_i is None or e_i is None:
            raise SystemExit("episode %s: anchor not found (%r -> %r)"
                             % (ep["slug"], start_anchor, end_anchor))
        ranges.append((s_i, e_i + 1))
        cursor = e_i + 1
    return ranges


def build(events: list, ep: dict) -> str:
    L = ["# " + ep["title"], ""]
    L.append("> **This is an annotated extract.** The complete, unedited transcript is "
             "in [`traces/`](../) as raw JSONL. Nothing here is paraphrased: every block "
             "below the annotations is verbatim from that file. Long tool inputs and "
             "outputs are truncated with the omitted character count shown.")
    L += ["", "## Why this episode", "", ep["why"], "", "## What to watch for", ""]
    L += ["%d. %s" % (i, w) for i, w in enumerate(ep["watch"], 1)]
    L += ["", "---", ""]

    prev_hi = None
    for lo, hi in ep["_ranges"]:
        if prev_hi is not None and lo > prev_hi:
            L += ["", "> *[%d transcript events omitted here: the intervening "
                  "investigation. They are present in the raw JSONL.]*" % (lo - prev_hi), ""]
        for ev in events[lo:hi]:
            block = render_event(ev)
            if block:
                L += ["<a id=\"e%d\"></a>`event %d`" % (ev["i"], ev["i"]), "", block, ""]
        prev_hi = hi

    L += ["---", "",
          "Episode covers transcript events %s of %d total. Raw transcript: "
          "[`traces/`](../)."
          % (", ".join("%d-%d" % (a, b - 1) for a, b in ep["_ranges"]), len(events))]
    return "\n".join(L) + "\n"


def main() -> int:
    path = default_trace()
    events = load_events(path)
    OUT.mkdir(parents=True, exist_ok=True)

    index = ["# Annotated trajectory episodes", "",
             "The full agent trajectories are the raw JSONL transcripts in "
             "[`traces/`](../), which are the authoritative record and are kept "
             "unmodified. That file is roughly 5 MB of session events, which is not "
             "something a reader can follow from an instruction through to a result.",
             "",
             "This directory is a **readable subset**: four episodes, annotated, showing "
             "agent instructions, tool calls, tool responses, retries and human "
             "checkpoints end to end. Nothing is paraphrased. Where events are skipped "
             "inside an episode the exact count is shown.", "",
             "| Episode | What it shows |", "|---|---|"]

    for ep in EPISODES:
        ep["_ranges"] = resolve_ranges(events, ep)
        text = build(events, ep)
        (OUT / (ep["slug"] + ".md")).write_text(text, encoding="utf-8", newline="\n")
        first_line = ep["why"].split(".")[0] + "."
        index.append("| [%s](%s.md) | %s |" % (ep["title"], ep["slug"], first_line))
        print("wrote traces/annotated/%s.md  (%d bytes)" % (ep["slug"], len(text)))

    index += ["", "Source transcript: `%s`, %d events." % (path.name, len(events)),
              "",
              "Episodes were chosen to show the loop working (episodes 1 and 4), an "
              "instruction being checked rather than obeyed (episode 2), and the loop "
              "catching its own defect before it corrupted a measurement (episode 3). "
              "The bug episode is kept deliberately: a trajectory set that only showed "
              "successes would misrepresent how the work actually went.", ""]
    (OUT / "README.md").write_text("\n".join(index), encoding="utf-8", newline="\n")
    print("wrote traces/annotated/README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
