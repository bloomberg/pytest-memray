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
	$(PYTHON) -m coverage run \
		--source=src/pytest_memray \
		--module pytest tests
	$(PYTHON) -m coverage report --show-missing --fail-under=89

.PHONY: format
format:  ## Autoformat all files
	$(PYTHON) -m isort $(python_files)
	$(PYTHON) -m black $(python_files)

.PHONY: lint
lint:  ## Lint all files
	$(PYTHON) -m isort --check $(python_files)
	$(PYTHON) -m flake8 $(python_files)
	$(PYTHON) -m black --check $(python_files)
	# $(PYTHON) -m mypy src/pytest_memray --ignore-missing-imports
	$(PYTHON) -m check_manifest

.PHONY: docs
docs:  ## Generate documentation
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

.PHONY: docs-live
docs-live:  ## Serve documentation on localhost:8000, with live-reload
	$(MAKE) -C docs clean
	$(MAKE) -C docs livehtml

.PHONY: gh-pages
gh-pages:  ## Publish documentation on BBGitHub Pages
	$(eval GIT_REMOTE := $(shell git remote get-url $(UPSTREAM_GIT_REMOTE)))
	$(eval COMMIT_HASH := $(shell git rev-parse HEAD))
	touch $(HTMLDIR)/.nojekyll
	@echo -n "Documentation ready, push to $(GIT_REMOTE)? [Y/n] " && read ans && [ $${ans:-Y} == Y ]
	git init $(HTMLDIR)
	GIT_DIR=$(HTMLDIR)/.git GIT_WORK_TREE=$(HTMLDIR) git add -A
	GIT_DIR=$(HTMLDIR)/.git git commit -m "Documentation for commit $(COMMIT_HASH)"
	GIT_DIR=$(HTMLDIR)/.git git push $(GIT_REMOTE) HEAD:gh-pages --force
	rm -rf $(HTMLDIR)/.git

.PHONY: clean
clean:  ## Clean any built/generated artifacts
	find . | grep -E '(\.o|\.so|\.gcda|\.gcno|\.gcov\.json\.gz)' | xargs rm -rf
	find . | grep -E '(__pycache__|\.pyc|\.pyo)' | xargs rm -rf

.PHONY: bump_version
bump_version:
	bump2version $(RELEASE)
	$(eval NEW_VERSION := $(shell bump2version \
	                                --allow-dirty \
	                                --dry-run \
	                                --list $(RELEASE) \
	                                | tail -1 \
	                                | sed s,"^.*=",,))
	./tools/bump_changelog.sh $(NEW_VERSION)
	git add debian/changelog
	git commit --amend --no-edit

.PHONY: gen_news
gen_news:
	$(eval CURRENT_VERSION := $(shell bump2version \
	                            --allow-dirty \
	                            --dry-run \
	                            --list $(RELEASE) \
	                            | grep current_version \
	                            | sed s,"^.*=",,))
	$(PYEXEC) towncrier --version $(CURRENT_VERSION) --name pytest_memray

.PHONY: release-patch
release-patch: RELEASE=patch
release-patch: bump_version gen_news  ## Prepare patch version release

.PHONY: release-minor
release-minor: RELEASE=minor
release-minor: bump_version gen_news  ## Prepare minor version release

.PHONY: release-major
release-major: RELEASE=major
release-major: bump_version gen_news ## Prepare major version release

.PHONY: help
help:  ## Print this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
