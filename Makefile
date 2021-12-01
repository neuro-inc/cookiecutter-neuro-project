LINTER_DIRS := tests
NEURO_COMMAND=neuro --verbose --show-traceback --color=no
TMP_DIR := $(shell mktemp -d)
VERSION_FILE := version.txt

.PHONY: setup init
setup init:
	pip install -r requirements/dev.txt
	cat requirements/pipx.txt | xargs -rn 1 -- pipx install -f
	pre-commit install

.PHONY: get-version
get-version: $(VERSION_FILE)
	cat $(VERSION_FILE)

.PHONY: update-version
update-version:
	echo "v`date +"%y.%m.%d"`" > $(VERSION_FILE)

.PHONY: lint
lint: format
	 mypy $(LINTER_DIRS)

.PHONY: format
format:
	pre-commit run --all-files --show-diff-on-failure

.PHONY: test
test:
	 export TMP_DIR=$$(mktemp -d) && \
	   cookiecutter --no-input --config-file ./tests/cookiecutter.yaml --output-dir $$TMP_DIR . && \
	   ls -d "$$TMP_DIR/test project/.neuro/"
	 pytest -v tests/unit
	 pytest -v tests/e2e
	 @echo -e "OK\n"

.PHONY: changelog-draft
changelog-draft: update-version $(VERSION_FILE)
	towncrier --draft --name "Neuro Platform Project Template" --version `cat version.txt`

.PHONY: changelog
changelog: update-version $(VERSION_FILE)
	towncrier --name "Neuro Platform Project Template" --version `cat version.txt` --yes
