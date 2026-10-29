test:
	uv run pytest -q

lint:
	uv run ruff check . && uv run ruff format --check .

typecheck:
	uv run mypy

.PHONY: test lint typecheck run

run:
	uv run uvicorn reorder.api.main:app --reload
