.PHONY: format lint test install install-dev install-hooks check

VENV_BIN ?= .venv/bin
BLACK = $(VENV_BIN)/black
ISORT = $(VENV_BIN)/isort
FLAKE8 = $(VENV_BIN)/flake8
MYPY = $(VENV_BIN)/mypy
PYTEST = $(VENV_BIN)/pytest
PIP = $(VENV_BIN)/pip

format:
	$(BLACK) src/ tests/
	$(ISORT) src/ tests/

lint:
	$(BLACK) --check src/ tests/
	$(ISORT) --check-only --diff src/ tests/
	$(FLAKE8) src/ tests/
	$(MYPY) src/

test:
	$(PYTEST) -v --cov=src/koubou

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

install-hooks:
	git config core.hooksPath .githooks

check: format lint test
