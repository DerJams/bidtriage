"""Parse a Claude Code session transcript into a flat, renderable event list.

The raw JSONL is the authoritative record and stays in the repository
untouched. This module exists only to make a readable subset of it, because a
4 MB stream of session events is not something a reader can follow from an
instruction through to a result.

Nothing here filters on content. Episodes are selected by text anchors in
build_trace_episodes.py and resolve to contiguous spans, so what was cut is
always a range rather than a judgement about which events were flattering.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRACES = ROOT / "traces"

# Event kinds, in the order they matter to a reader following the loop.
USER_TEXT = "user_text"          # an instruction from the human
ASSISTANT_TEXT = "assistant_text"  # what the agent said back
THINKING = "thinking"            # the agent's reasoning
TOOL_USE = "tool_use"            # a tool call, with its input
TOOL_RESULT = "tool_result"      # what the tool returned
SYSTEM = "system"


MIDTURN_HUMAN = "midturn_human"  # instruction sent while the agent was working


def _user_texts(path: pathlib.Path) -> set:
    """First 200 chars of every message that already appears as a user turn."""
    seen = set()
    for line in path.open(encoding="utf-8"):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "user":
            continue
        content = (rec.get("message") or {}).get("content")
        if isinstance(content, str):
            seen.add(content.strip()[:200])
        elif isinstance(content, list):
            for b in content:
                if b.get("type") == "text":
                    seen.add((b.get("text") or "").strip()[:200])
    return seen


def load_events(path: pathlib.Path) -> list:
    """Flatten the transcript into ordered events with stable indices.

    Includes `queue-operation` enqueues. Those carry the human's MID-TURN
    instructions, which are not stored as ordinary user turns and were
    therefore invisible in the first version of this parser. They are the
    human checkpoints, so omitting them would have hidden exactly the thing a
    reader most needs to see. The matching `remove` record is the dequeue and
    is skipped as a duplicate, as is any enqueue whose text also appears as a
    normal user turn.
    """
    already = _user_texts(path)
    events = []
    for lineno, line in enumerate(path.open(encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        rtype = rec.get("type")

        if rtype == "queue-operation":
            if rec.get("operation") != "enqueue":
                continue
            text = (rec.get("content") or "").strip()
            if not text or text[:200] in already:
                continue
            events.append({"i": len(events), "line": lineno,
                           "kind": MIDTURN_HUMAN, "text": text})
            continue

        if rtype not in ("user", "assistant", "system"):
            continue
        msg = rec.get("message") or {}
        content = msg.get("content")

        if isinstance(content, str):
            if content.strip():
                events.append({"i": len(events), "line": lineno,
                               "kind": USER_TEXT if rtype == "user" else ASSISTANT_TEXT,
                               "text": content})
            continue
        if not isinstance(content, list):
            continue

        for block in content:
            btype = block.get("type")
            if btype == "text":
                text = (block.get("text") or "").strip()
                if not text:
                    continue
                events.append({"i": len(events), "line": lineno,
                               "kind": USER_TEXT if rtype == "user" else ASSISTANT_TEXT,
                               "text": text})
            elif btype == "thinking":
                text = (block.get("thinking") or "").strip()
                if text:
                    events.append({"i": len(events), "line": lineno,
                                   "kind": THINKING, "text": text})
            elif btype == "tool_use":
                events.append({"i": len(events), "line": lineno, "kind": TOOL_USE,
                               "name": block.get("name"),
                               "input": block.get("input") or {},
                               "id": block.get("id")})
            elif btype == "tool_result":
                c = block.get("content")
                if isinstance(c, list):
                    c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
                events.append({"i": len(events), "line": lineno, "kind": TOOL_RESULT,
                               "text": (c if isinstance(c, str) else json.dumps(c))[:20000],
                               "is_error": bool(block.get("is_error")),
                               "id": block.get("tool_use_id")})
    return events


def summarize(ev: dict, width: int = 96) -> str:
    """One line describing an event, for locating episode boundaries."""
    k = ev["kind"]
    if k == TOOL_USE:
        inp = ev["input"]
        detail = (inp.get("command") or inp.get("file_path")
                  or inp.get("pattern") or inp.get("description")
                  or json.dumps(inp)[:width])
        if isinstance(detail, str) and len(detail) > width:
            detail = detail[:width] + "..."
        return "TOOL_USE   %-14s %s" % (ev.get("name"), str(detail).replace("\n", " ")[:width])
    if k == TOOL_RESULT:
        return "TOOL_RES   %s%s" % ("[ERROR] " if ev.get("is_error") else "",
                                    ev["text"].replace("\n", " ")[:width])
    label = {USER_TEXT: "USER      ", ASSISTANT_TEXT: "ASSISTANT ",
             THINKING: "THINKING  ", SYSTEM: "SYSTEM    ",
             MIDTURN_HUMAN: "HUMAN-MID "}.get(k, k)
    return "%s %s" % (label, ev["text"].replace("\n", " ")[:width])


def find(events: list, needle: str, kinds=None) -> list:
    """Indices of events whose text or tool input contains `needle`."""
    hits = []
    low = needle.lower()
    for ev in events:
        if kinds and ev["kind"] not in kinds:
            continue
        blob = ev.get("text") or ""
        if ev["kind"] == TOOL_USE:
            blob = json.dumps(ev.get("input") or {})
        if low in blob.lower():
            hits.append(ev["i"])
    return hits


# The episodes are all drawn from the build session. Once the diagram session
# was also captured, taking the first file alphabetically silently picked the
# wrong transcript and every anchor failed. Named explicitly rather than
# inferred, with a fallback so the module still works on a single-session
# checkout.
BUILD_SESSION = "session_fdfe39b4-2363-48df-b2be-a645f0669109.jsonl"


def default_trace() -> pathlib.Path:
    named = TRACES / BUILD_SESSION
    if named.exists():
        return named
    candidates = sorted(TRACES.glob("session_*.jsonl"))
    if not candidates:
        raise SystemExit("no session transcript found in traces/")
    return candidates[0]
