install:
	poetry install

lint:
	poetry run ruff src
	poetry run mypy src

test:
	poetry run pytest tests

check: lint test

clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache

.PHONY: check install lint test
