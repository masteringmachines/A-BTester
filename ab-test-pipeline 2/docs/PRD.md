# PRD #18 – A/B Test Evaluation Pipeline (Statistical Significance)

## 1. Objective
Provide a pipeline to compare **two LLM‑powered variants** (prompts, models, or decoding parameters) on a set of test examples, using a **paired evaluation design** and rigorous statistical tests (t‑test, Wilcoxon, bootstrap confidence intervals). The pipeline must be **cache‑aware** to avoid redundant LLM API calls.

## 2. Scope
**In scope**
- Compare Variant A vs Variant B over the same input set.
- Support for arbitrary evaluation metrics (e.g., relevance, accuracy, faithfulness).
- Output statistical significance (p‑value), effect size (Cohen's d), and practical significance (e.g., "Variant B is 5% better on average").
- Cache LLM outputs per variant + input to allow incremental runs.

**Out of scope**
- Multi‑arm A/B/n tests (can be extended).
- Sequential testing / early stopping.
- User interface – command‑line tool only.

## 3. User Stories
1. As a prompt engineer, I want to test if a new system prompt yields significantly higher answer relevance than the old one, using only 50 examples.
2. As a product manager, I want a one‑line summary: "B is better (p=0.03, +2.3% relevance)".
3. As an ML engineer, I want to reuse the same cache when I add more test examples, so I don't re‑run previous LLM calls.

## 4. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | Accept an input file (JSONL) with `id`, `input` (the prompt or user query), and optional `expected_output` for supervised metrics. |
| FR2 | Define two variants as callables: `variant_a(input) -> output` and `variant_b(input) -> output` (can wrap API calls). |
| FR3 | Define a metric function `metric(expected, actual, context) -> float` (e.g., semantic similarity, exact match, custom rubric). |
| FR4 | Run both variants on each input, compute per‑example metric scores for A and B (paired). |
| FR5 | Cache results: store `(variant_name, input_hash, output, latency, timestamp)` in SQLite. Before calling a variant, check cache. |
| FR6 | Compute: Mean(A), Mean(B), mean difference; paired t‑test p‑value and Wilcoxon signed‑rank p‑value; Cohen's d effect size; 95% bootstrap confidence interval for the mean difference (resampling with replacement, 10k iterations). |
| FR7 | Output a text report and optionally a CSV of per‑example scores. |
| FR8 | Gracefully handle missing cache – recompute only missing pairs. |

## 5. Non‑Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR1 | **Token efficiency** – Cache eliminates repeated calls. On a re‑run with 10 new examples, only 20 new LLM calls are made (A+B for each new input). |
| NFR2 | **Statistical robustness** – Automatically choose test based on sample size: if n<30, prefer Wilcoxon; if n>=30, report both t‑test and Wilcoxon. |
| NFR3 | **Performance** – With caching, evaluation of 200 examples (400 LLM calls) should complete in <0.1 second for the metric computation part. |
| NFR4 | **Extensibility** – Adding a new metric should not require changing the core A/B logic. |

## 6. System Design

### Components
- **Cache Layer** – SQLite with table `llm_cache(variant TEXT, input_hash TEXT, output TEXT, latency REAL, created_at DATETIME)`. Input hash = SHA256 of `variant_name + input`.
- **Variant Runner** – Takes a variant function, input, checks cache, else calls function and stores result.
- **Metric Evaluator** – Applies the metric function to (expected, actual, input) for each variant.
- **Statistical Engine** – Uses `scipy.stats` and `numpy`.
- **Report Builder** – Formats results as console output + JSON.

### Data Flow
1. Load inputs → list of dicts `[{id, input, expected_output}]`.
2. For each variant (A and B): for each input, check cache → if miss, call variant function, store output + latency.
3. Build two arrays `scores_A` and `scores_B` (paired by input id).
4. Run statistical tests.
5. Print report.

### Class Sketch
```python
class ABTestPipeline:
    def __init__(self, cache_path="ab_cache.db"):
        self.cache = sqlite3.connect(cache_path)
        self._init_db()

    def add_variant(self, name: str, variant_fn: Callable):
        self.variants[name] = variant_fn

    def set_metric(self, metric_fn: Callable):
        self.metric_fn = metric_fn

    def run(self, inputs: List[Dict]) -> Dict:
        # returns statistical summary
        pass

    def _get_or_compute_output(self, variant_name, input_text):
        # cache logic
        pass
```
