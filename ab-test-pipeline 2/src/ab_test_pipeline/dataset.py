"""Input loader (FR1): JSONL with `id`, `input`, optional `expected_output`."""
import json
from typing import List, TypedDict


class Example(TypedDict, total=False):
    id: str
    input: str
    expected_output: str


def load_examples(path: str) -> List[Example]:
    examples: List[Example] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if "id" not in obj or "input" not in obj:
                raise ValueError(f"Each line needs 'id' and 'input': {obj}")
            examples.append(obj)
    return examples
