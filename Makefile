.PHONY: lint format fix test check

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .

fix:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest

check: lint test
