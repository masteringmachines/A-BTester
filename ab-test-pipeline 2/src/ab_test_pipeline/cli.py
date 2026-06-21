"""Command-line entry point.

Usage:
    ab-test --examples data/examples.jsonl \
             --variant-a data/variant_a_outputs.jsonl \
             --variant-b data/variant_b_outputs.jsonl \
             --metric token_overlap \
             --output-dir results

Variants are supplied as JSONL lookup files of `{"input": ..., "output": ...}`
(see `lookup_variant.py`) so the CLI runs end-to-end with zero API keys. To
wire up a real LLM call, use the Python API directly: `ABTestPipeline.add_variant`
accepts any `Callable[[str], str]`.
"""
import argparse
import sys
from pathlib import Path

from .dataset import load_examples
from .lookup_variant import load_lookup_variant
from .metrics import REGISTRY
from .pipeline import ABTestPipeline
from .report import render_text, write_csv, write_html, write_json


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Paired A/B comparison of two variants with statistical tests."
    )
    p.add_argument("--examples", required=True, help="examples.jsonl path (FR1)")
    p.add_argument("--variant-a", required=True, help="JSONL lookup file for variant A outputs")
    p.add_argument("--variant-b", required=True, help="JSONL lookup file for variant B outputs")
    p.add_argument("--metric", default="token_overlap", choices=list(REGISTRY))
    p.add_argument("--cache-path", default="ab_cache.db")
    p.add_argument("--output-dir", default="results")
    p.add_argument("--n-iter", type=int, default=10_000, help="bootstrap resamples")
    p.add_argument("--seed", type=int, default=42)
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)

    examples = load_examples(args.examples)
    variant_a_fn = load_lookup_variant(args.variant_a)
    variant_b_fn = load_lookup_variant(args.variant_b)

    pipeline = ABTestPipeline(cache_path=args.cache_path)
    pipeline.add_variant("a", variant_a_fn)
    pipeline.add_variant("b", variant_b_fn)
    pipeline.set_metric(REGISTRY[args.metric])

    try:
        result, rows = pipeline.run(examples, n_iter=args.n_iter, seed=args.seed)
    except KeyError as e:
        sys.exit(f"Error: {e}")
    finally:
        pipeline.close()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(result, args.metric, out_dir / "summary.json")
    write_csv(rows, out_dir / "per_example.csv")
    write_html(result, rows, args.metric, out_dir / "report.html")

    print(render_text(result, args.metric))
    print(f"\nWrote report to {out_dir / 'report.html'}")


if __name__ == "__main__":
    main()
