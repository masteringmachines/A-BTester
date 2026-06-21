"""Metric functions (FR3/NFR4): score one (expected, actual) pair as a float.

A metric is any `Callable[[str, str], float]`. The statistical engine never
inspects *how* a metric computes its score — it only consumes the float — so
adding a new metric never touches `stats.py` or `pipeline.py` (NFR4).
"""
import re
from typing import Callable

Metric = Callable[[str, str], float]


def exact_match(expected: str, actual: str) -> float:
    """1.0 if outputs match exactly after trimming whitespace, else 0.0."""
    return 1.0 if expected.strip() == actual.strip() else 0.0


def token_overlap(expected: str, actual: str) -> float:
    """Jaccard overlap of lowercased word sets — a cheap proxy for relevance
    when you don't want to call an embedding model just to score outputs."""
    exp_tokens = set(re.findall(r"\w+", expected.lower()))
    act_tokens = set(re.findall(r"\w+", actual.lower()))
    if not exp_tokens and not act_tokens:
        return 1.0
    if not exp_tokens or not act_tokens:
        return 0.0
    return len(exp_tokens & act_tokens) / len(exp_tokens | act_tokens)


def length_ratio(expected: str, actual: str) -> float:
    """min(len)/max(len) — a trivial sanity metric, useful mainly for tests."""
    a, b = len(expected.strip()), len(actual.strip())
    if a == 0 and b == 0:
        return 1.0
    if a == 0 or b == 0:
        return 0.0
    return min(a, b) / max(a, b)


REGISTRY: dict[str, Metric] = {
    "exact_match": exact_match,
    "token_overlap": token_overlap,
    "length_ratio": length_ratio,
}
