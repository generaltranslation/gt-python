.PHONY: setup lint lint-fix format typecheck test check build clean changeset

setup:
	./scripts/setup.sh

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy .

test:
	uv run pytest

check: lint format-check typecheck test

build:
	@for pkg in packages/*/; do \
		pkg_name=$$(basename "$$pkg"); \
		if grep -q '\[build-system\]' "$$pkg/pyproject.toml" 2>/dev/null; then \
			echo "Building $$pkg_name..."; \
			uv build --package "$$pkg_name" --out-dir dist/; \
		fi; \
	done

changeset:
	sampo add

clean:
	rm -rf dist/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
