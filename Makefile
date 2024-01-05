install:
	poetry install

lint:
	poetry run ruff src
	poetry run mypy src

test:

check: lint test

.PHONY: check install lint
