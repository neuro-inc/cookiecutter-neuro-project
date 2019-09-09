ISORT_DIRS := tasks.py setup.py
BLACK_DIRS := $(ISORT_DIRS)
MYPY_DIRS :=  tests

setup:
	pip install --disable-pip-version-check -r requirements-dev.txt

.PHONY: lint
lint:
	isort -c -rc ${ISORT_DIRS}
	black --check $(BLACK_DIRS)
	mypy $(MYPY_DIRS)
	flake8 $(FLAKE8_DIRS)

.PHONY: format
format:
	isort -rc $(ISORT_DIRS)
	black $(BLACK_DIRS)

.PHONY: test
test:
	pytest -v tests/
