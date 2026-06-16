from ab_test_pipeline.metrics import exact_match
from ab_test_pipeline.pipeline import ABTestPipeline


def test_pipeline_end_to_end(tmp_path):
    examples = [
        {"id": "ex1", "input": "q1", "expected_output": "answer one"},
        {"id": "ex2", "input": "q2", "expected_output": "answer two"},
        {"id": "ex3", "input": "q3", "expected_output": "answer three"},
    ]

    def variant_a(text):
        return "wrong answer"

    def variant_b(text):
        mapping = {"q1": "answer one", "q2": "answer two", "q3": "answer three"}
        return mapping[text]

    pipeline = ABTestPipeline(cache_path=str(tmp_path / "cache.db"))
    pipeline.add_variant("a", variant_a)
    pipeline.add_variant("b", variant_b)
    pipeline.set_metric(exact_match)

    result, rows = pipeline.run(examples, n_iter=500, seed=1)
    pipeline.close()

    assert result.n == 3
    assert result.mean_a == 0.0
    assert result.mean_b == 1.0
    assert result.mean_diff == 1.0
    assert len(rows) == 3
    assert rows[0]["score_a"] == 0.0
    assert rows[0]["score_b"] == 1.0


def test_pipeline_uses_cache_across_runs(tmp_path):
    examples = [{"id": "ex1", "input": "q1", "expected_output": "x"}]
    calls = []

    def variant_a(text):
        calls.append(text)
        return "x"

    def variant_b(text):
        return "x"

    cache_path = str(tmp_path / "cache.db")

    pipeline1 = ABTestPipeline(cache_path=cache_path)
    pipeline1.add_variant("a", variant_a)
    pipeline1.add_variant("b", variant_b)
    pipeline1.set_metric(lambda e, a: 1.0 if e == a else 0.0)
    pipeline1.run(examples, n_iter=10)
    pipeline1.close()

    # Second pipeline instance, same cache file, same variant fn — should
    # not call variant_a again because the (variant, input) pair is cached.
    pipeline2 = ABTestPipeline(cache_path=cache_path)
    pipeline2.add_variant("a", variant_a)
    pipeline2.add_variant("b", variant_b)
    pipeline2.set_metric(lambda e, a: 1.0 if e == a else 0.0)
    pipeline2.run(examples, n_iter=10)
    pipeline2.close()

    assert calls == ["q1"]  # only called once across both pipeline runs
