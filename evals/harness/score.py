"""Deterministic scoring, implementing docs/scoring-rules.md exactly.

No model calls. Same input always produces the same score.
"""
from __future__ import annotations

from evals.harness.normalize import (
    REQUIRED_FIELDS,
    TRADE_VOCAB,
    UNPARSEABLE,
    normalize_field,
)

CORRECT = "correct"
CORRECT_ABSTENTION = "correct_abstention"
INCORRECT = "incorrect"
MISSED = "missed"
HALLUCINATED = "hallucinated"
FLAGGED = "flagged_for_review"

COUNTS_AS_CORRECT = (CORRECT, CORRECT_ABSTENTION)
COUNTS_AS_ASSERTED = (CORRECT, INCORRECT, HALLUCINATED)
COUNTS_AS_HALLUCINATION = (INCORRECT, HALLUCINATED)

BOND_SUBKEYS = ("required", "bid_bond_pct", "performance_bond_pct",
                "payment_bond_pct", "gl_limit_usd",
                "gl_per_occurrence_usd", "gl_aggregate_usd")


def _equal(field: str, gold_norm, pred_norm) -> bool:
    if field == "trade_scope":
        if not isinstance(pred_norm, list):
            return False
        if set(pred_norm) - TRADE_VOCAB:
            return False  # outside closed vocabulary
        return sorted(pred_norm) == sorted(gold_norm)
    if field == "bond_insurance":
        if not isinstance(pred_norm, dict) or not isinstance(gold_norm, dict):
            return False
        return pred_norm == gold_norm  # exact key set AND values
    if field == "estimated_project_value":
        if not isinstance(pred_norm, dict) or not isinstance(gold_norm, dict):
            return False
        return (pred_norm.get("low") == gold_norm.get("low")
                and pred_norm.get("high") == gold_norm.get("high"))
    return pred_norm == gold_norm


def _bond_diagnostics(gold_norm, pred_norm) -> dict:
    """Per-subcomponent match detail. Diagnostic only; headline stays binary."""
    diag = {}
    g = gold_norm if isinstance(gold_norm, dict) else {}
    p = pred_norm if isinstance(pred_norm, dict) else {}
    for k in BOND_SUBKEYS:
        in_g, in_p = k in g, k in p
        if not in_g and not in_p:
            continue
        if in_g and not in_p:
            diag[k] = "missing"
        elif in_p and not in_g:
            diag[k] = "extra_asserted"
        else:
            diag[k] = "match" if g[k] == p[k] else "mismatch(gold=%s,pred=%s)" % (g[k], p[k])
    return diag


def score_case(gold: dict, prediction: dict | None, flagged: list | None = None) -> dict:
    """Score one case. `flagged` names fields the system sent to human review."""
    flagged = set(flagged or [])
    pred = prediction if isinstance(prediction, dict) else {}
    out = {"case_id": gold.get("case_id"), "fields": {}, "bond_diagnostics": {}}

    for field in REQUIRED_FIELDS:
        gspec = gold["fields"][field]
        gold_present = gspec["present_in_source"]
        gold_norm = gspec["normalized"]

        raw = pred.get(field, None)
        if field in flagged:
            outcome, pred_norm = FLAGGED, None
        else:
            pred_norm = normalize_field(field, raw)
            if pred_norm is None:
                outcome = CORRECT_ABSTENTION if not gold_present else MISSED
            elif pred_norm is UNPARSEABLE:
                # Asserted something unreadable: an assertion, and a wrong one.
                outcome = HALLUCINATED if not gold_present else INCORRECT
            elif not gold_present:
                outcome = HALLUCINATED
            else:
                outcome = CORRECT if _equal(field, gold_norm, pred_norm) else INCORRECT

        out["fields"][field] = {
            "outcome": outcome,
            "gold_present": gold_present,
            "gold_normalized": gold_norm,
            "pred_raw": raw,
            "pred_normalized": (str(pred_norm) if pred_norm is UNPARSEABLE else pred_norm),
        }
        if field == "bond_insurance":
            out["bond_diagnostics"] = _bond_diagnostics(gold_norm, pred_norm)

    return out


def score_triage(gold: dict, prediction: dict | None) -> dict:
    """Triage is reported separately and never enters field accuracy."""
    g = gold.get("triage") or {}
    p = prediction if isinstance(prediction, dict) else {}
    pred_decision = p.get("triage_decision") or p.get("decision")
    pred_decision = (str(pred_decision).strip().lower().replace("-", "_").replace(" ", "_")
                     if pred_decision is not None else None)
    if pred_decision in ("go", "bid_it"):
        pred_decision = "bid"
    if pred_decision in ("no_go", "nobid", "no_bid"):
        pred_decision = "no_bid"

    gold_reasons = set(g.get("required_reasons") or [])
    raw_reasons = p.get("triage_reasons") or p.get("reasons") or []
    if isinstance(raw_reasons, str):
        raw_reasons = [raw_reasons]
    pred_reasons = {str(r).strip().lower().replace(" ", "_") for r in raw_reasons}

    return {
        "gold_decision": g.get("decision"),
        "pred_decision": pred_decision,
        "decision_correct": pred_decision == g.get("decision"),
        "gold_reasons": sorted(gold_reasons),
        "pred_reasons": sorted(pred_reasons),
        "reasons_recall": (len(gold_reasons & pred_reasons) / len(gold_reasons)
                           if gold_reasons else None),
    }


def aggregate(case_scores: list) -> dict:
    """Roll per-case scores into the frozen metrics."""
    tally = {k: 0 for k in (CORRECT, CORRECT_ABSTENTION, INCORRECT,
                            MISSED, HALLUCINATED, FLAGGED)}
    per_field = {}

    for cs in case_scores:
        for field, fs in cs["fields"].items():
            o = fs["outcome"]
            tally[o] += 1
            pf = per_field.setdefault(field, {k: 0 for k in tally})
            pf[o] += 1

    total = sum(tally.values())
    correct = tally[CORRECT] + tally[CORRECT_ABSTENTION]
    asserted = sum(tally[k] for k in COUNTS_AS_ASSERTED)
    halluc = sum(tally[k] for k in COUNTS_AS_HALLUCINATION)

    return {
        "total_slots": total,
        "outcomes": tally,
        "field_accuracy": (correct / total) if total else 0.0,
        "correct_slots": correct,
        "asserted_fields": asserted,
        "hallucination_count": halluc,
        # Judged metric: asserted-field denominator.
        "hallucination_rate_asserted": (halluc / asserted) if asserted else 0.0,
        # Diagnostic only: fixed /total denominator.
        "hallucination_rate_all_slots": (halluc / total) if total else 0.0,
        "per_field": {
            f: {**c,
                "accuracy": (c[CORRECT] + c[CORRECT_ABSTENTION]) / max(1, sum(c.values()))}
            for f, c in sorted(per_field.items())
        },
    }
