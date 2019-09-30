CODE_PATH?={{cookiecutter.code_directory}}
DATA_PATH?=data
NOTEBOOKS_PATH?=notebooks
REQUIREMENTS_PIP?=requirements.txt
REQUIREMENTS_APT?=apt.txt
RESULTS_PATH?=results
PROJECT_PYTHON_FILES=setup.py setup.cfg

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

NEURO_CP=neuro cp --recursive --update --no-target-directory

SETUP_NAME?=setup-{{cookiecutter.project_slug}}
TRAINING_NAME?=training-{{cookiecutter.project_slug}}
JUPYTER_NAME?=jupyter-{{cookiecutter.project_slug}}
TENSORBOARD_NAME?=tensorboard-{{cookiecutter.project_slug}}
FILEBROWSER_NAME?=filebrowser-{{cookiecutter.project_slug}}

BASE_ENV_NAME?=neuromation/base
CUSTOM_ENV_NAME?=image:neuromation-{{cookiecutter.project_slug}}
TRAINING_MACHINE_TYPE?=gpu-small

# Set it to True (verbatim) to disable HTTP authentication for your jobs
DISABLE_HTTP_AUTH:=
ifeq ($(DISABLE_HTTP_AUTH), True)
	HTTP_AUTH:=--no-http-auth
endif

APT_COMMAND?=apt-get -qq
PIP_INSTALL_COMMAND?=pip install --progress-bar=off
# example:
# TRAINING_COMMAND="bash -c 'cd $(PROJECT_PATH_ENV) && python -u $(CODE_PATH)/train.py --data $(DATA_PATH_ENV)'"
TRAINING_COMMAND?='echo "Replace this placeholder with a training script execution"'


.PHONY: help
help:
	@# idea: https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -hE '^[a-zA-Z_-]+:\s*?### .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


##### SETUP #####

.PHONY: setup
setup: ### Setup remote environment
	neuro kill $(SETUP_NAME) >/dev/null 2>&1
	neuro run \
		--name $(SETUP_NAME) \
		--preset cpu-small \
		--detach \
		--volume $(PROJECT_PATH_STORAGE):$(PROJECT_PATH_ENV):ro \
		--env PLATFORMAPI_SERVICE_HOST="." \
		$(BASE_ENV_NAME) \
		'sleep 1h'
	neuro cp $(REQUIREMENTS_APT) $(REQUIREMENTS_APT_STORAGE)
	neuro cp $(REQUIREMENTS_PIP) $(REQUIREMENTS_PIP_STORAGE)
	for file in $(PROJECT_PYTHON_FILES); do neuro cp ./$$file $(PROJECT_PATH_STORAGE)/$$file; done
	neuro exec --no-key-check $(SETUP_NAME) "bash -c 'export DEBIAN_FRONTEND=noninteractive && $(APT_COMMAND) update && cat $(REQUIREMENTS_APT_ENV) | xargs -I % $(APT_COMMAND) install --no-install-recommends % && $(APT_COMMAND) clean && $(APT_COMMAND) autoremove && rm -rf /var/lib/apt/lists/*'"
	neuro exec --no-key-check $(SETUP_NAME) "bash -c '$(PIP_INSTALL_COMMAND) -r $(REQUIREMENTS_PIP_ENV)'"
	neuro --network-timeout 300 job save $(SETUP_NAME) $(CUSTOM_ENV_NAME)
	neuro kill $(SETUP_NAME)

##### STORAGE #####

.PHONY: upload-code
upload-code:  ### Upload code directory to the platform storage
	$(NEURO_CP) $(CODE_PATH) $(CODE_PATH_STORAGE)

.PHONY: clean-code
clean-code:  ### Delete code directory from the platform storage
	neuro rm -r $(CODE_PATH_STORAGE)

.PHONY: upload-data
upload-data:  ### Upload data directory to the platform storage
	$(NEURO_CP) $(DATA_PATH) $(DATA_PATH_STORAGE)

.PHONY: clean-data
clean-data:  ### Delete data directory from the platform storage
	neuro rm -r $(DATA_PATH_STORAGE)

.PHONY: upload-notebooks
upload-notebooks:  ### Upload notebooks directory to the platform storage
	$(NEURO_CP) $(NOTEBOOKS_PATH) $(NOTEBOOKS_PATH_STORAGE)

.PHONY: download-notebooks
download-notebooks:  ### Download notebooks directory from the platform storage
	$(NEURO_CP) $(NOTEBOOKS_PATH_STORAGE) $(NOTEBOOKS_PATH)

.PHONY: clean-notebooks
clean-notebooks:  ### Delete notebooks directory from the platform storage
	neuro rm -r $(NOTEBOOKS_PATH_STORAGE)

.PHONY: upload  ### Upload code, data, and notebooks directories to the platform storage
upload: upload-code upload-data upload-notebooks

.PHONY: clean  ### Delete code, data, and notebooks directories from the platform storage
clean: clean-code clean-data clean-notebooks

##### JOBS #####

.PHONY: training
training:  ### Run a training job
	neuro run \
		--name $(TRAINING_NAME) \
		--preset $(TRAINING_MACHINE_TYPE) \
		--volume $(DATA_PATH_STORAGE):$(DATA_PATH_ENV):ro \
		--volume $(CODE_PATH_STORAGE):$(CODE_PATH_ENV):ro \
		--volume $(RESULTS_PATH_STORAGE):$(RESULTS_PATH_ENV):rw \
		--env PLATFORMAPI_SERVICE_HOST="." \
		$(CUSTOM_ENV_NAME) \
		$(TRAINING_COMMAND)

.PHONY: kill-training
kill-training:  ### Terminate the training job
	neuro kill $(TRAINING_NAME)

.PHONY: connect-training
connect-training:  ### Connect to the remote shell running on the training job
	neuro exec --no-key-check $(TRAINING_NAME) bash

.PHONY: jupyter
jupyter: upload-code upload-notebooks ### Run a job with Jupyter Notebook and open UI in the default browser
	neuro run \
		--name $(JUPYTER_NAME) \
		--preset $(TRAINING_MACHINE_TYPE) \
		--http 8888 --detach \
		$(HTTP_AUTH) \
		--browse \
		--volume $(DATA_PATH_STORAGE):$(DATA_PATH_ENV):ro \
		--volume $(CODE_PATH_STORAGE):$(CODE_PATH_ENV):rw \
		--volume $(NOTEBOOKS_PATH_STORAGE):$(NOTEBOOKS_PATH_ENV):rw \
		--volume $(RESULTS_PATH_STORAGE):$(RESULTS_PATH_ENV):rw \
		--env PLATFORMAPI_SERVICE_HOST="." \
		$(CUSTOM_ENV_NAME) \
		'jupyter notebook --no-browser --ip=0.0.0.0 --allow-root --NotebookApp.token= --notebook-dir=$(PROJECT_PATH_ENV)'

.PHONY: kill-jupyter
kill-jupyter:  ### Terminate the job with Jupyter Notebook
	neuro kill $(JUPYTER_NAME)

.PHONY: tensorboard
tensorboard:  ### Run a job with TensorBoard and open UI in the default browser
	neuro run \
		--name $(TENSORBOARD_NAME) \
		--preset cpu-small \
		--browse \
		--http 6006 --detach \
		$(HTTP_AUTH) \
		--volume $(RESULTS_PATH_STORAGE):$(RESULTS_PATH_ENV):ro \
		--env PLATFORMAPI_SERVICE_HOST="." \
		$(CUSTOM_ENV_NAME) \
		'tensorboard --logdir=$(RESULTS_PATH_ENV)'

.PHONY: kill-tensorboard
kill-tensorboard:  ### Terminate the job with TensorBoard
	neuro kill $(TENSORBOARD_NAME)

.PHONY: filebrowser
filebrowser:  ### Run a job with File Browser and open UI in the default browser
	neuro run \
		--name $(FILEBROWSER_NAME) \
		--preset cpu-small \
		--http 80 --detach \
		$(HTTP_AUTH) \
		--browse \
		--volume $(PROJECT_PATH_STORAGE):/srv:rw \
		--env PLATFORMAPI_SERVICE_HOST="." \
		filebrowser/filebrowser

.PHONY: kill-filebrowser
kill-filebrowser:  ### Terminate the job with File Browser
	neuro kill $(FILEBROWSER_NAME)

.PHONY: kill  ### Terminate all jobs of this project
kill: kill-training kill-jupyter kill-tensorboard kill-filebrowser

##### LOCAL #####

.PHONY: setup-local
setup-local:  ### Install pip requirements locally
	$(PIP_INSTALL_COMMAND) -r $(REQUIREMENTS_PIP)

.PHONY: lint
lint:  ### Run static code analysis locally
	flake8 .
	mypy .

##### MISC #####

.PHONY: ps
ps:  ### List all running and pending jobs
	neuro ps
