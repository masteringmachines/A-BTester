import numpy as np
import pytest

from ab_test_pipeline.stats import bootstrap_ci, cohens_d, compare


def test_compare_identical_arrays_gives_zero_diff():
    a = [0.5, 0.6, 0.7, 0.8]
    b = [0.5, 0.6, 0.7, 0.8]
    result = compare(a, b)
    assert result.mean_diff == pytest.approx(0.0)
    assert result.wilcoxon_p == 1.0


def test_compare_b_clearly_better():
    a = [0.1, 0.2, 0.15, 0.1, 0.2, 0.18, 0.12, 0.19]
    b = [0.9, 0.85, 0.95, 0.88, 0.92, 0.91, 0.87, 0.93]
    result = compare(a, b)
    assert result.mean_diff > 0
    assert result.cohens_d > 0
    assert "B is better" in result.summary_line()


def test_compare_requires_equal_length():
    with pytest.raises(ValueError):
        compare([0.1, 0.2], [0.1])


def test_ttest_only_reported_when_n_at_least_30():
    small_a = [0.5] * 10
    small_b = [0.6] * 10
    result_small = compare(small_a, small_b)
    assert result_small.ttest_p is None

    big_a = list(np.linspace(0.4, 0.6, 30))
    big_b = list(np.linspace(0.5, 0.7, 30))
    result_big = compare(big_a, big_b)
    assert result_big.ttest_p is not None


def test_cohens_d_zero_for_no_variance_no_diff():
    a = np.array([0.5, 0.5, 0.5])
    b = np.array([0.5, 0.5, 0.5])
    assert cohens_d(a, b) == 0.0


def test_bootstrap_ci_contains_true_mean_diff_roughly():
    rng = np.random.default_rng(0)
    a = rng.normal(0.5, 0.05, size=200)
    noise = rng.normal(0.0, 0.02, size=200)
    b = a + 0.1 + noise  # true mean diff is 0.1, with per-example noise
    low, high = bootstrap_ci(a, b, n_iter=2000, seed=1)
    assert low <= 0.1 <= high
