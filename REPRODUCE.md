# REPRODUCE

> **Not yet runnable.** This file is filled in with real, executed commands and
> real measured versions/runtime/cost as each stage lands. Nothing here is
> written ahead of the run it describes.

## Environment (target)

- Python 3.12 (installed via `uv python install 3.12`)
- Dependencies pinned in `requirements.txt` (exact versions recorded after first
  successful resolve, not hand-written)
- One external service: the Anthropic API. No others.

## Setup

_TBD — recorded at Step 1._

## Commands

| Purpose | Command | Status |
|---|---|---|
| Generate eval corpus | `python -m data.generate` | pending Step 1 |
| Run baseline | `python -m evals.run --target baseline` | pending Step 2 |
| Run solution | `python -m evals.run --target solution` | pending Step 4 |

## Runtime and cost

_TBD — measured, not estimated._
