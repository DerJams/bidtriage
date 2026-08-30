"""OpenRouter client: bounded retry, explicit failures, full call accounting.

With `allow_fallbacks: False` an upstream 429 is a hard failure -- OpenRouter
will not silently reroute to another provider. That is the point of pinning,
but it means rate limits must be handled loudly rather than swallowed. Every
call records its attempt count, every retry records why, and a call that
exhausts its attempts is recorded as a failure rather than being retried
forever or returning something empty that scores as an abstention.

Cost is the actual amount charged, taken from `usage.cost` on the response
(requested via `usage: {include: true}`). It is never computed from a price
table, so it cannot drift from what the account was really billed.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from evals import config


class MissingAPIKey(RuntimeError):
    pass


@dataclass
class CallResult:
    """Everything one API call produced, including how it went wrong."""
    ok: bool
    content: str | None = None
    tool_calls: list = field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    finish_reason: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: float = 0.0
    attempts: int = 0
    retries: int = 0
    retry_log: list = field(default_factory=list)
    latency_s: float = 0.0
    error: str | None = None

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "provider": self.provider,
            "model": self.model,
            "finish_reason": self.finish_reason,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "cost_usd": self.cost_usd,
            "attempts": self.attempts,
            "retries": self.retries,
            "retry_log": self.retry_log,
            "latency_s": round(self.latency_s, 3),
            "error": self.error,
        }


def require_api_key() -> None:
    """Fail before spending time or writing a results file.

    Without this, a run with no key still completed, scored every field as
    missed, exited 0, and wrote a results file that looked like a legitimate
    0% measurement. Found by a clean-room walkthrough of REPRODUCE.md.
    """
    _api_key()


def _api_key() -> str:
    key = os.environ.get(config.API_KEY_ENV)
    if not key:
        raise MissingAPIKey(
            "%s is not set. Export it before running any target." % config.API_KEY_ENV)
    return key


def call(messages: list,
         model: str | None = None,
         tools: list | None = None,
         tool_choice: Any = None,
         response_format: dict | None = None,
         max_tokens: int | None = None) -> CallResult:
    """One chat completion against the pinned provider, with bounded retry."""
    body: dict = {
        "model": model or config.MODEL,
        "messages": messages,
        "temperature": config.TEMPERATURE,
        "max_tokens": max_tokens or config.MAX_TOKENS,
        "provider": dict(config.PROVIDER_ROUTING),
        "usage": {"include": True},
    }
    if tools:
        body["tools"] = tools
    if tool_choice is not None:
        body["tool_choice"] = tool_choice
    if response_format is not None:
        body["response_format"] = response_format

    payload = json.dumps(body).encode()
    headers = {"Authorization": "Bearer " + _api_key(),
               "Content-Type": "application/json"}

    res = CallResult(ok=False)
    started = time.time()

    for attempt in range(1, config.MAX_ATTEMPTS + 1):
        res.attempts = attempt
        req = urllib.request.Request(config.API_URL, method="POST",
                                     data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            detail = e.read()[:400].decode("utf-8", "replace")
            if e.code in config.RETRY_STATUS and attempt < config.MAX_ATTEMPTS:
                delay = min(config.BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)),
                            config.BACKOFF_MAX_SECONDS)
                res.retries += 1
                res.retry_log.append({"attempt": attempt, "status": e.code,
                                      "sleep_s": delay, "detail": detail[:200]})
                time.sleep(delay)
                continue
            res.error = "HTTP %d: %s" % (e.code, detail)
            res.latency_s = time.time() - started
            return res
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt < config.MAX_ATTEMPTS:
                delay = min(config.BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)),
                            config.BACKOFF_MAX_SECONDS)
                res.retries += 1
                res.retry_log.append({"attempt": attempt, "status": "transport",
                                      "sleep_s": delay, "detail": repr(e)[:200]})
                time.sleep(delay)
                continue
            res.error = "transport: %r" % (e,)
            res.latency_s = time.time() - started
            return res

        # An error can also arrive inside a 200 body.
        if "error" in data and not data.get("choices"):
            res.error = "body error: %s" % json.dumps(data["error"])[:300]
            res.latency_s = time.time() - started
            return res

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        usage = data.get("usage") or {}

        res.ok = True
        res.content = msg.get("content")
        res.tool_calls = msg.get("tool_calls") or []
        res.provider = data.get("provider")
        res.model = data.get("model")
        res.finish_reason = choice.get("finish_reason")
        res.prompt_tokens = usage.get("prompt_tokens") or 0
        res.completion_tokens = usage.get("completion_tokens") or 0
        res.reasoning_tokens = ((usage.get("completion_tokens_details") or {})
                                .get("reasoning_tokens") or 0)
        res.cost_usd = float(usage.get("cost") or 0.0)
        res.latency_s = time.time() - started

        # Pinning is a claim about what ran. Verify it rather than trust it.
        if res.provider and res.provider.lower().replace(" ", "") \
                not in (config.PINNED_PROVIDER, config.PINNED_PROVIDER.replace("_", "")):
            res.retry_log.append({"attempt": attempt, "status": "provider_mismatch",
                                  "detail": "expected %s, got %s"
                                            % (config.PINNED_PROVIDER, res.provider)})
        return res

    res.error = "exhausted %d attempts" % config.MAX_ATTEMPTS
    res.latency_s = time.time() - started
    return res
