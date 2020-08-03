LINTER_DIRS := tests
NEURO_COMMAND=neuro --verbose --show-traceback --color=no
TMP_DIR := $(shell mktemp -d)

.PHONY: setup init
setup init:
	pip install -r requirements-dev.txt

.PHONY: cook
cook:
	cookiecutter gh:neuromation/cookiecutter-neuro-project

.PHONY: version
version:
	@grep -Po "^VERSION=(\K.+)" \{\{cookiecutter.project_slug\}\}/Makefile || echo "v?.?"

.PHONY: lint
lint:
#	 isort -c -rc $(LINTER_DIRS)
#	 black --check $(LINTER_DIRS)
#	 mypy $(LINTER_DIRS)
#	 flake8 $(LINTER_DIRS)

.PHONY: format
format:
	isort -rc $(LINTER_DIRS)
	black $(LINTER_DIRS)


.PHONY: test_doctest
test_doctest:
	# python -m doctest tests/e2e/conftest.py
	# python -m doctest tests/e2e/helpers/runners.py
	# python -m doctest tests/e2e/helpers/utils.py
	# @echo -e "OK\n"

.PHONY: test_unit
test_unit:
	 pytest -v -s tests/unit
	 @echo -e "OK\n"
	 cookiecutter --no-input --config-file ./tests/cookiecutter.yaml --output-dir $(TMP_DIR) .
	 stat $(TMP_DIR)/test-project
	 @echo -e "OK\n"

.PHONY: test_e2e_dev
test_e2e_dev:
	PRESET=cpu-small NEURO="$(NEURO_COMMAND)"  pytest -s -v --environment=dev --tb=short tests/e2e

.PHONY: test_e2e_staging
test_e2e_staging:
	PRESET=gpu-small NEURO="$(NEURO_COMMAND)"  pytest -s -v --environment=staging --tb=short tests/e2e

.PHONY: get_e2e_failures
get_e2e_failures:
	@[ -f tests/e2e/output/failures.txt ] && cat tests/e2e/output/failures.txt || echo "(no data)"

.PHONY: cleanup_e2e_storage
cleanup_e2e_storage:
	bash -c tests/e2e/cleanup.sh
