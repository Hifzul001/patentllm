.PHONY: install test lint api demo clean

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src tests

api:
	uvicorn patentllm.api:app --reload

demo:
	patentllm demo

clean:
	rm -rf .pytest_cache .ruff_cache .patentllm reports patentllm.db
