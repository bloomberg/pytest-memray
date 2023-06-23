PYTHON ?= python
PRETTIER ?= prettier --no-editorconfig

# Doc generation variables
UPSTREAM_GIT_REMOTE ?= origin
DOCSBUILDDIR := docs/_build
HTMLDIR := $(DOCSBUILDDIR)/html
PKG_CONFIG_PATH ?= /opt/bb/lib64/pkgconfig
PIP_INSTALL=PKG_CONFIG_PATH="$(PKG_CONFIG_PATH)" $(PYTHON) -m pip install

markdown_files := $(shell find . -name \*.md -not -path '*/\.*')
python_files := $(shell find . -name \*.py -not -path '*/\.*')
PURELIB=$(shell $(PYTHON) -c 'import sysconfig; print(sysconfig.get_path("purelib"))')
# Use this to inject arbitrary commands before the make targets (e.g. docker)
ENV :=

.PHONY: dist
dist:  ## Generate Python distribution files
	$(PYTHON) -m build .

.PHONY: install-sdist
install-sdist: dist  ## Install from source distribution
	$(ENV) $(PIP_INSTALL) $(wildcard dist/*.tar.gz)

.PHONY: test-install
test-install:  ## Install with test dependencies
	$(ENV) $(PIP_INSTALL) -e .[test]

.PHONY: check
check:
	$(PYTHON) -m pytest -vvv --color=yes $(PYTEST_ARGS) tests

.PHONY: coverage
coverage:  ## Run the test suite, with Python code coverage
	$(PYTHON) -m coverage erase
	$(PYTHON) -m coverage run -m pytest tests
	$(PYTHON) -m coverage combine
	$(PYTHON) -m coverage report
	$(PYTHON) -m coverage html -d .pytest_cov/htmlcov

.PHONY: format
format:  ## Autoformat all files
	$(PYTHON) -m ruff --fix $(python_files)
	$(PYTHON) -m black $(python_files)

.PHONY: lint
lint:  ## Lint all files
	$(PYTHON) -m ruff check $(python_files)
	$(PYTHON) -m black --check --diff $(python_files)
	$(PYTHON) -m mypy src/pytest_memray --ignore-missing-imports

.PHONY: docs
docs:  ## Generate documentation
	sphinx-build docs docs/_build/html --color -W --keep-going -n -bhtml -b linkcheck -W

.PHONY: clean
clean:  ## Clean any built/generated artifacts
	find . | grep -E '(\.o|\.so|\.gcda|\.gcno|\.gcov\.json\.gz)' | xargs rm -rf
	find . | grep -E '(__pycache__|\.pyc|\.pyo)' | xargs rm -rf

.PHONY: gen_news
gen_news:
	$(PYEXEC) towncrier build --version $(VERSION) --yes

.PHONY: help
help:  ## Print this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
