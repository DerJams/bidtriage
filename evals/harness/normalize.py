"""Deterministic normalizers, one per match rule in docs/scoring-rules.md.

Pure functions, no model calls, no randomness. The same normalizer is applied
to the baseline and to every solution lever, so no target can win on
formatting. Anything that cannot be parsed returns UNPARSEABLE, which scores as
wrong rather than silently as a miss -- a value the system asserted but that
cannot be read is not an abstention.
"""
from __future__ import annotations

import re
from datetime import date

UNPARSEABLE = "__UNPARSEABLE__"

TRADE_VOCAB = {"hvac", "plumbing", "piping", "sheet_metal", "controls",
               "refrigeration", "fire_protection"}

# Synonym map. Extraction is being measured, not vocabulary luck, so common
# phrasings collapse onto the closed vocabulary. Applied identically to every
# target. Anything not mapped stays as-is and fails the vocabulary check.
TRADE_SYNONYMS = {
    "hvac": "hvac", "heating ventilation and air conditioning": "hvac",
    "heating, ventilation, and air conditioning": "hvac", "mechanical (hvac)": "hvac",
    "air conditioning": "hvac", "heating": "hvac", "ventilation": "hvac",
    "plumbing": "plumbing", "domestic water": "plumbing",
    "piping": "piping", "process piping": "piping", "hydronic piping": "piping",
    "process and hydronic piping": "piping", "hydronic": "piping",
    "sheet metal": "sheet_metal", "sheet_metal": "sheet_metal",
    "sheetmetal": "sheet_metal", "ductwork": "sheet_metal",
    "controls": "controls", "automatic temperature controls": "controls",
    "temperature controls": "controls", "ddc": "controls",
    "building automation": "controls", "bas": "controls",
    "building automation system": "controls", "direct digital controls": "controls",
    "refrigeration": "refrigeration", "ammonia refrigeration": "refrigeration",
    "fire protection": "fire_protection", "fire_protection": "fire_protection",
    "fire suppression": "fire_protection", "sprinkler": "fire_protection",
    "standpipe": "fire_protection", "fire sprinkler": "fire_protection",
}

_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

_WORD_NUMS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20,
    "twenty-five": 25, "fifty": 50, "seventy-five": 75, "one hundred": 100,
    "hundred": 100,
}

# "co" is deliberately NOT here. It is a corporate suffix, but it is also the
# Colorado state abbreviation, and every location in this corpus ends in ", CO".
# Including it silently truncated "denver, co" to "denver" and would have failed
# all 12 location fields. Caught by selftest.py.
_SUFFIXES = ("inc", "llc", "ltd", "corp", "incorporated", "corporation")


def _ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# --- normalized_string -----------------------------------------------------

def norm_string(v):
    if v is None:
        return None
    if not isinstance(v, str):
        v = str(v)
    s = _ws(v).casefold()
    s = s.strip(" .,;:-–—\"'")
    parts = s.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].strip(".,") in _SUFFIXES:
        s = parts[0].strip(" ,")
    return s or UNPARSEABLE


# --- iso_date --------------------------------------------------------------

def norm_date(v):
    if v is None:
        return None
    if not isinstance(v, str):
        v = str(v)
    s = _ws(v)

    # Lookarounds, not \b: an ISO datetime like "2026-09-25T14:00:00-06:00" has
    # no word boundary before the T, so \b made a MORE precise correct answer
    # score as unparseable. Caught by the first single-case smoke run.
    m = re.search(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            return UNPARSEABLE

    m = re.search(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", s)
    if m and m.group(1).lower() in _MONTHS:
        try:
            return date(int(m.group(3)), _MONTHS[m.group(1).lower()],
                        int(m.group(2))).isoformat()
        except ValueError:
            return UNPARSEABLE

    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b", s)
    if m and m.group(2).lower() in _MONTHS:
        try:
            return date(int(m.group(3)), _MONTHS[m.group(2).lower()],
                        int(m.group(1))).isoformat()
        except ValueError:
            return UNPARSEABLE

    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", s)
    if m:  # US convention, matching the corpus
        try:
            return date(int(m.group(3)), int(m.group(1)), int(m.group(2))).isoformat()
        except ValueError:
            return UNPARSEABLE

    return UNPARSEABLE


# --- currency_interval -----------------------------------------------------

_MULT = {"k": 1_000, "m": 1_000_000, "mm": 1_000_000, "b": 1_000_000_000,
         "thousand": 1_000, "million": 1_000_000, "billion": 1_000_000_000}


def _one_amount(tok: str):
    tok = tok.strip().lower().replace("$", "").replace(",", "").strip()
    # Anchored at the start but tolerant of trailing text. A full-string match
    # meant "$2,100,000 (engineer estimate)" parsed as nothing, so a correctly
    # extracted RANGE silently collapsed to a point value and scored wrong.
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(k|mm|m|b|thousand|million|billion)?\b", tok)
    if not m:
        return None
    val = float(m.group(1))
    if m.group(2):
        val *= _MULT[m.group(2)]
    return int(round(val))


def norm_money(v):
    if v is None:
        return None
    if isinstance(v, dict) and "low" in v and "high" in v:
        try:
            return {"low": int(v["low"]), "high": int(v["high"]),
                    "currency": v.get("currency", "USD")}
        except (TypeError, ValueError):
            return UNPARSEABLE
    if isinstance(v, (int, float)):
        return {"low": int(v), "high": int(v), "currency": "USD"}
    if not isinstance(v, str):
        return UNPARSEABLE

    s = _ws(v).lower()
    s = re.sub(r"\([^)]*\)", " ", s)  # drop parentheticals e.g. "(engineer estimate)"
    s = re.sub(r"\b(approximately|approx\.?|about|est\.?|estimated|engineer'?s estimate"
               r"|budget|around|circa|usd)\b", " ", s)
    s = _ws(s)

    parts = re.split(r"\s*(?:-|–|—|to|through|and)\s*", s)
    amounts = [a for a in (_one_amount(p) for p in parts if p.strip()) if a is not None]

    if not amounts:
        nums = re.findall(r"\$?\s*\d[\d,]*(?:\.\d+)?\s*(?:k|mm|m|b|thousand|million|billion)?", s)
        amounts = [a for a in (_one_amount(n) for n in nums) if a is not None]
    if not amounts:
        return UNPARSEABLE
    return {"low": min(amounts), "high": max(amounts), "currency": "USD"}


# --- token_set -------------------------------------------------------------

# Keyword -> trade, checked by containment within a token. Ordered longest
# first so "fire protection" wins before a bare "protection" could matter.
_TRADE_KEYWORDS = [
    ("fire protection", "fire_protection"), ("fire suppression", "fire_protection"),
    ("fire sprinkler", "fire_protection"), ("sprinkler", "fire_protection"),
    ("standpipe", "fire_protection"),
    ("sheet metal", "sheet_metal"), ("sheetmetal", "sheet_metal"),
    ("sheet_metal", "sheet_metal"), ("ductwork", "sheet_metal"), ("duct", "sheet_metal"),
    ("refrigeration", "refrigeration"), ("ammonia", "refrigeration"),
    ("plumbing", "plumbing"), ("domestic water", "plumbing"),
    ("piping", "piping"), ("hydronic", "piping"),
    ("controls", "controls"), ("automation", "controls"), ("ddc", "controls"),
    ("bas", "controls"),
    ("hvac", "hvac"), ("air conditioning", "hvac"), ("ventilation", "hvac"),
    ("heating", "hvac"),
]

# Bare modifiers that are not trades on their own. Splitting "process and
# hydronic piping" on " and " strands "process"; without this it would leak
# through as a bogus token. Caught by selftest.py.
_TRADE_MODIFIERS = {"process", "hydronic", "mechanical", "commercial", "new",
                    "existing", "base bid", "base", "general"}


def norm_trades(v):
    if v is None:
        return None
    if isinstance(v, str):
        items = re.split(r"[,;/]| and | & |\n", v)
    elif isinstance(v, (list, tuple, set)):
        items = []
        for x in v:
            items.extend(re.split(r"[,;/]| and | & ", str(x)))
    else:
        return UNPARSEABLE

    out = set()
    for raw in items:
        t = _ws(str(raw)).casefold().strip(" .-()")
        if not t:
            continue
        t = re.sub(r"\s+work$|\s+trade$|\s+scope$", "", t).strip()
        # Never let a negated mention become a positive trade.
        if re.match(r"^(no|not|excluding|excludes|except)\b", t):
            continue
        if t in TRADE_SYNONYMS:
            out.add(TRADE_SYNONYMS[t])
            continue
        hit = next((trade for kw, trade in _TRADE_KEYWORDS if kw in t), None)
        if hit:
            out.add(hit)
        elif t not in _TRADE_MODIFIERS:
            out.add(t.replace(" ", "_"))  # unrecognized: kept so it fails the vocab check
    if not out:
        return UNPARSEABLE
    return sorted(out)


# --- bond_dict -------------------------------------------------------------

def _pct(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return UNPARSEABLE
    if isinstance(v, (int, float)):
        return int(round(float(v)))
    s = _ws(str(v)).lower().replace("percent", "").replace("%", "").strip()
    if s in _WORD_NUMS:
        return _WORD_NUMS[s]
    m = re.search(r"\d+(?:\.\d+)?", s)
    return int(round(float(m.group(0)))) if m else UNPARSEABLE


def _usd(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return UNPARSEABLE
    if isinstance(v, (int, float)):
        return int(v)
    s = _ws(str(v)).lower()
    for word, mult in (("million", 1_000_000), ("thousand", 1_000), ("billion", 1_000_000_000)):
        m = re.search(r"(\d+(?:\.\d+)?)\s*" + word, s)
        if m:
            return int(round(float(m.group(1)) * mult))
    for word, num in _WORD_NUMS.items():
        if re.search(r"\b" + re.escape(word) + r"\s+million\b", s):
            return num * 1_000_000
    got = _one_amount(s)
    return got if got is not None else UNPARSEABLE


_BOND_KEYMAP = {
    "required": "required", "bonding_required": "required", "bonds_required": "required",
    "bid_bond_pct": "bid_bond_pct", "bid_bond": "bid_bond_pct",
    "bid_bond_percent": "bid_bond_pct", "bid_bond_percentage": "bid_bond_pct",
    "performance_bond_pct": "performance_bond_pct", "performance_bond": "performance_bond_pct",
    "performance_bond_percent": "performance_bond_pct",
    "payment_bond_pct": "payment_bond_pct", "payment_bond": "payment_bond_pct",
    "payment_bond_percent": "payment_bond_pct",
    # v1 single undifferentiated limit
    "gl_limit_usd": "gl_limit_usd", "gl_limit": "gl_limit_usd",
    "general_liability": "gl_limit_usd", "general_liability_limit": "gl_limit_usd",
    "commercial_general_liability": "gl_limit_usd", "gl": "gl_limit_usd",
    "insurance_gl_limit": "gl_limit_usd",
    # v2 split limits. Both shapes are accepted by the normalizer; which one is
    # correct for a given case is decided by the gold key, since the key set must
    # match exactly. That keeps v1 scoring intact while v2 uses the documented
    # per-occurrence and aggregate convention.
    "gl_per_occurrence_usd": "gl_per_occurrence_usd",
    "gl_per_occurrence": "gl_per_occurrence_usd",
    "per_occurrence": "gl_per_occurrence_usd",
    "general_liability_per_occurrence": "gl_per_occurrence_usd",
    "cgl_per_occurrence": "gl_per_occurrence_usd",
    "gl_aggregate_usd": "gl_aggregate_usd",
    "gl_aggregate": "gl_aggregate_usd",
    "aggregate": "gl_aggregate_usd",
    "general_liability_aggregate": "gl_aggregate_usd",
    "cgl_aggregate": "gl_aggregate_usd",
}

_PCT_KEYS = ("bid_bond_pct", "performance_bond_pct", "payment_bond_pct")


def norm_bond(v):
    """Normalize to the frozen dict shape. Key set must match gold exactly."""
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip().lower()
        # Only an explicit statement of "none required" is an assertion.
        if re.search(r"\bno\b.*\bbond", s) or "not required" in s or "no bonding" in s:
            return {"required": False}
        return UNPARSEABLE
    if not isinstance(v, dict):
        return UNPARSEABLE

    out: dict = {}
    for raw_k, raw_v in v.items():
        k = _BOND_KEYMAP.get(_ws(str(raw_k)).casefold().replace(" ", "_").replace("-", "_"))
        if k is None:
            continue  # unknown keys ignored; they cannot rescue a wrong dict
        if raw_v is None:
            continue
        if k == "required":
            if isinstance(raw_v, bool):
                out["required"] = raw_v
            elif isinstance(raw_v, str):
                out["required"] = raw_v.strip().lower() in ("true", "yes", "required")
            else:
                return UNPARSEABLE
        elif k in _PCT_KEYS:
            got = _pct(raw_v)
            if got is UNPARSEABLE:
                return UNPARSEABLE
            if got is not None:
                out[k] = got
        else:
            got = _usd(raw_v)
            if got is UNPARSEABLE:
                return UNPARSEABLE
            if got is not None:
                out[k] = got

    if not out:
        return UNPARSEABLE
    # A dict carrying any real requirement implies required=True.
    if "required" not in out and len(out) > 0:
        out["required"] = True
    if out.get("required") is False:
        # "None required" is asserted alone; stray zeros are not requirements.
        return {"required": False}
    return out


# --- us_city_state ---------------------------------------------------------

_CITY_STATE = re.compile(r"([A-Za-z][A-Za-z .'\-]*?),\s*([A-Za-z]{2})(?![A-Za-z])")


def norm_location(v):
    """Reduce a location to 'city, st'.

    A target that answers "Cascade Ridge Middle School, Arvada, CO" has found
    the right place and named the building too. Under bare string equality that
    scored wrong, which overstates error: city+state is the unit the radius
    check actually keys on (the profile's distance table is keyed exactly this
    way). So the scored unit is city+state, and extra site detail neither helps
    nor hurts. Applied identically to every target.

    Rule clarified after a single-case smoke run and before any full run was
    recorded; see CHANGELOG.md.
    """
    if v is None:
        return None
    if not isinstance(v, str):
        v = str(v)
    matches = _CITY_STATE.findall(_ws(v))
    if matches:
        city, state = matches[-1]  # trailing "City, ST" wins over any prefix
        return "%s, %s" % (_ws(city).casefold(), state.casefold())
    return norm_string(v)


NORMALIZERS = {
    "normalized_string": norm_string,
    "iso_date": norm_date,
    "currency_interval": norm_money,
    "token_set": norm_trades,
    "bond_dict": norm_bond,
    "us_city_state": norm_location,
}

FIELD_RULES = {
    "client_name": "normalized_string",
    "project_title": "normalized_string",
    "trade_scope": "token_set",
    "location": "us_city_state",
    "bid_due_date": "iso_date",
    "estimated_project_value": "currency_interval",
    "bond_insurance": "bond_dict",
    "walkthrough_date": "iso_date",
}

REQUIRED_FIELDS = list(FIELD_RULES)


def normalize_field(field: str, value):
    return NORMALIZERS[FIELD_RULES[field]](value)
