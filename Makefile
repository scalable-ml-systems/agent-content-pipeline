PYTHON ?= python
TOPIC ?= KV-aware routing vs round robin in LLM inference

.PHONY: help install install-dev run test clean

help:
	@echo "Available targets:"
	@echo "  install      - install runtime dependencies"
	@echo "  install-dev  - install runtime + dev dependencies"
	@echo "  run          - run the pipeline with TOPIC"
	@echo "  test         - run tests"
	@echo "  clean        - remove Python cache files"

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) -m app.main "$(TOPIC)"

test:
	pytest

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete