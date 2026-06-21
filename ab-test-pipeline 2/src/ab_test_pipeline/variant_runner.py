"""Variant Runner (FR2/FR5): cache-checked execution of a variant callable.

A "variant" is just any `Callable[[str], str]` — wrap an API call, a local
model, a fixed lookup table, whatever. `run_variant` is the only place that
decides cache-hit vs cache-miss, so this is the single chokepoint that makes
NFR1 (no redundant LLM calls) true.
"""
import time
from typing import Callable

from .cache import Cache

Variant = Callable[[str], str]


def run_variant(name: str, fn: Variant, input_text: str, cache: Cache) -> str:
    """Return the variant's output for `input_text`, using the cache first."""
    cached = cache.get(name, input_text)
    if cached is not None:
        return cached

    t0 = time.perf_counter()
    output = fn(input_text)
    latency = time.perf_counter() - t0

    cache.put(name, input_text, output, latency)
    return output
