"""Copy THIS project's Claude Code session transcripts into traces/.

    python scripts/capture_traces.py <session-id> [<session-id> ...]
    python scripts/capture_traces.py --list

Why this is a script and not `cp -r`:

The Claude Code project directory for this machine
(~/.claude/projects/C--Users-James/) contains every session ever run from the
home directory -- at time of writing, 10 sessions totalling 28 MB, only one of
which is BidTriage work. Copying the directory wholesale into a PUBLIC repo
would publish unrelated transcripts. This script therefore requires session ids
to be named explicitly. There is deliberately no "copy everything" flag.

Every copied transcript is also passed through a redactor for credential-shaped
strings before it is written. Redactions are counted and reported, and the
counts are written into traces/REDACTIONS.md so the redaction is visible rather
than silent.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECTS_ROOT = pathlib.Path.home() / ".claude" / "projects"


def _resolve_projects_dir(explicit=None):
    """Locate the Claude Code project directory holding this repo's sessions.

    This path was hardcoded to one developer's username, which made the script
    unusable on any other machine. Found by a clean-room walkthrough of
    REPRODUCE.md. Resolution order: an explicit --project name, then the
    directory whose name encodes this repo's own path, then the single
    directory containing transcripts if there is exactly one. Anything
    ambiguous asks rather than guessing.
    """
    if explicit:
        return PROJECTS_ROOT / explicit
    # Claude Code encodes the working directory into the folder name.
    encoded = str(ROOT).replace(":", "-").replace(chr(92), "-").replace("/", "-")
    for cand in (PROJECTS_ROOT / encoded, PROJECTS_ROOT / encoded.rstrip("-")):
        if cand.is_dir():
            return cand
    if PROJECTS_ROOT.is_dir():
        withlogs = [d for d in PROJECTS_ROOT.iterdir()
                    if d.is_dir() and any(d.glob("*.jsonl"))]
        if len(withlogs) == 1:
            return withlogs[0]
        if len(withlogs) > 1:
            names = ", ".join(sorted(d.name for d in withlogs))
            raise SystemExit(
                "Multiple Claude Code project directories found. Pass one with "
                "--project NAME. Available: %s" % names)
    raise SystemExit("No Claude Code project directory found under %s" % PROJECTS_ROOT)
TRACES = ROOT / "traces"

# Credential-shaped patterns. Ordered; each maps to a stable placeholder.
PATTERNS = [
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("bearer_token", re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{24,}")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    # Real addresses only. The synthetic corpus uses the reserved .example TLD
    # (RFC 6761) throughout, and those are work product -- redacting them would
    # gut the trace. The negative lookahead sits before the TLD, not the domain.
    ("email_address", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+"
                                 r"\.(?!example\b)[A-Za-z]{2,}")),
]


def redact(text: str) -> tuple[str, dict]:
    counts = {}
    for name, pat in PATTERNS:
        text, n = pat.subn("[REDACTED:%s]" % name, text)
        if n:
            counts[name] = counts.get(name, 0) + n
    return text, counts


def main(argv: list[str]) -> int:
    explicit = None
    if "--project" in argv:
        i = argv.index("--project")
        explicit = argv[i + 1] if i + 1 < len(argv) else None
        argv = argv[:i] + argv[i + 2:]

    PROJECTS = _resolve_projects_dir(explicit)
    if not PROJECTS.exists():
        print("project dir not found: %s" % PROJECTS, file=sys.stderr)
        return 1

    sessions = sorted(PROJECTS.glob("*.jsonl"))
    if "--list" in argv or not argv:
        print("Sessions in %s\n" % PROJECTS)
        for s in sessions:
            print("  %-40s %10.1f KB" % (s.stem, s.stat().st_size / 1024))
        print("\nPass session ids explicitly. There is no copy-all flag: this "
              "directory holds unrelated sessions and traces/ is public.")
        return 0 if argv else 1

    TRACES.mkdir(parents=True, exist_ok=True)
    total = {}
    written = []
    for sid in argv:
        src = PROJECTS / (sid + ".jsonl")
        if not src.exists():
            print("no such session: %s" % sid, file=sys.stderr)
            return 1
        raw = src.read_text(encoding="utf-8", errors="replace")
        clean, counts = redact(raw)
        dst = TRACES / ("session_" + sid + ".jsonl")
        dst.write_text(clean, encoding="utf-8", newline="\n")
        written.append((dst.name, dst.stat().st_size, counts))
        for k, v in counts.items():
            total[k] = total.get(k, 0) + v
        print("wrote %s  (%.1f KB)  redactions: %s"
              % (dst.name, dst.stat().st_size / 1024, counts or "none"))

    lines = [
        "# Trace redactions",
        "",
        "`scripts/capture_traces.py` passes every transcript through a",
        "credential-shaped-string redactor before writing it here. This file",
        "records what was replaced, so the redaction is auditable rather than",
        "silent. Placeholders have the form `[REDACTED:<kind>]`.",
        "",
        "Only BidTriage sessions are copied. The Claude Code project directory",
        "on this machine also holds unrelated sessions; those are never copied,",
        "and the capture script has no copy-all flag by design.",
        "",
        "| Trace file | Size (KB) | Redactions |",
        "|---|---:|---|",
    ]
    for name, size, counts in written:
        c = ", ".join("%s x%d" % (k, v) for k, v in sorted(counts.items())) or "none"
        lines.append("| `%s` | %.1f | %s |" % (name, size / 1024, c))
    lines += ["", "Totals: %s" % (", ".join("%s x%d" % (k, v)
                                            for k, v in sorted(total.items())) or "none"), ""]
    (TRACES / "REDACTIONS.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("\nwrote traces/REDACTIONS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
