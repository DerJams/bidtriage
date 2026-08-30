"""Human-minutes-per-intake proxy.

This is a PROXY, not a measurement. No human was timed. It exists so the two
targets can be compared on effort using one fixed formula, and it is labelled
as a proxy everywhere it is reported. Constants are frozen here before any
measurement, so they cannot be tuned after seeing which target wins.

Model
-----
Manual (today):   read the whole document carefully, re-key all 8 fields,
                  then decide.
Assisted:         read a short brief, fix whatever the system got wrong
                  (which means going back to the source), adjudicate whatever
                  it flagged (cheaper -- the flag comes with a cited span),
                  then sanity-check the decision.

Known limitation, stated rather than hidden: this charges a hallucinated field
the same as a merely incorrect one. In reality an undetected hallucination is
far more expensive, because it is wrong in a way nobody is looking for. The
proxy therefore FLATTERS a target that hallucinates. It is reported alongside
the hallucination rate for that reason, never instead of it.
"""
from __future__ import annotations

from evals.harness.score import (
    CORRECT,
    CORRECT_ABSTENTION,
    FLAGGED,
    HALLUCINATED,
    INCORRECT,
    MISSED,
)

# --- Frozen constants ------------------------------------------------------
WPM_CAREFUL = 200.0     # reading an RFP properly, not skimming
WPM_SKIM = 350.0        # reading a generated brief
RE_KEY_MIN_PER_FIELD = 1.5   # locate + transcribe one field into the sheet
DECISION_MIN = 4.0           # manual bid/no-bid judgement
BRIEF_WORDS = 250.0          # assumed estimator brief length
FIX_MIN_PER_FIELD = 3.0      # wrong/missing: back to source, find, correct
REVIEW_MIN_PER_FLAG = 1.5    # flagged: adjudicate against a cited span
DECISION_REVIEW_MIN = 1.0    # sanity-check a proposed decision

CONSTANTS = {
    "wpm_careful": WPM_CAREFUL, "wpm_skim": WPM_SKIM,
    "re_key_min_per_field": RE_KEY_MIN_PER_FIELD, "decision_min": DECISION_MIN,
    "brief_words": BRIEF_WORDS, "fix_min_per_field": FIX_MIN_PER_FIELD,
    "review_min_per_flag": REVIEW_MIN_PER_FLAG,
    "decision_review_min": DECISION_REVIEW_MIN,
}

NEEDS_FIX = (INCORRECT, MISSED, HALLUCINATED)


def manual_minutes(source_text: str) -> float:
    words = len(source_text.split())
    return round(words / WPM_CAREFUL + 8 * RE_KEY_MIN_PER_FIELD + DECISION_MIN, 2)


def assisted_minutes(case_score: dict) -> float:
    outcomes = [f["outcome"] for f in case_score["fields"].values()]
    fixes = sum(1 for o in outcomes if o in NEEDS_FIX)
    flags = sum(1 for o in outcomes if o == FLAGGED)
    return round(BRIEF_WORDS / WPM_SKIM
                 + fixes * FIX_MIN_PER_FIELD
                 + flags * REVIEW_MIN_PER_FLAG
                 + DECISION_REVIEW_MIN, 2)


def summarize(case_scores: list, source_texts: dict) -> dict:
    manual = [manual_minutes(source_texts[cs["case_id"]]) for cs in case_scores]
    assisted = [assisted_minutes(cs) for cs in case_scores]
    n = max(1, len(case_scores))
    return {
        "_disclaimer": "PROXY, not measured human time. Constants frozen in "
                       "evals/harness/minutes.py before any measurement.",
        "constants": CONSTANTS,
        "manual_minutes_mean": round(sum(manual) / n, 2),
        "assisted_minutes_mean": round(sum(assisted) / n, 2),
        "minutes_saved_mean": round((sum(manual) - sum(assisted)) / n, 2),
        "per_case": {cs["case_id"]: {"manual": m, "assisted": a}
                     for cs, m, a in zip(case_scores, manual, assisted)},
    }
