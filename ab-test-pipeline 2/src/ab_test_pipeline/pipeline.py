"""ABTestPipeline (FR4): runs both variants on every example, paired by id.

This is intentionally a thin orchestrator — it owns no statistics or caching
logic itself, it just wires `variant_runner`, `metrics`, and `stats` together
in the order the PRD's Data Flow section specifies.
"""
from typing import Dict, List, Optional

from .cache import Cache
from .dataset import Example
from .metrics import Metric
from .stats import StatResult, compare
from .variant_runner import Variant, run_variant


class ABTestPipeline:
    def __init__(self, cache_path: str = "ab_cache.db"):
        self.cache = Cache(cache_path)
        self.variants: Dict[str, Variant] = {}
        self.metric_fn: Optional[Metric] = None

    def add_variant(self, name: str, variant_fn: Variant) -> None:
        self.variants[name] = variant_fn

    def set_metric(self, metric_fn: Metric) -> None:
        self.metric_fn = metric_fn

    def run(
        self,
        examples: List[Example],
        variant_a: str = "a",
        variant_b: str = "b",
        n_iter: int = 10_000,
        seed: int = 42,
    ) -> tuple[StatResult, List[Dict]]:
        """Run both variants on every example, score them, compare.

        Returns (StatResult, per_example_rows) — rows are ready for
        `report.write_csv`.
        """
        if self.metric_fn is None:
            raise RuntimeError("call set_metric() before run()")
        for name in (variant_a, variant_b):
            if name not in self.variants:
                raise RuntimeError(f"unknown variant {name!r}; call add_variant() first")

        rows: List[Dict] = []
        scores_a: List[float] = []
        scores_b: List[float] = []

        for ex in examples:
            expected = ex.get("expected_output", "")
            out_a = run_variant(variant_a, self.variants[variant_a], ex["input"], self.cache)
            out_b = run_variant(variant_b, self.variants[variant_b], ex["input"], self.cache)

            score_a = self.metric_fn(expected, out_a)
            score_b = self.metric_fn(expected, out_b)

            scores_a.append(score_a)
            scores_b.append(score_b)
            rows.append(
                {
                    "id": ex["id"],
                    f"score_{variant_a}": score_a,
                    f"score_{variant_b}": score_b,
                    "diff": score_b - score_a,
                }
            )

        result = compare(scores_a, scores_b, n_iter=n_iter, seed=seed)
        return result, rows

    def close(self) -> None:
        self.cache.close()
