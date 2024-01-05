install:
	poetry install

lint:
	poetry run ruff src

.PHONY: install
