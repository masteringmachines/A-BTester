# A/B Test Evaluation Pipeline

Paired statistical comparison of two LLM-powered variants (prompts, models,
decoding params) over the same test set — Wilcoxon, paired t-test, Cohen's d,
and a bootstrap confidence interval, with a SQLite cache so repeat runs never
re-pay for the same (variant, input) pair.

## Quickstart

```bash
pip install -e ".[dev]"

ab-test \
  --examples data/examples.jsonl \
  --variant-a data/variant_a_outputs.jsonl \
  --variant-b data/variant_b_outputs.jsonl \
  --metric token_overlap \
  --output-dir results
```

This prints a report like:

```
A/B Test Report  (metric: token_overlap, n=8)
--------------------------------------------------
Mean A:           0.1984
Mean B:           0.9087
Mean diff (B-A):  +0.7104
Cohen's d:        3.855
95% bootstrap CI: [+0.5815, +0.8189]
Paired t-test p:  n/a (n<30, see Wilcoxon)
Wilcoxon p:       0.0078
--------------------------------------------------
B is better (p=0.008, +358.1% relative change)
```

and writes `results/summary.json` + `results/per_example.csv`.

## Project layout

```
ab-test-pipeline/
├── src/ab_test_pipeline/
│   ├── cli.py              # entry point (`ab-test` console script)
│   ├── dataset.py           # load examples.jsonl
│   ├── cache.py              # SQLite cache, keyed by SHA256(variant + input)
│   ├── variant_runner.py     # cache-checked execution of a variant callable
│   ├── metrics.py             # exact_match, token_overlap, length_ratio
│   ├── stats.py                # paired t-test, Wilcoxon, Cohen's d, bootstrap CI
│   ├── pipeline.py             # ABTestPipeline — orchestrates the above
│   ├── lookup_variant.py        # JSONL-lookup variant for CLI/offline use
│   └── report.py                # console text, JSON, CSV output
├── data/                          # sample examples + two variant outputs
├── tests/                          # pytest unit + integration tests
└── docs/PRD.md                     # original product spec
```

## Input formats

**`examples.jsonl`** — one JSON object per line:

```json
{"id": "ex1", "input": "What is the capital of France?", "expected_output": "Paris is the capital of France."}
```

**Variant outputs** (CLI only) — JSONL lookup tables of `{"input": ..., "output": ...}`,
so the CLI runs end-to-end with no API keys. To wire up a real LLM, use the
Python API instead — `ABTestPipeline.add_variant("a", my_api_call_fn)` accepts
any `Callable[[str], str]`.

## Using the Python API directly

```python
from ab_test_pipeline.pipeline import ABTestPipeline
from ab_test_pipeline.metrics import token_overlap
from ab_test_pipeline.dataset import load_examples

pipeline = ABTestPipeline(cache_path="ab_cache.db")
pipeline.add_variant("a", lambda prompt: call_my_old_prompt(prompt))
pipeline.add_variant("b", lambda prompt: call_my_new_prompt(prompt))
pipeline.set_metric(token_overlap)

examples = load_examples("data/examples.jsonl")
result, rows = pipeline.run(examples)
print(result.summary_line())
```

Re-running with extra examples appended to the JSONL only calls the variants
for the *new* rows — everything previously cached is read straight from
SQLite (NFR1).

## Metrics (NFR4: pluggable, no core changes needed)

| Metric          | Definition                                              |
|-----------------|----------------------------------------------------------|
| `exact_match`   | 1.0 if outputs match exactly (after trim), else 0.0      |
| `token_overlap` | Jaccard overlap of lowercased word sets                  |
| `length_ratio`  | min(len)/max(len) — sanity-check metric                  |

Add your own by writing any `Callable[[str, str], float]` and passing it to
`pipeline.set_metric(...)` — the statistical engine never inspects how a
metric computes its score.

## Statistics (FR6/NFR2)

- **Paired t-test** — only reported when n ≥ 30 (the usual CLT threshold);
  shown as `n/a` below that, since a t-test's normality assumption is shaky
  on small samples.
- **Wilcoxon signed-rank** — always reported; makes no distributional
  assumption, so it's the metric to trust for small sample sizes.
- **Cohen's d** — effect size: mean of the paired differences divided by
  their standard deviation.
- **95% bootstrap CI** — 10,000 resamples (configurable via `--n-iter`) of
  the paired differences, seeded for reproducibility.

## Tests

```bash
pip install -e ".[dev]"
pytest -q
```
