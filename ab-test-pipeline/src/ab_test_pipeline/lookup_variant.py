"""Lookup-table variant (FR2): wraps a JSONL file of {id: output} as a callable.

Real variants wrap an LLM API call; for the CLI demo (and for tests) it's
useful to have a zero-dependency variant that just replays pre-recorded
outputs keyed by example id. This keeps the whole pipeline runnable offline.
"""
import json
from typing import Dict


def load_lookup_variant(path: str):
    """Read a JSONL file of `{"id": ..., "output": ...}` and return a
    `Variant` callable keyed by *input text* lookup is not enough here since
    the pipeline calls variants with `input`, not `id` — so this helper
    expects the JSONL to use `input` as the key instead.
    """
    table: Dict[str, str] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            table[obj["input"]] = obj["output"]

    def variant(input_text: str) -> str:
        if input_text not in table:
            raise KeyError(f"no recorded output for input: {input_text!r}")
        return table[input_text]

    return variant
