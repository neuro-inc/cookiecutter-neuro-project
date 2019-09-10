CODE_PATH?={{cookiecutter.project_slug}}
DATA_PATH?=data
NOTEBOOKS_PATH?=notebooks
REQUIREMENTS_PIP?=requirements.txt
REQUIREMENTS_APT?=apt.txt
RESULTS_PATH?=results
PROJECT_PATH_STORAGE?=storage:{{cookiecutter.project_slug}}
CODE_PATH_STORAGE?=$(PROJECT_PATH_STORAGE)/$(CODE_PATH)
DATA_PATH_STORAGE?=$(PROJECT_PATH_STORAGE)/$(DATA_PATH)
NOTEBOOKS_PATH_STORAGE?=$(PROJECT_PATH_STORAGE)/$(NOTEBOOKS_PATH)
REQUIREMENTS_PIP_STORAGE?=$(PROJECT_PATH_STORAGE)/$(REQUIREMENTS_PIP)
REQUIREMENTS_APT_STORAGE?=$(PROJECT_PATH_STORAGE)/$(REQUIREMENTS_APT)
RESULTS_PATH_STORAGE?=$(PROJECT_PATH_STORAGE)/$(RESULTS_PATH)

PROJECT_PATH_ENV?=/project
CODE_PATH_ENV?=$(PROJECT_PATH_ENV)/$(CODE_PATH)
DATA_PATH_ENV?=$(PROJECT_PATH_ENV)/$(DATA_PATH)
NOTEBOOKS_PATH_ENV?=$(PROJECT_PATH_ENV)/$(NOTEBOOKS_PATH)
REQUIREMENTS_PIP_ENV?=$(PROJECT_PATH_ENV)/$(REQUIREMENTS_PIP)
REQUIREMENTS_APT_ENV?=$(PROJECT_PATH_ENV)/$(REQUIREMENTS_APT)
RESULTS_PATH_ENV?=$(PROJECT_PATH_ENV)/$(RESULTS_PATH)

SETUP_NAME?=setup
TRAINING_NAME?=training
JUPYTER_NAME?=jupyter
TENSORBOARD_NAME?=tensorboard
FILEBROWSER_NAME?=filebrowser

BASE_ENV_NAME?=neuromation/base-2
CUSTOM_ENV_NAME?=image:neuromation-{{cookiecutter.project_slug}}


.PHONY: help
help:
	# idea: https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z_-]+:\s*?### .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


##### SETUP #####

.PHONY: setup
setup: ### Setup remote environment
	neuro kill $(SETUP_NAME)
	neuro run \
		--name $(SETUP_NAME) \
		--preset cpu-small \
		--detach \
		--volume $(PROJECT_PATH_STORAGE):$(PROJECT_PATH_ENV):ro \
		$(BASE_ENV_NAME) \
		'sleep 1h'
	neuro cp $(REQUIREMENTS_APT) $(REQUIREMENTS_APT_STORAGE)
	neuro cp $(REQUIREMENTS_PIP) $(REQUIREMENTS_PIP_STORAGE)
	neuro exec $(SETUP_NAME) "bash -c 'apt-get update && cat $(REQUIREMENTS_APT_ENV) | xargs -I % apt-get install -y --no-install-recommends % && apt-get clean && apt-get autoremove && rm -rf /var/lib/apt/lists/*'"
	neuro exec $(SETUP_NAME) 'pip install -r $(REQUIREMENTS_PIP_ENV)'
	neuro job save $(SETUP_NAME) $(CUSTOM_ENV_NAME)
	neuro kill $(SETUP_NAME)

##### STORAGE #####

.PHONY: upload_code
upload_code:  ### Upload code directory to Storage
	neuro cp -r -T $(CODE_PATH) $(CODE_PATH_STORAGE)

.PHONY: clean_code
clean_code:  ### Delete code directory on Storage
	neuro rm -r $(CODE_PATH_STORAGE)

.PHONY: upload_data  ### Upload data directory to Storage
upload_data:
	neuro storage load -p -u -T $(DATA_PATH) $(DATA_PATH_STORAGE)

.PHONY: clean_data  ### Delete data directory on Storage
clean_data:
	neuro rm -r $(DATA_PATH_STORAGE)

.PHONY: upload_notebooks
upload_notebooks:  ### Upload notebooks directory to Storage
	neuro cp -r -T $(NOTEBOOKS_PATH) $(NOTEBOOKS_PATH_STORAGE)

.PHONY: download_notebooks
download_notebooks:  ### Download notebooks directory from Storage
	neuro cp -r $(NOTEBOOKS_PATH_STORAGE) $(NOTEBOOKS_PATH)

.PHONY: clean_notebooks
clean_notebooks:  ### Delete notebooks directory on Storage
	neuro rm -r $(NOTEBOOKS_PATH_STORAGE)

.PHONY: upload  ### Upload code, data and notebooks directories to Storage
upload: upload_code upload_data upload_notebooks

.PHONY: clean  ### Delete code, data and notebooks directories on Storage
clean: clean_code clean_data clean_notebooks

##### JOBS #####

.PHONY: training
training:  ### Run training job
	neuro run \
		--name $(TRAINING_NAME) \
		--preset gpu-small \
		--volume $(DATA_PATH_STORAGE):$(DATA_PATH_ENV):ro \
		--volume $(CODE_PATH_STORAGE):$(CODE_PATH_ENV):ro \
		--volume $(RESULTS_PATH_STORAGE):$(RESULTS_PATH_ENV):rw \
		$(CUSTOM_ENV_NAME) \
		'python $(CODE_PATH_ENV)/train.py --log_dir $(RESULTS_PATH_ENV) --data_root $(DATA_PATH_ENV)/cifar10'

.PHONY: kill_training
kill_training:  ### Stop training job
	neuro kill $(TRAINING_NAME)

.PHONY: connect_training
connect_training:  ### Execute shell to the training job
	neuro exec $(TRAINING_NAME) bash

.PHONY: jupyter
jupyter:  ### Run jupyter job
	neuro run \
		--name $(JUPYTER_NAME) \
		--preset gpu-small \
		--http 8888 --no-http-auth --detach \
		--volume $(DATA_PATH_STORAGE):$(DATA_PATH_ENV):ro \
		--volume $(CODE_PATH_STORAGE):$(CODE_PATH_ENV):rw \
		--volume $(NOTEBOOKS_PATH_STORAGE):$(NOTEBOOKS_PATH_ENV):rw \
		--volume $(RESULTS_PATH_STORAGE):$(RESULTS_PATH_ENV):rw \
		$(CUSTOM_ENV_NAME) \
		'jupyter notebook --no-browser --ip=0.0.0.0 --allow-root --NotebookApp.token= --notebook-dir=$(NOTEBOOKS_PATH_ENV)'
	neuro job browse $(JUPYTER_NAME)

.PHONY: kill_jupyter
kill_jupyter:  ### Stop jupyter job
	neuro kill $(JUPYTER_NAME)

.PHONY: tensorboard
tensorboard:  ### Run tensorboard job
	neuro run \
		--name $(TENSORBOARD_NAME) \
		--preset cpu-small \
		--http 6006 --no-http-auth --detach \
		--volume $(RESULTS_PATH_STORAGE):$(RESULTS_PATH_ENV):ro \
		$(CUSTOM_ENV_NAME) \
		'tensorboard --logdir=$(RESULTS_PATH_ENV)'
	neuro job browse $(TENSORBOARD_NAME)

.PHONY: kill_tensorboard
kill_tensorboard:  ### Kill tensorboard job
	neuro kill $(TENSORBOARD_NAME)

.PHONY: filebrowser
filebrowser:  ### Run filebrowser job
	neuro run \
		--name $(FILEBROWSER_NAME) \
		--preset cpu-small \
		--http 80 --no-http-auth --detach \
		--volume $(PROJECT_PATH_STORAGE):/srv:rw \
		filebrowser/filebrowser
	neuro job browse $(FILEBROWSER_NAME)

.PHONY: kill_filebrowser
kill_filebrowser:  ### Kill filebrowser job
	neuro kill $(FILEBROWSER_NAME)

.PHONY: kill  ### Kill training, jupyter, tensorboard and filebrowser jobs (even if some of them are not running)
kill: kill_training kill_jupyter kill_tensorboard kill_filebrowser

##### LOCAL #####

.PHONY: setup_local
setup_local:  ### Install pip requirements locally
	pip install -r requirements/pip.txt

.PHONY: lint
lint:  ### Run static code analysis locally
	flake8 .
	mypy .

.PHONY: install
install:  ### Install project as a python package locally
	python setup.py install --user

##### MISC #####

.PHONY: ps
ps:  ### List all running and pending jobs
	neuro ps
