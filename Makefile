LINTER_DIRS := tests
NEURO_COMMAND=neuro --verbose --show-traceback --color=no
TMP_DIR := $(shell mktemp -d)
VERSION_FILE := version.txt

.PHONY: setup init
setup init:
	pip install -r '{{cookiecutter.project_slug}}/requirements.txt'
	pip install -r requirements.txt

.PHONY: cook
cook:
	cookiecutter gh:neuro-inc/cookiecutter-neuro-project

.PHONY: get-version
get-version: $(VERSION_FILE)
	cat $(VERSION_FILE)

.PHONY: update-version
update-version:
	echo "v`date +"%y.%m.%d"`" > $(VERSION_FILE)

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

.PHONY: test
test:
	 export TMP_DIR=$$(mktemp -d) && \
	   cookiecutter --no-input --config-file ./tests/cookiecutter.yaml --output-dir $$TMP_DIR . && \
	   ls -d $$TMP_DIR/test-project/.neuro/
	 pytest -v -s tests/unit
	 pytest -v -s tests/e2e
	 @echo -e "OK\n"

.PHONY: changelog-draft
changelog-draft: update-version $(VERSION_FILE)
	towncrier --draft --name "Neuro Platform Project Template" --version `cat version.txt`

.PHONY: changelog
changelog: update-version $(VERSION_FILE)
	towncrier --name "Neuro Platform Project Template" --version `cat version.txt` --yes
