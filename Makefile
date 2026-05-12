PYTHON ?= python
PIP ?= pip

.PHONY: build install clean test

build:
	$(PYTHON) -m build

install:
	$(PIP) install -e .

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

test:
	pytest -q
