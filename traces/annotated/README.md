# Annotated trajectory episodes

The full agent trajectories are the raw JSONL transcripts in [`traces/`](../), which are the authoritative record and are kept unmodified. There are TWO of them, because the work ran across two Claude Code sessions: the build session (10 MB), which produced everything except the diagrams, and the diagram session (45 MB), which produced the two system-design files in `docs/`. Together that is 55 MB of session events, which is not something a reader can follow from an instruction through to a result.

This directory is a **readable subset**: four episodes, annotated, showing agent instructions, tool calls, tool responses, retries and human checkpoints end to end. Nothing is paraphrased. Where events are skipped inside an episode the exact count is shown.

| Episode | What it shows |
|---|---|
| [Human checkpoint: freezing the scoring rules before any measurement](01-human-checkpoint-scoring-rules.md) | The metric had to be fixed before any number existed, otherwise the target could be fitted to whatever the first attempt happened to produce. |
| [An instruction that could not be followed, overridden by measurement](02-instruction-overridden-by-measurement.md) | The human instructed the agent to pin provider routing to Exacto. |
| [The loop catching its own error before it corrupted any result](03-the-loop-catching-its-own-error.md) | The agent wrote a self-test for its scorer before trusting the scorer with a paid run. |
| [Lever 3 reaches 100 percent, and the agent checks whether that is hollow](04-lever-3-verified-not-assumed.md) | On corpus v1, lever 3 took triage from 90.62 percent to 100.00 percent with zero variance across 8 runs. |

Episodes below are drawn from the build session, `session_fdfe39b4-2363-48df-b2be-a645f0669109.jsonl`, 1279 events. The diagram session is included raw but has no annotated episodes: it is largely large JSON payloads for the drawing itself, which annotate poorly.

Episodes were chosen to show the loop working (episodes 1 and 4), an instruction being checked rather than obeyed (episode 2), and the loop catching its own defect before it corrupted a measurement (episode 3). The bug episode is kept deliberately: a trajectory set that only showed successes would misrepresent how the work actually went.
