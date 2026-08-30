"""The output contract, shared by every target.

Baseline and solution emit the SAME JSON shape via the same structured-output
schema. That is deliberate: without it, the baseline would lose points for
malformed JSON, and the measured lever deltas would partly reflect formatting
robustness rather than extraction accuracy. Holding the output contract fixed
keeps the comparison about the thing being measured.

Every field is nullable. Emitting null is how a target abstains, and abstention
is a legitimate -- sometimes correct -- answer, since 8 of the 96 gold slots are
legitimately absent from their source documents.
"""
from __future__ import annotations

_NULLABLE_STR = {"type": ["string", "null"]}
_NULLABLE_NUM = {"type": ["number", "null"]}

EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "client_name", "project_title", "trade_scope", "location",
        "bid_due_date", "estimated_project_value", "bond_insurance",
        "walkthrough_date", "triage_decision", "triage_reasons",
    ],
    "properties": {
        "client_name": _NULLABLE_STR,
        "project_title": _NULLABLE_STR,
        "trade_scope": {
            "type": ["array", "null"],
            "items": {"type": "string"},
            "description": ("Trades in the BASE scope only. Allowed values: hvac, "
                            "plumbing, piping, sheet_metal, controls, refrigeration, "
                            "fire_protection. Null if the document does not say."),
        },
        "location": _NULLABLE_STR,
        "bid_due_date": {**_NULLABLE_STR,
                         "description": "ISO YYYY-MM-DD. The date actually in force."},
        "estimated_project_value": {
            **_NULLABLE_STR,
            "description": "As written, e.g. '$850,000' or '$1,800,000 to $2,100,000'.",
        },
        "bond_insurance": {
            "type": ["object", "null"],
            "additionalProperties": False,
            "required": ["required", "bid_bond_pct", "performance_bond_pct",
                         "payment_bond_pct", "gl_limit_usd"],
            "properties": {
                "required": {"type": ["boolean", "null"],
                             "description": "false only if the source explicitly "
                                            "states no bonding is required."},
                "bid_bond_pct": _NULLABLE_NUM,
                "performance_bond_pct": _NULLABLE_NUM,
                "payment_bond_pct": _NULLABLE_NUM,
                "gl_limit_usd": _NULLABLE_NUM,
            },
            "description": ("Null only if the source says nothing about bonding or "
                            "insurance. Use null for any individual requirement the "
                            "source does not state -- do not assume a standard value."),
        },
        "walkthrough_date": {**_NULLABLE_STR, "description": "ISO YYYY-MM-DD, or null."},
        "triage_decision": {
            "type": ["string", "null"],
            "enum": ["bid", "no_bid", "insufficient_information", None],
        },
        "triage_reasons": {"type": ["array", "null"], "items": {"type": "string"}},
    },
}


def response_format(name: str = "bid_extraction") -> dict:
    return {"type": "json_schema",
            "json_schema": {"name": name, "strict": True, "schema": EXTRACTION_SCHEMA}}
