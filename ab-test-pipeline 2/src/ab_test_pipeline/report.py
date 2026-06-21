"""Report Builder (FR7): console text, JSON summary, optional per-example CSV + HTML."""
import csv
import json
from dataclasses import asdict
from typing import Dict, List

from .stats import StatResult


def write_html(result: StatResult, rows: List[Dict], metric_name: str, path) -> None:
    """Single-file HTML report. No external deps — pure HTML/CSS/vanilla JS."""
    winner = "B" if result.mean_diff > 0 else "A"
    pct = (result.mean_diff / result.mean_a * 100) if result.mean_a else 0.0
    p_val = result.wilcoxon_p if result.ttest_p is None else min(result.ttest_p, result.wilcoxon_p)
    verdict_color = "#16a34a" if result.mean_diff > 0 else "#dc2626"
    ci_low  = f"{result.bootstrap_ci_low:+.4f}"
    ci_high = f"{result.bootstrap_ci_high:+.4f}"
    ttest_str = f"{result.ttest_p:.4f}" if result.ttest_p is not None else "n/a (n &lt; 30)"

    stat_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in [
        ("Metric",            metric_name),
        ("Examples (n)",      result.n),
        ("Mean A",            f"{result.mean_a:.4f}"),
        ("Mean B",            f"{result.mean_b:.4f}"),
        ("Mean diff (B-A)",   f"{result.mean_diff:+.4f}"),
        ("Cohen's d",         f"{result.cohens_d:.3f}"),
        ("95% Bootstrap CI",  f"[{ci_low}, {ci_high}]"),
        ("Paired t-test p",   ttest_str),
        ("Wilcoxon p",        f"{result.wilcoxon_p:.4f}"),
    ])

    score_a_key = next((k for k in rows[0] if k.startswith("score_a")), "score_a")
    score_b_key = next((k for k in rows[0] if k.startswith("score_b")), "score_b")
    example_rows = "".join(
        f"<tr>"
        f"<td>{r['id']}</td>"
        f"<td>{r[score_a_key]:.4f}</td>"
        f"<td>{r[score_b_key]:.4f}</td>"
        f"<td style='color:{'#16a34a' if r['diff']>0 else '#dc2626' if r['diff']<0 else '#6b7280'}'>"
        f"{r['diff']:+.4f}</td>"
        f"</tr>"
        for r in rows
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>A/B Test Report</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,sans-serif;background:#f8fafc;color:#1e293b;padding:2rem}}
  h1{{font-size:1.5rem;font-weight:700;margin-bottom:.25rem}}
  .sub{{color:#64748b;font-size:.9rem;margin-bottom:2rem}}
  .verdict{{background:#fff;border-radius:12px;padding:1.5rem 2rem;margin-bottom:1.5rem;
            border-left:5px solid {verdict_color};box-shadow:0 1px 4px #0001}}
  .verdict .label{{font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b}}
  .verdict .value{{font-size:2rem;font-weight:800;color:{verdict_color};margin:.25rem 0}}
  .verdict .detail{{font-size:.95rem;color:#475569}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem}}
  @media(max-width:600px){{.grid{{grid-template-columns:1fr}}}}
  .card{{background:#fff;border-radius:12px;padding:1.25rem 1.5rem;box-shadow:0 1px 4px #0001}}
  .card h2{{font-size:1rem;font-weight:600;margin-bottom:.75rem;color:#334155}}
  table{{width:100%;border-collapse:collapse;font-size:.9rem}}
  th{{text-align:left;padding:.5rem .75rem;background:#f1f5f9;font-weight:600;
      font-size:.8rem;text-transform:uppercase;letter-spacing:.04em;color:#64748b}}
  td{{padding:.5rem .75rem;border-top:1px solid #e2e8f0}}
  td:first-child{{color:#64748b;white-space:nowrap}}
  td:last-child{{font-weight:500}}
  tr:hover td{{background:#f8fafc}}
  .score-table td:first-child{{font-weight:500;color:#1e293b}}
  .bar-wrap{{background:#e2e8f0;border-radius:999px;height:6px;margin-top:.35rem}}
  .bar{{height:6px;border-radius:999px}}
  .bars{{display:flex;flex-direction:column;gap:.75rem}}
  .bar-row label{{font-size:.85rem;color:#64748b;display:flex;
                  justify-content:space-between;margin-bottom:.1rem}}
</style>
</head>
<body>
<h1>A/B Test Report</h1>
<p class="sub">Metric: <strong>{metric_name}</strong> &nbsp;&middot;&nbsp; {result.n} examples</p>

<div class="verdict">
  <div class="label">Verdict</div>
  <div class="value">Variant {winner} wins</div>
  <div class="detail">p = {p_val:.3f} &nbsp;&middot;&nbsp; {pct:+.1f}% relative change
  &nbsp;&middot;&nbsp; Cohen&#39;s d = {result.cohens_d:.2f}</div>
</div>

<div class="grid">
  <div class="card">
    <h2>Score comparison</h2>
    <div class="bars">
      <div class="bar-row">
        <label><span>Variant A</span><span>{result.mean_a:.4f}</span></label>
        <div class="bar-wrap">
          <div class="bar" style="width:{min(result.mean_a*100,100):.1f}%;background:#94a3b8"></div>
        </div>
      </div>
      <div class="bar-row">
        <label><span>Variant B</span><span>{result.mean_b:.4f}</span></label>
        <div class="bar-wrap">
          <div class="bar" style="width:{min(result.mean_b*100,100):.1f}%;background:{verdict_color}"></div>
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Statistics</h2>
    <table><tbody>{stat_rows}</tbody></table>
  </div>
</div>

<div class="card">
  <h2>Per-example scores</h2>
  <table>
    <thead><tr><th>ID</th><th>Score A</th><th>Score B</th><th>Diff (B-A)</th></tr></thead>
    <tbody class="score-table">{example_rows}</tbody>
  </table>
</div>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


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
