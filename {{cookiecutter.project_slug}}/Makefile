##### PATHS #####

DATA_PATH?=data
CODE_PATH?={{cookiecutter.code_directory}}
NOTEBOOKS_PATH?=notebooks
RESULTS_PATH?=results

PROJECT_FILES=requirements.txt apt.txt setup.cfg

PROJECT_PATH_STORAGE?=storage:{{cookiecutter.project_slug}}

PROJECT_PATH_ENV?=/{{cookiecutter.project_slug}}

##### JOB NAMES #####

PROJECT_POSTFIX?={{cookiecutter.project_slug.replace('_', '-')}}

SETUP_NAME?=setup-$(PROJECT_POSTFIX)
TRAINING_NAME?=training-$(PROJECT_POSTFIX)
JUPYTER_NAME?=jupyter-$(PROJECT_POSTFIX)
TENSORBOARD_NAME?=tensorboard-$(PROJECT_POSTFIX)
FILEBROWSER_NAME?=filebrowser-$(PROJECT_POSTFIX)

##### ENVIRONMENTS #####

BASE_ENV_NAME?=neuromation/base
CUSTOM_ENV_POSTFIX?=neuromation-$(PROJECT_POSTFIX)
USER_NAME := $(shell neuro config show | grep -oP 'User Name: \K\w+')
CUSTOM_ENV_NAME?=image://$(USER_NAME)/$(CUSTOM_ENV_POSTFIX)
TRAINING_MACHINE_TYPE?=gpu-small

##### COMMANDS #####

APT?=apt-get -qq
PIP?=pip install --progress-bar=off
NEURO?=neuro

##### VARIABLES YOU MAY WANT TO MODIFY #####

# Location of your dataset on the platform storage. Example:
# DATA_PATH_STORAGE?=storage:datasets/cifar10
DATA_PATH_STORAGE?=$(PROJECT_PATH_STORAGE)/$(DATA_PATH)
# The type of the training machine (run `neuro config show` to see the list of available types).
TRAINING_MACHINE_TYPE?=gpu-small
# HTTP authentication for the forwarded HTTP port (set `--no-http-auth` to disable it).
HTTP_AUTH?=--http-auth
# Command to run training inside the environment. Example:
# TRAINING_COMMAND="bash -c 'cd $(PROJECT_PATH_ENV) && python -u $(CODE_PATH)/train.py --data $(DATA_PATH)'"
TRAINING_COMMAND?='echo "Replace this placeholder with a training script execution"'

FORCE_SETUP?=no
ifeq (yes,$(FORCE_SETUP))
  PRE_SETUP_EXIT_CODE=0
else
  PRE_SETUP_EXIT_CODE=1
endif

##### HELP #####

.PHONY: help
help:
	@# idea: https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -hE '^[a-zA-Z_-]+:\s*?### .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

##### SETUP #####

.PHONY: pre-setup
pre-setup: ### Check environment before setup
	# Check if the target image already exists:
	$(NEURO) images | grep $(CUSTOM_ENV_NAME) && { echo "Image already exists"; exit $(PRE_SETUP_EXIT_CODE); } || { echo "Image does not exist"; }

.PHONY: setup
setup: pre-setup ### Setup remote environment
	$(NEURO) kill $(SETUP_NAME) >/dev/null 2>&1
	$(NEURO) run \
		--name $(SETUP_NAME) \
		--preset cpu-small \
		--detach \
		--volume $(PROJECT_PATH_STORAGE):$(PROJECT_PATH_ENV):ro \
		--env PLATFORMAPI_SERVICE_HOST="." \
		$(BASE_ENV_NAME) \
		'sleep 1h'
	for file in $(PROJECT_FILES); do $(NEURO) cp ./$$file $(PROJECT_PATH_STORAGE)/$$file; done
	$(NEURO) exec --no-tty --no-key-check $(SETUP_NAME) "bash -c 'export DEBIAN_FRONTEND=noninteractive && $(APT) update && cat $(PROJECT_PATH_ENV)/apt.txt | xargs -I % $(APT) install --no-install-recommends % && $(APT) clean && $(APT) autoremove && rm -rf /var/lib/apt/lists/*'"
	$(NEURO) exec --no-tty --no-key-check $(SETUP_NAME) "bash -c '$(PIP) -r $(PROJECT_PATH_ENV)/requirements.txt'"
	$(NEURO) --network-timeout 300 job save $(SETUP_NAME) $(CUSTOM_ENV_NAME)
	$(NEURO) kill $(SETUP_NAME)

##### STORAGE #####

.PHONY: upload-code
upload-code:  ### Upload code directory to the platform storage
	$(NEURO) cp --recursive --update --no-target-directory $(CODE_PATH) $(PROJECT_PATH_STORAGE)/$(CODE_PATH)

.PHONY: clean-code
clean-code:  ### Delete code directory from the platform storage
	$(NEURO) rm --recursive $(PROJECT_PATH_STORAGE)/$(CODE_PATH)

.PHONY: upload-data
upload-data:  ### Upload data directory to the platform storage
	$(NEURO) cp --recursive --update --no-target-directory $(DATA_PATH) $(DATA_PATH_STORAGE)

.PHONY: clean-data
clean-data:  ### Delete data directory from the platform storage
	$(NEURO) rm --recursive $(DATA_PATH_STORAGE)

.PHONY: upload-notebooks
upload-notebooks:  ### Upload notebooks directory to the platform storage
	$(NEURO) cp --recursive --update --no-target-directory $(NOTEBOOKS_PATH) $(PROJECT_PATH_STORAGE)/$(NOTEBOOKS_PATH)

.PHONY: download-notebooks
download-notebooks:  ### Download notebooks directory from the platform storage
	$(NEURO) cp --recursive --update --no-target-directory $(PROJECT_PATH_STORAGE)/$(NOTEBOOKS_PATH) $(NOTEBOOKS_PATH)

.PHONY: clean-notebooks
clean-notebooks:  ### Delete notebooks directory from the platform storage
	$(NEURO) rm --recursive $(PROJECT_PATH_STORAGE)/$(NOTEBOOKS_PATH)

.PHONY: upload  ### Upload code, data, and notebooks directories to the platform storage
upload: upload-code upload-data upload-notebooks

.PHONY: clean  ### Delete code, data, and notebooks directories from the platform storage
clean: clean-code clean-data clean-notebooks

##### JOBS #####

.PHONY: training
training:  ### Run a training job
	$(NEURO) run \
		--name $(TRAINING_NAME) \
		--preset $(TRAINING_MACHINE_TYPE) \
		--volume $(DATA_PATH_STORAGE):$(PROJECT_PATH_ENV)/$(DATA_PATH):ro \
		--volume $(PROJECT_PATH_STORAGE)/$(CODE_PATH):$(PROJECT_PATH_ENV)/$(CODE_PATH):ro \
		--volume $(PROJECT_PATH_STORAGE)/$(RESULTS_PATH):$(PROJECT_PATH_ENV)/$(RESULTS_PATH):rw \
		--env PLATFORMAPI_SERVICE_HOST="." \
		$(CUSTOM_ENV_NAME) \
		$(TRAINING_COMMAND)

.PHONY: kill-training
kill-training:  ### Terminate the training job
	$(NEURO) kill $(TRAINING_NAME)

.PHONY: connect-training
connect-training:  ### Connect to the remote shell running on the training job
	$(NEURO) exec --no-tty --no-key-check $(TRAINING_NAME) bash

.PHONY: jupyter
jupyter: upload-code upload-notebooks ### Run a job with Jupyter Notebook and open UI in the default browser
	$(NEURO) run \
		--name $(JUPYTER_NAME) \
		--preset $(TRAINING_MACHINE_TYPE) \
		--http 8888 \
		$(HTTP_AUTH) \
		--browse \
		--volume $(DATA_PATH_STORAGE):$(PROJECT_PATH_ENV)/$(DATA_PATH):ro \
		--volume $(PROJECT_PATH_STORAGE)/$(CODE_PATH):$(PROJECT_PATH_ENV)/$(CODE_PATH):rw \
		--volume $(PROJECT_PATH_STORAGE)/$(NOTEBOOKS_PATH):$(PROJECT_PATH_ENV)/$(NOTEBOOKS_PATH):rw \
		--volume $(PROJECT_PATH_STORAGE)/$(RESULTS_PATH):$(PROJECT_PATH_ENV)/$(RESULTS_PATH):rw \
		--env PLATFORMAPI_SERVICE_HOST="." \
		$(CUSTOM_ENV_NAME) \
		'jupyter notebook --no-browser --ip=0.0.0.0 --allow-root --NotebookApp.token= --notebook-dir=$(PROJECT_PATH_ENV)'

.PHONY: kill-jupyter
kill-jupyter:  ### Terminate the job with Jupyter Notebook
	$(NEURO) kill $(JUPYTER_NAME)

.PHONY: tensorboard
tensorboard:  ### Run a job with TensorBoard and open UI in the default browser
	$(NEURO) run \
		--name $(TENSORBOARD_NAME) \
		--preset cpu-small \
		--http 6006 \
		$(HTTP_AUTH) \
		--browse \
		--volume $(PROJECT_PATH_STORAGE)/$(RESULTS_PATH):$(PROJECT_PATH_ENV)/$(RESULTS_PATH):ro \
		--env PLATFORMAPI_SERVICE_HOST="." \
		$(CUSTOM_ENV_NAME) \
		'tensorboard --host=0.0.0.0 --logdir=$(PROJECT_PATH_ENV)/$(RESULTS_PATH)'

.PHONY: kill-tensorboard
kill-tensorboard:  ### Terminate the job with TensorBoard
	$(NEURO) kill $(TENSORBOARD_NAME)

.PHONY: filebrowser
filebrowser:  ### Run a job with File Browser and open UI in the default browser
	$(NEURO) run \
		--name $(FILEBROWSER_NAME) \
		--preset cpu-small \
		--http 80 \
		$(HTTP_AUTH) \
		--browse \
		--volume $(PROJECT_PATH_STORAGE):/srv:rw \
		--env PLATFORMAPI_SERVICE_HOST="." \
		filebrowser/filebrowser

.PHONY: kill-filebrowser
kill-filebrowser:  ### Terminate the job with File Browser
	$(NEURO) kill $(FILEBROWSER_NAME)

.PHONY: kill  ### Terminate all jobs of this project
kill: kill-training kill-jupyter kill-tensorboard kill-filebrowser

##### LOCAL #####

.PHONY: setup-local
setup-local:  ### Install pip requirements locally
	$(PIP) -r $(REQUIREMENTS_PIP)

.PHONY: lint
lint:  ### Run static code analysis locally
	flake8 .
	mypy .

##### MISC #####

.PHONY: ps
ps:  ### List all running and pending jobs
	$(NEURO) ps
