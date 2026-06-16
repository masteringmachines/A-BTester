.PHONY: install test run-demo

install:
	pip install -e ".[dev]"

test:
	pytest -q

run-demo:
	ab-test \
		--examples data/examples.jsonl \
		--variant-a data/variant_a_outputs.jsonl \
		--variant-b data/variant_b_outputs.jsonl \
		--metric token_overlap \
		--output-dir results
