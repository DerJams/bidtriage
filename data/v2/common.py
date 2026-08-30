"""Shared helpers for the corpus v2 case definitions.

A case is a list of BLOCKS. A block tagged with a scored field name becomes
both the document text and that field's gold `source_span`, so spans are
verbatim by construction.

`normalized` values here are typed independently rather than produced by the
production normalizer. That is deliberate: build.py checks the two against each
other, and if gold were derived from the same code the scorer uses, a
normalizer bug would propagate into gold and the check would be vacuous. This
is what caught the `co` suffix bug in v1.

Commercial terms follow the conventions documented in docs/corpus-v2-design.md:
bid bonds 5 to 10 percent on private and municipal work and up to 20 percent on
federal Miller Act work, performance and payment bonds at 100 percent, and
commercial general liability at 2M per occurrence / 4M aggregate for these
trades rather than the 1M/2M general baseline.
"""
from __future__ import annotations

import re

V2E = "data/synthetic/emails_v2"
V2P = "data/synthetic/pdfs_v2"


def low(s: str) -> str:
    """Independent minimal string normalizer, deliberately not the production one."""
    t = re.sub(r"\s+", " ", s).strip().lower()
    t = t.strip(" .,;:-\"'")
    for suf in (" inc", " llc", " ltd", " corp", " incorporated", " corporation"):
        if t.endswith(suf):
            t = t[: -len(suf)].strip(" ,")
    return t


def M(low_v, high_v=None):
    return {"low": low_v, "high": high_v if high_v is not None else low_v,
            "currency": "USD"}


def bond(required=True, bid=None, perf=None, pay=None, occ=None, agg=None):
    if not required:
        return {"required": False}
    d = {"required": True}
    if bid is not None:
        d["bid_bond_pct"] = bid
    if perf is not None:
        d["performance_bond_pct"] = perf
    if pay is not None:
        d["payment_bond_pct"] = pay
    if occ is not None:
        d["gl_per_occurrence_usd"] = occ
    if agg is not None:
        d["gl_aggregate_usd"] = agg
    return d


def F(value, normalized, extra=None):
    return {"value": value, "normalized": normalized, "extra": extra or {}}


def email_part(path, frm, to, subject, date, blocks, role="document"):
    return {"path": path, "kind": "email", "role": role,
            "headers": {"from": frm, "to": to, "subject": subject, "date": date},
            "blocks": blocks}


def pdf_part(path, blocks, role="document"):
    return {"path": path, "kind": "pdf", "role": role, "blocks": blocks}


TO = "estimating@summitpeakmech.example"
STD_BOND_TEXT = ("Bonding: bid bond 5% of the total bid; performance bond and payment "
                 "bond each 100% of the contract price. Commercial general liability "
                 "$2,000,000 per occurrence and $4,000,000 aggregate.")
STD_BOND = bond(bid=5, perf=100, pay=100, occ=2000000, agg=4000000)

MUNI_BOND_TEXT = ("Bid security shall be 10% of the bid amount. Performance and payment "
                  "bonds are each 100% of the contract price. Contractor shall carry "
                  "commercial general liability of $2,000,000 per occurrence and "
                  "$4,000,000 aggregate.")
MUNI_BOND = bond(bid=10, perf=100, pay=100, occ=2000000, agg=4000000)



