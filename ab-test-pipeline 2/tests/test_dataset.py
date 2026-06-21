import pytest

from ab_test_pipeline.dataset import load_examples


def test_load_examples(tmp_path):
    f = tmp_path / "examples.jsonl"
    f.write_text(
        '{"id": "ex1", "input": "q1", "expected_output": "a1"}\n'
        '{"id": "ex2", "input": "q2"}\n',
        encoding="utf-8",
    )
    examples = load_examples(str(f))
    assert len(examples) == 2
    assert examples[0]["id"] == "ex1"
    assert examples[1].get("expected_output") is None


def test_load_examples_requires_id_and_input(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text('{"input": "q1"}\n', encoding="utf-8")
    with pytest.raises(ValueError):
        load_examples(str(f))


def test_load_examples_skips_blank_lines(tmp_path):
    f = tmp_path / "examples.jsonl"
    f.write_text('{"id": "ex1", "input": "q1"}\n\n\n', encoding="utf-8")
    assert len(load_examples(str(f))) == 1
