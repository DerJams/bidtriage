"""Baseline: one direct call, raw document text, no tools, no verification.

This must stay a fair, reasonable, basic approach. It is not sandbagged and it
will not be improved -- its whole job is to be the honest "what you'd do first"
comparison point.

Two choices worth stating, both made to keep the comparison fair rather than
flattering:

* It uses the same structured-output schema as the solution. Without that the
  baseline would lose points for malformed JSON, and the lever deltas would
  partly measure formatting robustness instead of extraction.
* It is given the same contractor facts as the solution, in prose. A triage
  decision is not well-posed without them. Lever 3's job is to make those
  criteria explicit and scored, not to be the first to mention them.

"No retries" means no semantic retry: the model gets one shot and there is no
self-correction, re-ask, or verification pass. Network-level retry on HTTP 429
still applies, because with allow_fallbacks disabled a rate limit is a hard
failure of the infrastructure, not of the approach. Conflating the two would
measure OpenRouter's queue depth instead of the method.
"""
from __future__ import annotations

import json

from evals.harness import client
from evals.harness.schema import response_format

SYSTEM = """You are helping the operations coordinator at Summit Peak Mechanical, \
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

USER_TEMPLATE = """Inbound bid request ({case_id}, {fmt}):

---
{document}
---

Extract the fields and recommend bid / no_bid / insufficient_information."""


def run(case_id: str, gold: dict, document_text: str) -> tuple:
    """Return (prediction_dict_or_None, flagged_fields, call_result)."""
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER_TEMPLATE.format(
            case_id=case_id, fmt=gold.get("format", "document"),
            document=document_text)},
    ]
    res = client.call(messages, response_format=response_format())

    if not res.ok:
        return None, [], res

    try:
        prediction = json.loads(res.content or "")
    except (json.JSONDecodeError, TypeError):
        prediction = None
        res.error = "unparseable JSON content"

    # The baseline never flags anything for human review. That capability is
    # what lever 2 introduces.
    return prediction, [], res
