from ab_test_pipeline.cache import Cache
from ab_test_pipeline.variant_runner import run_variant


def test_run_variant_calls_function_on_miss(tmp_path):
    cache = Cache(str(tmp_path / "test.db"))
    calls = []

    def fn(text):
        calls.append(text)
        return text.upper()

    result = run_variant("a", fn, "hello", cache)
    assert result == "HELLO"
    assert calls == ["hello"]
    cache.close()


def test_run_variant_uses_cache_on_hit(tmp_path):
    cache = Cache(str(tmp_path / "test.db"))
    calls = []

    def fn(text):
        calls.append(text)
        return text.upper()

    run_variant("a", fn, "hello", cache)
    run_variant("a", fn, "hello", cache)  # second call should hit cache
    assert calls == ["hello"]  # fn only invoked once
    cache.close()
