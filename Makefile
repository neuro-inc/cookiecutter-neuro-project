ISORT_DIRS := tests cleanup_jobs.py
BLACK_DIRS := $(ISORT_DIRS)
MYPY_DIRS :=  tests

.PHONY: init
init:
	pip install -r requirements-dev.txt
	@echo OK

.PHONY: cook
cook:
	cookiecutter gh:neuromation/cookiecutter-neuro-project
	@echo OK

.PHONY: lint
lint:
	isort -c -rc ${ISORT_DIRS}
	black --check $(BLACK_DIRS)
	mypy $(MYPY_DIRS)
	flake8 $(FLAKE8_DIRS)
	@echo OK

.PHONY: format
format:
	isort -rc $(ISORT_DIRS)
	black $(BLACK_DIRS)
	@echo OK

.PHONY: test_unit
test_unit:
	pytest -v -s tests/unit
	cookiecutter --no-input --config-file ./tests/cookiecutter.yaml --output-dir .. .
	stat ../test_project
	python -m doctest tests/e2e/conftest.py
	@echo OK

.PHONY: test_e2e_dev
test_e2e_dev:
	TRAINING_MACHINE_TYPE=cpu-small pytest -s --environment=dev --tb=line --reruns=2 tests/e2e
	@echo OK

.PHONY: test_e2e_staging
test_e2e_staging:
	TRAINING_MACHINE_TYPE=gpu-small pytest -s --environment=staging --tb=line --reruns=2 tests/e2e
	@echo OK
