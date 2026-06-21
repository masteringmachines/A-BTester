"""Statistical Engine (FR6/NFR2): paired comparison of two score arrays.

All inputs are paired by input id — `scores_a[i]` and `scores_b[i]` must be
the same example. Everything here is pure functions over numpy arrays, so it
has zero dependency on how the scores were produced (LLM call, cache hit,
whatever) — keeps the stats logic testable without any caching/IO involved.
"""
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
from scipy import stats


@dataclass
class StatResult:
    n: int
    mean_a: float
    mean_b: float
    mean_diff: float  # mean(B) - mean(A); positive means B scored higher
    cohens_d: float
    bootstrap_ci_low: float
    bootstrap_ci_high: float
    ttest_p: Optional[float]  # None when n < 30 (NFR2)
    wilcoxon_p: float

    def summary_line(self) -> str:
        """One-line summary per the PRD's user story #2."""
        pct = (self.mean_diff / self.mean_a * 100) if self.mean_a else float("nan")
        better = "B" if self.mean_diff > 0 else "A"
        p = self.wilcoxon_p if self.ttest_p is None else min(self.ttest_p, self.wilcoxon_p)
        return f"{better} is better (p={p:.3f}, {pct:+.1f}% relative change)"


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Effect size for paired data: mean difference / std of the differences."""
    diff = b - a
    sd = diff.std(ddof=1)
    return float(diff.mean() / sd) if sd > 0 else 0.0


def bootstrap_ci(
    a: np.ndarray, b: np.ndarray, n_iter: int = 10_000, seed: int = 42
) -> tuple[float, float]:
    """95% CI for mean(B) - mean(A) via paired bootstrap resampling (FR6)."""
    rng = np.random.default_rng(seed)  # NFR4-style reproducibility
    diff = b - a
    n = len(diff)
    resampled_means = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        resampled_means[i] = diff[idx].mean()
    low, high = np.percentile(resampled_means, [2.5, 97.5])
    return float(low), float(high)


def compare(
    scores_a: Sequence[float], scores_b: Sequence[float], n_iter: int = 10_000, seed: int = 42
) -> StatResult:
    """Run the full paired comparison described in FR6.

    NFR2: t-test is only reported when n >= 30 (the usual rule-of-thumb
    threshold for the CLT to make a t-test trustworthy); Wilcoxon is always
    reported since it makes no normality assumption.
    """
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    if len(a) != len(b):
        raise ValueError("scores_a and scores_b must be the same length (paired design)")
    n = len(a)

    ttest_p = None
    if n >= 30:
        _, ttest_p = stats.ttest_rel(a, b)
        ttest_p = float(ttest_p)

    diff = b - a
    if np.all(diff == 0):
        wilcoxon_p = 1.0
    else:
        _, wilcoxon_p = stats.wilcoxon(a, b)
        wilcoxon_p = float(wilcoxon_p)

    ci_low, ci_high = bootstrap_ci(a, b, n_iter=n_iter, seed=seed)

    return StatResult(
        n=n,
        mean_a=float(a.mean()),
        mean_b=float(b.mean()),
        mean_diff=float(b.mean() - a.mean()),
        cohens_d=cohens_d(a, b),
        bootstrap_ci_low=ci_low,
        bootstrap_ci_high=ci_high,
        ttest_p=ttest_p,
        wilcoxon_p=wilcoxon_p,
    )
