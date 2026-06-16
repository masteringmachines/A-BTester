import pytest

from ab_test_pipeline.metrics import exact_match, length_ratio, token_overlap


def test_exact_match():
    assert exact_match("hello", "hello") == 1.0
    assert exact_match("hello", "world") == 0.0
    assert exact_match(" hello ", "hello") == 1.0  # whitespace trimmed


def test_token_overlap():
    assert token_overlap("the cat sat", "the cat sat") == 1.0
    assert token_overlap("the cat sat", "a dog ran") == 0.0
    assert token_overlap("", "") == 1.0
    assert token_overlap("hello", "") == 0.0
    score = token_overlap("the cat sat on mat", "the cat ran")
    assert 0.0 < score < 1.0


def test_length_ratio():
    assert length_ratio("abc", "abc") == 1.0
    assert length_ratio("ab", "abcd") == pytest.approx(0.5)
    assert length_ratio("", "") == 1.0
    assert length_ratio("", "abc") == 0.0
