"""Frozen model and routing configuration.

Single source of truth. The baseline and every solution lever import from here
so they cannot drift apart -- a measured delta has to come from the lever, not
from a quietly different model or provider.

Why a single pinned provider instead of Auto Exacto
---------------------------------------------------
The original plan was to pin routing to Exacto. That is not possible, and
verifying it changed the design:

* Auto Exacto is not a mode you select. Per OpenRouter's documentation it
  "runs by default on every tool-calling request, requiring no configuration".
  It is opt-out (via `sort: "price"` or the `:floor` variant), not opt-in.
  There is no value to pin or record.
* It applies ONLY to requests that include tools. The baseline is specified as
  a single toolless call, so Auto Exacto would never apply to it.

Measured live, three runs per config, on z-ai/glm-5.3-flash:

    no tools, unpinned      -> Z.AI       3/3   $0.075/$0.25   no structured_outputs
    tools, unpinned         -> Together   3/3   $0.15 /$0.50   structured_outputs
    only=[deepinfra]        -> DeepInfra  3/3   $0.075/$0.25   structured_outputs

So leaving Exacto on would have run the baseline on Z.AI and the solution on
Together: different provider, different price, different structured-output
support. Every lever delta would have confounded the lever with a provider
change. Auto Exacto also reorders on rolling 32-day live signals, so it is not
stable across days either.

Pinning one provider makes runs comparable and reproducible. DeepInfra is the
cheapest endpoint that supports structured outputs -- half the price of the one
Exacto selected.
"""
from __future__ import annotations

# --- Model -----------------------------------------------------------------
MODEL = "z-ai/glm-5.3-flash"

# Fallback if structured output proves unreliable. Switching models is a
# deliberate, logged decision -- never automatic -- and must be recorded in
# CHANGELOG.md when it happens.
FALLBACK_MODEL = "z-ai/glm-5.2"

# --- Routing ---------------------------------------------------------------
ROUTING_MODE = "pinned_single_provider"
PINNED_PROVIDER = "deepinfra"

PROVIDER_ROUTING = {
    "only": [PINNED_PROVIDER],
    "allow_fallbacks": False,
    "require_parameters": True,
}

# Auto Exacto is inapplicable under this configuration: provider ordering is
# fixed to a single endpoint, so there is nothing for it to reorder. Recorded
# in every results file rather than left implicit.
AUTO_EXACTO = "not_applicable_provider_pinned"

# --- Sampling --------------------------------------------------------------
TEMPERATURE = 0.0
MAX_TOKENS = 4096

# --- Retry -----------------------------------------------------------------
# allow_fallbacks is False, so an upstream 429 is a hard failure rather than
# something OpenRouter silently reroutes around. Observed empirically: the
# shared upstream pool returned 429 twice before succeeding on a trivial call,
# so retries are mandatory, bounded, and counted.
MAX_ATTEMPTS = 6
BACKOFF_BASE_SECONDS = 2.0
BACKOFF_MAX_SECONDS = 30.0
RETRY_STATUS = (408, 429, 500, 502, 503, 504)

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY_ENV = "OPENROUTER_API_KEY"


def run_config(model: str | None = None) -> dict:
    """The exact configuration stamped into every results file."""
    return {
        "model": model or MODEL,
        "routing_mode": ROUTING_MODE,
        "pinned_provider": PINNED_PROVIDER,
        "provider_routing": dict(PROVIDER_ROUTING),
        "auto_exacto": AUTO_EXACTO,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "max_attempts": MAX_ATTEMPTS,
        "api_base": API_URL,
    }
