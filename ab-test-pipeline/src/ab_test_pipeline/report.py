"""Report Builder (FR7): console text, JSON summary, optional per-example CSV."""
import csv
import json
from dataclasses import asdict
from typing import Dict, List

from .stats import StatResult


def render_text(result: StatResult, metric_name: str) -> str:
    """Human-readable report for the console (FR7)."""
    lines = [
        f"A/B Test Report  (metric: {metric_name}, n={result.n})",
        "-" * 50,
        f"Mean A:           {result.mean_a:.4f}",
        f"Mean B:           {result.mean_b:.4f}",
        f"Mean diff (B-A):  {result.mean_diff:+.4f}",
        f"Cohen's d:        {result.cohens_d:.3f}",
        f"95% bootstrap CI: [{result.bootstrap_ci_low:+.4f}, {result.bootstrap_ci_high:+.4f}]",
    ]
    if result.ttest_p is not None:
        lines.append(f"Paired t-test p:  {result.ttest_p:.4f}")
    else:
        lines.append("Paired t-test p:  n/a (n<30, see Wilcoxon)")
    lines.append(f"Wilcoxon p:       {result.wilcoxon_p:.4f}")
    lines.append("-" * 50)
    lines.append(result.summary_line())
    return "\n".join(lines)


def write_json(result: StatResult, metric_name: str, path: str) -> None:
    payload = {"metric": metric_name, **asdict(result), "summary": result.summary_line()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def write_csv(rows: List[Dict], path: str) -> None:
    """One row per example: id, score_a, score_b, diff (FR7)."""
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
