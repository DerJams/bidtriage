"""BidTriage solution. Levers are added one at a time and measured.

Select active levers with the BIDTRIAGE_LEVERS environment variable, e.g.

    BIDTRIAGE_LEVERS=lever2 python -m evals.run --target solution

Lever 2 -- verification with programmatic span checking
-------------------------------------------------------
Pass 1 extracts (identical to the baseline). Pass 2 re-reads the source and
returns, per field, a status and a VERBATIM span.

The span is what makes this more than self-assessment. A model saying "yes, I
checked" is worth nothing. A model that must produce a quote which is then
searched for character-for-character in the source document is making a
checkable claim. Reconciliation below does that search, and a field whose
claimed span cannot be found is downgraded to human review rather than
believed.

Reconciliation is deterministic -- no model call decides the final outcome:

    NOT_STATED                  -> value becomes null (abstain)
    UNCERTAIN                   -> flag for human review
    SUPPORTED + span found      -> keep the verified value
    SUPPORTED + span NOT found  -> flag (claimed support it could not produce)
    SUPPORTED + value is null   -> flag (self-contradictory)
    trade_scope out of vocab    -> flag (invalid against the closed vocabulary)

Flagging deliberately costs field accuracy while protecting the hallucination
rate. That asymmetry is the whole point: if flagging were free, the lever would
be scoring itself.
"""
from __future__ import annotations

import json
import os
import re

from evals.harness import client
from evals.harness.normalize import TRADE_VOCAB, norm_trades
from evals.harness.schema import response_format as extract_response_format
from solution import brief
from solution import triage as triage_mod
from solution import verify_schema

ALL_LEVERS = ("lever1_parse", "lever2_verify", "lever3_triage", "lever4_brief")


def _active_levers() -> tuple:
    raw = os.environ.get("BIDTRIAGE_LEVERS", "lever2_verify")
    wanted = {t.strip() for t in raw.split(",") if t.strip()}
    unknown = wanted - set(ALL_LEVERS)
    if unknown:
        raise SystemExit("unknown lever(s): %s" % sorted(unknown))
    return tuple(l for l in ALL_LEVERS if l in wanted)


ACTIVE_LEVERS = _active_levers()

EXTRACT_SYSTEM = """You are helping the operations coordinator at Summit Peak Mechanical, \
a small commercial mechanical contractor based in Golden, Colorado.

Summit Peak self-performs HVAC, plumbing, piping, sheet metal, and controls work. \
It does not self-perform refrigeration or fire protection. It works within about \
90 miles of Golden, takes projects roughly between $250,000 and $3,000,000, and \
can run at most 3 projects at once. It currently has commitments running from \
September 2026 into March 2027.

Read the inbound bid request below and extract the required fields, then \
recommend whether to bid.

Return only the JSON object described by the schema. If the document does not \
state something, return null for it rather than guessing."""

VERIFY_SYSTEM = """You are verifying a draft extraction from a bid document for \
Summit Peak Mechanical, a small commercial mechanical contractor in Golden, Colorado.

Your job is to check the draft against the source document, field by field, and \
correct it. You are not being asked to agree with it.

For every field, decide one of:

  SUPPORTED   The source explicitly states this. Copy the exact supporting text \
into "span", VERBATIM, character for character from the document. Do not \
paraphrase, do not summarise, do not tidy the punctuation. The quote is searched \
for in the document and a quote that cannot be found is treated as unsupported.

  EXPLICITLY_NONE  The source explicitly says this thing does not exist or will \
not happen -- for example "a pre-bid walk-through will not be held". The correct \
value is null, and "span" quotes that statement. Note the difference from a \
bonding requirement: "no bonding is required" is a bonding VALUE \
(required=false), not a null, so that case is SUPPORTED, not EXPLICITLY_NONE.

  NOT_STATED  The source is simply silent, or does not state this at the \
specificity the field requires, so the correct value is null. A document that \
says only "Category: Mechanical" has NOT stated a specific trade scope. A \
document that says nothing at all about bonding has NOT stated bonding \
requirements.

  UNCERTAIN   The source is ambiguous, or two parts of it conflict, and a person \
should decide. Use this sparingly and only when you genuinely cannot resolve it.

Rules that matter:

* Where a document has been amended, the amendment controls. A date repeated in \
page footers is not evidence; an addendum that supersedes it is.
* Alternates are not base scope. Work priced under an alternate is excluded.
* "No bonding is required" is a real, positive finding. If the source explicitly \
says no bonds are required, that is SUPPORTED with required=false -- it is NOT \
NOT_STATED, and it is not null.
* Trade scope must use only: hvac, plumbing, piping, sheet_metal, controls, \
refrigeration, fire_protection. If the document does not identify a specific \
trade from that list, the field is NOT_STATED.
* Do not invent a bonding requirement the source never mentions. Omit what is \
not stated rather than assuming a standard value.

You are checking the eight extracted fields only. You are NOT being asked to \
re-decide the bid/no-bid triage; copy whatever the draft says for \
triage_decision and triage_reasons straight through unchanged.

Return the corrected extraction in "verified" and your per-field findings in \
"evidence"."""


def _ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _span_found(span: str, source: str) -> bool:
    """Verbatim check, tolerant only of whitespace and case."""
    if not span or not span.strip():
        return False
    return _ws(span).casefold() in _ws(source).casefold()


def _extract(case_id, gold, document_text):
    messages = [
        {"role": "system", "content": EXTRACT_SYSTEM},
        {"role": "user", "content": "Inbound bid request (%s, %s):\n\n---\n%s\n---\n\n"
                                    "Extract the fields and recommend bid / no_bid / "
                                    "insufficient_information."
                                    % (case_id, gold.get("format", "document"), document_text)},
    ]
    res = client.call(messages, response_format=extract_response_format())
    if not res.ok:
        return None, res
    try:
        return json.loads(res.content or ""), res
    except (json.JSONDecodeError, TypeError):
        res.error = "unparseable JSON content (extract)"
        return None, res


def _verify(case_id, draft, document_text):
    messages = [
        {"role": "system", "content": VERIFY_SYSTEM},
        {"role": "user", "content": "Source document (%s):\n\n---\n%s\n---\n\n"
                                    "Draft extraction to check:\n\n%s"
                                    % (case_id, document_text,
                                       json.dumps(draft, indent=2))},
    ]
    res = client.call(messages, response_format=verify_schema.response_format())
    if not res.ok:
        return None, res
    try:
        return json.loads(res.content or ""), res
    except (json.JSONDecodeError, TypeError):
        res.error = "unparseable JSON content (verify)"
        return None, res


TRIAGE_SYSTEM = """You are deciding whether Summit Peak Mechanical should bid a \
project, using explicit capacity criteria.

Work through every criterion in order and evaluate it against the extracted \
fields and the source document. Give a short reason for each, citing the actual \
figures you used. Do not decide by overall impression: a project that fits the \
trades and the budget is still a no_bid if the crew is already committed.

Pay particular attention to the timeline criterion. You must find the \
construction window in the document, then work out whether it overlaps a period \
during which the contractor is already running its maximum number of concurrent \
projects. Overlapping by a single day is a conflict."""


def _triage(case_id, fields, document_text):
    messages = [
        {"role": "system", "content": TRIAGE_SYSTEM},
        {"role": "user", "content": "%s\n\nEXTRACTED FIELDS for %s:\n\n%s\n\n"
                                    "SOURCE DOCUMENT:\n\n---\n%s\n---\n\n"
                                    "Evaluate all four criteria and decide."
                                    % (triage_mod.render_criteria(), case_id,
                                       json.dumps(fields, indent=2), document_text)},
    ]
    res = client.call(messages, response_format=triage_mod.response_format())
    if not res.ok:
        return None, res
    try:
        return json.loads(res.content or ""), res
    except (json.JSONDecodeError, TypeError):
        res.error = "unparseable JSON content (triage)"
        return None, res


def _reconcile(verified: dict, evidence: dict, source: str):
    """Deterministic. No model call decides the final outcome."""
    prediction = dict(verified or {})
    flagged, audit = [], {}

    for field, ev in (evidence or {}).items():
        status = (ev or {}).get("status")
        span = (ev or {}).get("span")
        value = prediction.get(field)
        verdict = None

        if status == "NOT_STATED":
            prediction[field] = None
            verdict = "abstained_silent"
        elif status == "EXPLICITLY_NONE":
            # The document says there is none. That is evidence FOR null, not a
            # contradiction. Treating it as one cost a point the baseline had.
            prediction[field] = None
            verdict = "abstained_explicit"
        elif status == "UNCERTAIN":
            flagged.append(field)
            verdict = "flagged_uncertain"
        elif status == "SUPPORTED":
            if value is None:
                flagged.append(field)
                verdict = "flagged_supported_but_null"
            elif not _span_found(span or "", source):
                flagged.append(field)
                verdict = "flagged_span_not_found"
            else:
                verdict = "kept_span_verified"
        else:
            flagged.append(field)
            verdict = "flagged_bad_status"

        audit[field] = {"status": status, "verdict": verdict, "span": span,
                        "span_verified": bool(span) and _span_found(span or "", source)}

    # Closed-vocabulary guard. An unrecognised trade is not a low-confidence
    # guess we should publish; it is exactly the "I am not sure, look at this"
    # case the lever exists to surface.
    trades = prediction.get("trade_scope")
    if trades is not None and "trade_scope" not in flagged:
        norm = norm_trades(trades)
        if not isinstance(norm, list) or (set(norm) - TRADE_VOCAB):
            flagged.append("trade_scope")
            audit.setdefault("trade_scope", {})["verdict"] = "flagged_out_of_vocabulary"

    return prediction, sorted(set(flagged)), audit


def _merge_accounting(target, *others):
    """Fold token, cost, retry and latency accounting across multiple calls."""
    for o in others:
        if o is None:
            continue
        target.prompt_tokens += o.prompt_tokens
        target.completion_tokens += o.completion_tokens
        target.cost_usd += o.cost_usd
        target.retries += o.retries
        target.attempts += o.attempts
        target.retry_log = list(target.retry_log) + list(o.retry_log)
        target.latency_s += o.latency_s
    return target


def _apply_triage(prediction, case_id, document_text, combined):
    """Lever 3. The model evaluates the criteria; code combines them."""
    payload, res3 = _triage(case_id, prediction, document_text)
    _merge_accounting(combined, res3)

    if payload is None:
        combined.error = (combined.error or "") + " | triage failed, kept prior decision"
        return prediction

    criteria = payload.get("criteria") or {}
    rule_decision, rule_reasons = triage_mod.apply_rule(criteria)
    model_decision = payload.get("decision")

    prediction["triage_decision"] = rule_decision
    prediction["triage_reasons"] = rule_reasons

    # Recorded so the rule's contribution is visible rather than assumed.
    combined.triage_audit = {
        "model_decision": model_decision,
        "rule_decision": rule_decision,
        "model_agreed_with_rule": model_decision == rule_decision,
        "criteria": {c: (criteria.get(c) or {}).get("value") for c in triage_mod.CRITERIA},
        "criteria_reasons": {c: (criteria.get(c) or {}).get("reason")
                             for c in triage_mod.CRITERIA},
        "construction_window": payload.get("construction_window"),
    }
    return prediction


def run(case_id: str, gold: dict, document_text: str) -> tuple:
    draft, res1 = _extract(case_id, gold, document_text)
    if draft is None:
        return None, [], res1

    if "lever2_verify" not in ACTIVE_LEVERS:
        combined = res1
        if "lever3_triage" in ACTIVE_LEVERS:
            draft = _apply_triage(draft, case_id, document_text, combined)
        _attach_brief(combined, case_id, draft, [], None)
        return draft, [], combined

    payload, res2 = _verify(case_id, draft, document_text)

    # Merge accounting across calls so cost and retries stay truthful.
    combined = res2 if res2 is not None else res1
    if res2 is not None:
        combined.prompt_tokens = res1.prompt_tokens + res2.prompt_tokens
        combined.completion_tokens = res1.completion_tokens + res2.completion_tokens
        combined.cost_usd = res1.cost_usd + res2.cost_usd
        combined.retries = res1.retries + res2.retries
        combined.attempts = res1.attempts + res2.attempts
        combined.retry_log = list(res1.retry_log) + list(res2.retry_log)
        combined.latency_s = res1.latency_s + res2.latency_s

    if payload is None:
        # Verification failed: fall back to the draft rather than losing the case,
        # and say so loudly in the result rather than silently degrading.
        combined.error = (combined.error or "") + " | verify failed, used draft"
        if "lever3_triage" in ACTIVE_LEVERS:
            draft = _apply_triage(draft, case_id, document_text, combined)
        return draft, [], combined

    prediction, flagged, audit = _reconcile(
        payload.get("verified") or {}, payload.get("evidence") or {}, document_text)

    # Lever isolation: lever 2 verifies the eight extracted FIELDS. It does not
    # decide triage -- that is lever 3. The verifier's schema carries the triage
    # keys because it reuses the extraction shape, and left to itself the model
    # nulls them, which showed up as a spurious 11pp triage "regression". Carry
    # triage through from the extraction pass so each lever is measured on the
    # thing it actually changes.
    prediction["triage_decision"] = draft.get("triage_decision")
    prediction["triage_reasons"] = draft.get("triage_reasons")

    combined.verification_audit = audit

    if "lever3_triage" in ACTIVE_LEVERS:
        prediction = _apply_triage(prediction, case_id, document_text, combined)

    _attach_brief(combined, case_id, prediction, flagged, audit)
    return prediction, flagged, combined


def _attach_brief(combined, case_id, prediction, flagged, audit=None):
    """Lever 4. Renders from what is already verified; makes no model call.

    Citations come from spans the verification pass produced and that
    reconciliation then located in the source, so the brief can only quote text
    that was actually found in the document.
    """
    if "lever4_brief" not in ACTIVE_LEVERS:
        return
    evidence = {f: {"span": a.get("span")}
                for f, a in (audit or {}).items()
                if a.get("span") and a.get("span_verified")}
    text = brief.render(case_id, prediction, flagged, evidence,
                        getattr(combined, "triage_audit", None))
    combined.brief = text
    combined.brief_checks = brief.brief_checks(text, prediction, flagged, evidence)
