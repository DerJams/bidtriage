"""Schema for the verification pass (lever 2).

The verifier returns two things per case:

* `verified` -- the full corrected extraction, same shape as the extraction
  schema. The verifier may retract a value it cannot support, or recover one
  the first pass missed.
* `evidence` -- per field, a status and a VERBATIM span from the source.

The span is the point. A model asserting "yes I checked" is worth nothing; a
model producing a quote that must then be found character-for-character in the
source document is checkable. The reconciliation step in run_solution.py does
that check programmatically, so a claimed-but-absent span downgrades the field
to human review rather than being taken at face value.
"""
from __future__ import annotations

from evals.harness.schema import EXTRACTION_SCHEMA

STATUS_VALUES = ["SUPPORTED", "EXPLICITLY_NONE", "NOT_STATED", "UNCERTAIN"]

_EVIDENCE_FIELDS = ["client_name", "project_title", "trade_scope", "location",
                    "bid_due_date", "estimated_project_value", "bond_insurance",
                    "walkthrough_date"]

_evidence_props = {
    f: {
        "type": "object",
        "additionalProperties": False,
        "required": ["status", "span"],
        "properties": {
            "status": {
                "type": "string",
                "enum": STATUS_VALUES,
                "description": (
                    "SUPPORTED: the source explicitly states a value, and the span "
                    "below quotes it. "
                    "EXPLICITLY_NONE: the source explicitly states that this thing "
                    "does not exist or will not happen (e.g. 'no walk-through will "
                    "be held'), so the correct value is null and the span quotes "
                    "that statement. "
                    "NOT_STATED: the source is simply silent, or does not state it "
                    "at the required specificity, so the correct value is null. "
                    "UNCERTAIN: the source is ambiguous or conflicting and a human "
                    "should decide."),
            },
            "span": {
                "type": ["string", "null"],
                "description": ("VERBATIM quote copied character-for-character from "
                                "the source document. Required when status is "
                                "SUPPORTED. Null otherwise. Do not paraphrase; the "
                                "quote is checked against the document."),
            },
        },
    }
    for f in _EVIDENCE_FIELDS
}

VERIFICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["verified", "evidence"],
    "properties": {
        "verified": {
            "type": "object",
            "additionalProperties": False,
            "required": EXTRACTION_SCHEMA["required"],
            "properties": EXTRACTION_SCHEMA["properties"],
            "description": "The corrected extraction after checking the source.",
        },
        "evidence": {
            "type": "object",
            "additionalProperties": False,
            "required": _EVIDENCE_FIELDS,
            "properties": _evidence_props,
        },
    },
}


def response_format(name: str = "bid_verification") -> dict:
    return {"type": "json_schema",
            "json_schema": {"name": name, "strict": True, "schema": VERIFICATION_SCHEMA}}
