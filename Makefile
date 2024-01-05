install:
	poetry install

lint:
	poetry run ruff src
	poetry run mypy src

.PHONY: install lint
