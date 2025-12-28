# Makefile for RFC-Shared-Agent-Scaffolding
#
# Purpose: Provides convenient targets for common development tasks including
# linting, validation, and testing. Supports both local development workflow
# and CI automation.
#
# Usage:
# - make lint-yaml       : Run YAML linting (yamllint + actionlint)
# - make lint-all        : Run all linters
# - make validate        : Run validation scripts
# - make help            : Show available targets
#
# Dependencies:
# - yamllint (install: pip install yamllint)
# - actionlint (install: see https://github.com/rhysd/actionlint)
# - Python 3.8+ (for validation scripts)
# - Bash (for shell scripts)
# - For lint-all target: black, flake8, pylint (Python), shellcheck (Bash)
#
# Notes:
# - Targets fail fast on errors
# - Use 'make -k' to continue on errors
# - CI workflows use the same commands for consistency

.PHONY: help lint-yaml lint-all validate

help:
	@echo "Available targets:"
	@echo "  lint-yaml       - Run YAML linting (yamllint + actionlint)"
	@echo "  lint-all        - Run all linters"
	@echo "  validate        - Run validation scripts"
	@echo "  help            - Show this help message"

# YAML linting
lint-yaml:
	@echo "Running yamllint..."
	yamllint .
	@echo "Running actionlint..."
	actionlint -shellcheck= .github/workflows/*.yml

# All linters
lint-all: lint-yaml
	@echo "Running Python linting..."
	@if [ -n "$$(git ls-files '**/*.py')" ]; then \
		black --check . ; \
		flake8 . ; \
		git ls-files -z '**/*.py' | xargs -0 -r pylint ; \
	fi
	@echo "Running Bash linting..."
	@if [ -n "$$(git ls-files '**/*.sh')" ]; then \
		git ls-files -z '**/*.sh' | xargs -0 -r shellcheck -S warning ; \
	fi

# Validation scripts
validate:
	@echo "Running docstring validation..."
	python3 scripts/validate-docstrings.py
	@echo "Running structure validation..."
	./scripts/validate-structure.sh
	@echo "Running reference verification..."
	./scripts/verify-repo-references.sh
