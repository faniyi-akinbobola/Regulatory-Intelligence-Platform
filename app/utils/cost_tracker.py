"""
Per-request LLM cost tracking using Python contextvars.

Each async workflow invocation gets its own isolated token counter via a
ContextVar. The compliance service resets and reads the tracker around
each workflow.ainvoke() call — no global state, no thread-safety issues.

Pricing reference (gpt-4o-mini as of 2025):
  Input  : $0.150 / 1M tokens
  Output : $0.600 / 1M tokens
"""

from contextvars import ContextVar
from dataclasses import dataclass, field

# Per-model pricing in USD per 1 token
_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {
        "input":  0.150 / 1_000_000,
        "output": 0.600 / 1_000_000,
    },
    "gpt-4o": {
        "input":  2.50 / 1_000_000,
        "output": 10.00 / 1_000_000,
    },
    "gpt-4-turbo": {
        "input":  10.00 / 1_000_000,
        "output": 30.00 / 1_000_000,
    },
}
_DEFAULT_PRICING = {"input": 0.150 / 1_000_000, "output": 0.600 / 1_000_000}


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    llm_calls: int = 0


# One accumulator per async task (each workflow invocation runs in its own task)
_current_usage: ContextVar[TokenUsage] = ContextVar("_current_usage")


def reset() -> TokenUsage:
    """Create a fresh tracker for this async context and return it."""
    tracker = TokenUsage()
    _current_usage.set(tracker)
    return tracker


def get() -> TokenUsage | None:
    """Return the tracker for the current async context, or None."""
    return _current_usage.get(None)


def record(model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Add a single LLM call's token usage to the current context tracker."""
    tracker = _current_usage.get(None)
    if tracker is None:
        return
    pricing = _PRICING.get(model, _DEFAULT_PRICING)
    call_cost = (prompt_tokens * pricing["input"]) + (completion_tokens * pricing["output"])
    tracker.prompt_tokens += prompt_tokens
    tracker.completion_tokens += completion_tokens
    tracker.total_tokens += prompt_tokens + completion_tokens
    tracker.cost_usd += call_cost
    tracker.llm_calls += 1
