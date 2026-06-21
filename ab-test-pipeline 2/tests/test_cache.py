from ab_test_pipeline.cache import Cache, input_hash


def test_cache_miss_then_hit(tmp_path):
    cache = Cache(str(tmp_path / "test.db"))
    assert cache.get("a", "hello") is None

    cache.put("a", "hello", "world", latency=0.01)
    assert cache.get("a", "hello") == "world"
    cache.close()


def test_cache_keys_by_variant_and_text(tmp_path):
    cache = Cache(str(tmp_path / "test.db"))
    cache.put("a", "hello", "from-a", latency=0.0)
    cache.put("b", "hello", "from-b", latency=0.0)
    assert cache.get("a", "hello") == "from-a"
    assert cache.get("b", "hello") == "from-b"
    cache.close()


def test_input_hash_stable_and_distinct():
    h1 = input_hash("a", "hello")
    h2 = input_hash("a", "hello")
    h3 = input_hash("b", "hello")
    assert h1 == h2
    assert h1 != h3


def test_cache_persists_across_reopen(tmp_path):
    db_path = str(tmp_path / "persist.db")
    cache = Cache(db_path)
    cache.put("a", "x", "y", latency=0.0)
    cache.close()

    reopened = Cache(db_path)
    assert reopened.get("a", "x") == "y"
    reopened.close()
