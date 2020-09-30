LINTER_DIRS := tests
NEURO_COMMAND=neuro --verbose --show-traceback --color=no
TMP_DIR := $(shell mktemp -d)

.PHONY: setup init
setup init:
	pip install -r '{{cookiecutter.project_slug}}/requirements.txt'
	pip install -r requirements.txt

.PHONY: cook
cook:
	cookiecutter gh:neuromation/cookiecutter-neuro-project

.PHONY: version
version:
	@grep -Po "^VERSION=(\K.+)" \{\{cookiecutter.project_slug\}\}/Makefile || echo "v?.?"

.PHONY: lint
lint:
	 isort -c -rc $(LINTER_DIRS)
	 black --check $(LINTER_DIRS)
	 mypy $(LINTER_DIRS)
	 flake8 $(LINTER_DIRS)

.PHONY: format
format:
	isort -rc $(LINTER_DIRS)
	black $(LINTER_DIRS)

.PHONY: test_unit
test_unit:
	 export TMP_DIR=$$(mktemp -d) && \
	   cookiecutter --no-input --config-file ./tests/cookiecutter.yaml --output-dir $$TMP_DIR . && \
	   ls -d $$TMP_DIR/test-project/.neuro/
	 @echo -e "OK\n"
	 pytest -v -s tests/unit
	 @echo -e "OK\n"
