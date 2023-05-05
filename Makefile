LINTER_DIRS := tests
NEURO_COMMAND=neuro --verbose --show-traceback --color=no
TMP_DIR := $(shell mktemp -d)
VERSION_FILE := version.txt

.PHONY: setup init
setup init:
	pip install -r requirements/dev.txt
	# cat requirements/pipx.txt | xargs -rn 1 -- pipx install -f
	# tmp work-around awaiting for the release of sdk. afterwards - rm belov pipx commands and uncomment above
	# also, replace deps installation in tests/unit/test_bake_project.py
	pipx install git+https://github.com/neuro-inc/neuro-cli.git@0ff55bb299b85c6c0052ed4fc8954a0cf8500119#subdirectory=neuro-cli/
	pipx runpip neuro-cli uninstall neuro-sdk -y
	pipx inject neuro-cli git+https://github.com/neuro-inc/neuro-cli.git@0ff55bb299b85c6c0052ed4fc8954a0cf8500119#subdirectory=neuro-sdk/
	pipx inject neuro-cli --include-apps git+https://github.com/neuro-inc/neuro-flow.git@248d39f7cbfdeeb9cdc079d9d793664b0060be46
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
	   ls -d "$$TMP_DIR/test flow/.neuro/"
	 pytest -v -n auto tests/unit
	 pytest -v -n auto tests/e2e
	 @echo -e "OK\n"

.PHONY: changelog-draft
changelog-draft: update-version $(VERSION_FILE)
	towncrier --draft --name "Neuro Platform Flow Template" --version `cat version.txt`

.PHONY: changelog
changelog: update-version $(VERSION_FILE)
	towncrier --name "Neuro Platform Flow Template" --version `cat version.txt` --yes
