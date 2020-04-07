VERSION=v1.4
BASE_ENV_VERSION=v1.4
PROJECT_ID=placeholder

##### CONSTANTS #####

DATA_DIR=data
CONFIG_DIR=config
CODE_DIR={{cookiecutter.code_directory}}
NOTEBOOKS_DIR=notebooks
RESULTS_DIR=results

PROJECT_PATH_STORAGE=storage:{{cookiecutter.project_slug}}
PROJECT_PATH_ENV=/project

PROJECT={{cookiecutter.project_slug}}
SETUP_JOB=setup-$(PROJECT)
TRAIN_JOB=train-$(PROJECT)
DEVELOP_JOB=develop-$(PROJECT)
JUPYTER_JOB=jupyter-$(PROJECT)
TENSORBOARD_JOB=tensorboard-$(PROJECT)
FILEBROWSER_JOB=filebrowser-$(PROJECT)
_PROJECT_TAGS=--tag "kind:project" \
              --tag "project:$(PROJECT)" \
              --tag "project-id:$(PROJECT_ID)"

BASE_ENV=neuromation/base:$(BASE_ENV_VERSION)
CUSTOM_ENV=image:neuromation-$(PROJECT):$(VERSION)

##### VARIABLES #####

# To overload a variable use either way:
# - change its default value in Makefile,
# - export variable: `export VAR=value`,
# - or change its value for a single run only: `make <target> VAR=value`.

# Allows to set the `neuro` executable:
#   make setup NEURO=/usr/bin/neuro
#   make setup NEURO="neuro --verbose --show-traceback"
NEURO=neuro


# Location of your dataset on the platform storage:
#   make setup DATA_DIR_STORAGE=storage:datasets/cifar10
DATA_DIR_STORAGE?=$(PROJECT_PATH_STORAGE)/$(DATA_DIR)

# The type of the training machine (run `neuro config show`
# to see the list of available types):
#   make jupyter PRESET=cpu-small
PRESET?=gpu-small

# Extra options for `neuro run` targets:
#   make train RUN_EXTRA="--env MYVAR=value"
RUN_EXTRA?=

# HTTP authentication (via cookies) for the job's HTTP link.
# Applied only to jupyter, tensorboard and filebrowser jobs.
# Set `HTTP_AUTH=--no-http-auth` to disable any authentication.
# WARNING: removing authentication might disclose your sensitive data stored in the job.
#   make jupyter HTTP_AUTH=--no-http-auth
HTTP_AUTH?=--http-auth

# If set to `yes`, then wait until the training job gets actually running,
# and stream logs to the standard output:
#   make train TRAIN_STREAM_LOGS=nope
TRAIN_STREAM_LOGS?=yes

# Command to run training inside the environment:
#   make train TRAIN_CMD="python ./train.py"
TRAIN_CMD?=python -u $(CODE_DIR)/train.py --data $(DATA_DIR)

# Postfix of training jobs:
#   make train RUN=experiment-2
#   make kill RUN=experiment-2
RUN?=base

# Local port to use in `port-forward`:
#   make port-forward-develop LOCAL_PORT=2233
LOCAL_PORT?=2211

# Jupyter mode. Available options: `notebook` (to
# run Jupyter Notebook), `lab` (to run JupyterLab):
#   make jupyter JUPYTER_MODE=LAB
JUPYTER_MODE?=notebook

# Number of hyper-parameter search jobs:
#   make hypertrain N_HYPERPARAM_JOBS=5
N_HYPERPARAM_JOBS?=3

# Google Cloud integration settings:
#   make gcloud-check-auth GCP_SECRET_FILE=name-of-gcp-key-file.json
GCP_SECRET_FILE?=neuro-job-key.json

# AWS integration settings:
#   make aws-check-auth AWS_SECRET_FILE=name-of-aws-key-file.json
AWS_SECRET_FILE?=aws-credentials.txt

# Weights and Biases integration settings:
#   make wandb-check-auth WANDB_SECRET_FILE=name-of-wandb-key-file.json
WANDB_SECRET_FILE?=wandb-token.txt

# Weights and Biases hyperparameter search configuration file:
#   make hypertrain WANDB_SECRET_FILE=name-of-wandb-sweep-file.json
WANDB_SWEEP_CONFIG_FILE?=wandb-sweep.yaml


##### CONSTANTS #####

GCP_SECRET_PATH_LOCAL=$(CONFIG_DIR)/$(GCP_SECRET_FILE)
GCP_SECRET_PATH_ENV=$(PROJECT_PATH_ENV)/$(GCP_SECRET_PATH_LOCAL)
AWS_SECRET_PATH_LOCAL=$(CONFIG_DIR)/$(AWS_SECRET_FILE)
AWS_SECRET_PATH_ENV=$(PROJECT_PATH_ENV)/$(AWS_SECRET_PATH_LOCAL)
WANDB_SECRET_PATH_LOCAL=$(CONFIG_DIR)/$(WANDB_SECRET_FILE)
WANDB_SECRET_PATH_ENV=$(PROJECT_PATH_ENV)/$(WANDB_SECRET_PATH_LOCAL)
WANDB_SWEEP_CONFIG_PATH=$(CODE_DIR)/$(WANDB_SWEEP_CONFIG_FILE)
WANDB_SWEEPS_FILE=.wandb_sweeps


ifeq ($(TRAIN_STREAM_LOGS), yes)
	TRAIN_WAIT_START_OPTION=--wait-start --detach
else
	TRAIN_WAIT_START_OPTION=
endif
ifneq ($(wildcard $(GCP_SECRET_PATH_LOCAL)),)
	OPTION_GCP_CREDENTIALS=\
		--env GOOGLE_APPLICATION_CREDENTIALS="$(GCP_SECRET_PATH_ENV)" \
		--env GCP_SERVICE_ACCOUNT_KEY_PATH="$(GCP_SECRET_PATH_ENV)"
else
	OPTION_GCP_CREDENTIALS=
endif
ifneq ($(wildcard $(AWS_SECRET_PATH_LOCAL)),)
	OPTION_AWS_CREDENTIALS=\
		--env AWS_CONFIG_FILE="$(AWS_SECRET_PATH_ENV)" \
		--env NM_AWS_CONFIG_FILE="$(AWS_SECRET_PATH_ENV)"
else
	OPTION_AWS_CREDENTIALS=
endif
ifneq ($(wildcard $(WANDB_SECRET_PATH_LOCAL)),)
	OPTION_WANDB_CREDENTIALS=--env NM_WANDB_TOKEN_PATH="$(WANDB_SECRET_PATH_ENV)"
else
	OPTION_WANDB_CREDENTIALS=
endif

##### HELP #####

.PHONY: help
help:
	@# generate help message by parsing current Makefile
	@# idea: https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -hE '^[a-zA-Z_-]+:[^#]*?### .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

##### SETUP #####

.PHONY: setup
setup: ### Setup remote environment
	$(NEURO) mkdir --parents $(PROJECT_PATH_STORAGE) \
		$(PROJECT_PATH_STORAGE)/$(CODE_DIR) \
		$(DATA_DIR_STORAGE) \
		$(PROJECT_PATH_STORAGE)/$(CONFIG_DIR) \
		$(PROJECT_PATH_STORAGE)/$(NOTEBOOKS_DIR) \
		$(PROJECT_PATH_STORAGE)/$(RESULTS_DIR)
	$(NEURO) cp requirements.txt $(PROJECT_PATH_STORAGE)
	$(NEURO) cp apt.txt $(PROJECT_PATH_STORAGE)
	$(NEURO) cp setup.cfg $(PROJECT_PATH_STORAGE)
	$(NEURO) run $(RUN_EXTRA) \
		--name $(SETUP_JOB) \
		--tag "target:setup" $(_PROJECT_TAGS) \
		--preset cpu-small \
		--detach \
		--life-span=1h \
		--volume $(PROJECT_PATH_STORAGE):$(PROJECT_PATH_ENV):ro \
		$(BASE_ENV) \
		'sleep infinity'
	$(NEURO) exec --no-key-check -T $(SETUP_JOB) "bash -c 'export DEBIAN_FRONTEND=noninteractive && apt-get -qq update && cat $(PROJECT_PATH_ENV)/apt.txt | tr -d \"\\r\" | xargs -I % apt-get -qq install --no-install-recommends % && apt-get -qq clean && apt-get autoremove && rm -rf /var/lib/apt/lists/*'"
	$(NEURO) exec --no-key-check -T $(SETUP_JOB) "bash -c 'pip install --progress-bar=off -U --no-cache-dir -r $(PROJECT_PATH_ENV)/requirements.txt'"
	$(NEURO) --network-timeout 300 job save $(SETUP_JOB) $(CUSTOM_ENV)
	$(NEURO) kill $(SETUP_JOB) || :
	@touch .setup_done

.PHONY: kill-setup
kill-setup:  ### Terminate the setup job (if it was not killed by `make setup` itself)
	$(NEURO) kill $(SETUP_JOB) || :

.PHONY: _check_setup
_check_setup:
	@test -f .setup_done || { echo "Please run 'make setup' first"; false; }

##### STORAGE #####

.PHONY: upload-code
upload-code: _check_setup  ### Upload code directory to the platform storage
	$(NEURO) cp \
		--recursive \
		--update \
		--no-target-directory \
		$(CODE_DIR) $(PROJECT_PATH_STORAGE)/$(CODE_DIR)

.PHONY: download-code
download-code: _check_setup  ### Download code directory from the platform storage
	$(NEURO) cp \
		--recursive \
		--update \
		--no-target-directory \
		$(PROJECT_PATH_STORAGE)/$(CODE_DIR) $(CODE_DIR)

.PHONY: clean-code
clean-code: _check_setup  ### Delete code directory from the platform storage
	$(NEURO) rm --recursive $(PROJECT_PATH_STORAGE)/$(CODE_DIR)/*

.PHONY: upload-data
upload-data: _check_setup  ### Upload data directory to the platform storage
	$(NEURO) cp \
		--recursive \
		--update \
		--no-target-directory \
		$(DATA_DIR) $(DATA_DIR_STORAGE)

.PHONY: download-data
download-data: _check_setup  ### Download data directory from the platform storage
	$(NEURO) cp \
		--recursive \
		--update \
		--no-target-directory \
		$(DATA_DIR_STORAGE) $(DATA_DIR)

.PHONY: clean-data
clean-data: _check_setup  ### Delete data directory from the platform storage
	$(NEURO) rm --recursive $(DATA_DIR_STORAGE)/*

.PHONY: upload-config
upload-config: _check_setup  ### Upload config directory to the platform storage
	$(NEURO) cp \
		--recursive \
		--update \
		--no-target-directory \
		$(CONFIG_DIR) $(PROJECT_PATH_STORAGE)/$(CONFIG_DIR)

.PHONY: download-config
download-config: _check_setup  ### Download config directory from the platform storage
	$(NEURO) cp \
		--recursive \
		--update \
		--no-target-directory \
		$(PROJECT_PATH_STORAGE)/$(CONFIG_DIR) $(CONFIG_DIR)

.PHONY: clean-config
clean-config: _check_setup  ### Delete config directory from the platform storage
	$(NEURO) rm --recursive $(PROJECT_PATH_STORAGE)/$(CONFIG_DIR)/*

.PHONY: upload-notebooks
upload-notebooks: _check_setup  ### Upload notebooks directory to the platform storage
	$(NEURO) cp \
		--recursive \
		--update \
		--no-target-directory \
		--exclude="*" \
		--include="*.ipynb" \
		$(NOTEBOOKS_DIR) $(PROJECT_PATH_STORAGE)/$(NOTEBOOKS_DIR)

.PHONY: download-notebooks
download-notebooks: _check_setup  ### Download notebooks directory from the platform storage
	$(NEURO) cp \
		--recursive \
		--update \
		--no-target-directory \
		--exclude="*" \
		--include="*.ipynb" \
		$(PROJECT_PATH_STORAGE)/$(NOTEBOOKS_DIR) $(NOTEBOOKS_DIR)

.PHONY: clean-notebooks
clean-notebooks: _check_setup  ### Delete notebooks directory from the platform storage
	$(NEURO) rm --recursive $(PROJECT_PATH_STORAGE)/$(NOTEBOOKS_DIR)/*

.PHONY: upload-results
upload-results: _check_setup  ### Upload results directory to the platform storage
	$(NEURO) cp \
		--recursive \
		--update \
		--no-target-directory \
		$(RESULTS_DIR)/ $(PROJECT_PATH_STORAGE)/$(RESULTS_DIR)

.PHONY: download-results
download-results: _check_setup  ### Download results directory from the platform storage
		$(NEURO) cp \
		--recursive \
		--update \
		--no-target-directory \
		$(PROJECT_PATH_STORAGE)/$(RESULTS_DIR)/ $(RESULTS_DIR)

.PHONY: clean-results
clean-results: _check_setup  ### Delete results directory from the platform storage
	$(NEURO) rm --recursive $(PROJECT_PATH_STORAGE)/$(RESULTS_DIR)/*

.PHONY: upload-all
upload-all: upload-code upload-data upload-config upload-notebooks upload-results  ### Upload code, data, config, notebooks, and results directories to the platform storage

.PHONY: download-all
download-all: download-code download-data download-config download-notebooks download-results  ### Download code, data, config, notebooks, and results directories from the platform storage

.PHONY: clean-all
clean-all: clean-code clean-data clean-config clean-notebooks clean-results  ### Delete code, data, config, notebooks, and results directories from the platform storage

##### Google Cloud Integration #####

.PHONY: gcloud-check-auth
gcloud-check-auth:  ### Check if the file containing Google Cloud service account key exists
	@echo "Using variable: GCP_SECRET_FILE='$(GCP_SECRET_FILE)'"
	@test "$(OPTION_GCP_CREDENTIALS)" \
		&& echo "Google Cloud will be authenticated via service account key file: '$$PWD/$(GCP_SECRET_PATH_LOCAL)'" \
		|| { echo "ERROR: Not found Google Cloud service account key file: '$$PWD/$(GCP_SECRET_PATH_LOCAL)'"; \
			echo "Please save the key file named GCP_SECRET_FILE='$(GCP_SECRET_FILE)' to './$(CONFIG_DIR)/'"; \
			false; }

##### AWS Integration #####

.PHONY: aws-check-auth
aws-check-auth:  ### Check if the file containing AWS user account credentials exists
	@echo "Using variable: AWS_SECRET_FILE='$(AWS_SECRET_FILE)'"
	@test "$(OPTION_AWS_CREDENTIALS)" \
		&& echo "AWS will be authenticated via user account credentials file: '$$PWD/$(AWS_SECRET_PATH_LOCAL)'" \
		|| { echo "ERROR: Not found AWS user account credentials file: '$$PWD/$(AWS_SECRET_PATH_LOCAL)'"; \
			echo "Please save the key file named AWS_SECRET_FILE='$(AWS_SECRET_FILE)' to './$(CONFIG_DIR)/'"; \
			false; }

##### WandB Integration #####

.PHONY: wandb-check-auth
wandb-check-auth:  ### Check if the file Weights and Biases authentication file exists
	@echo Using variable: WANDB_SECRET_FILE='$(WANDB_SECRET_FILE)'
	@test "$(OPTION_WANDB_CREDENTIALS)" \
		&& echo "Weights & Biases will be authenticated via key file: '$$PWD/$(WANDB_SECRET_PATH_LOCAL)'" \
		|| { echo "ERROR: Not found Weights & Biases key file: '$$PWD/$(WANDB_SECRET_PATH_LOCAL)'"; \
			echo "Please save the key file named WANDB_SECRET_FILE='$(WANDB_SECRET_FILE)' to './$(CONFIG_DIR)/'"; \
			false; }

##### JOBS #####

.PHONY: develop
develop: _check_setup upload-code upload-config upload-notebooks  ### Run a development job
	$(NEURO) run $(RUN_EXTRA) \
		--name $(DEVELOP_JOB) \
		--tag "target:develop" $(_PROJECT_TAGS) \
		--preset $(PRESET) \
		--detach \
		--volume $(DATA_DIR_STORAGE):$(PROJECT_PATH_ENV)/$(DATA_DIR):ro \
		--volume $(PROJECT_PATH_STORAGE)/$(CODE_DIR):$(PROJECT_PATH_ENV)/$(CODE_DIR):rw \
		--volume $(PROJECT_PATH_STORAGE)/$(CONFIG_DIR):$(PROJECT_PATH_ENV)/$(CONFIG_DIR):ro \
		--volume $(PROJECT_PATH_STORAGE)/$(RESULTS_DIR):$(PROJECT_PATH_ENV)/$(RESULTS_DIR):rw \
		--env PYTHONPATH=$(PROJECT_PATH_ENV) \
		--env EXPOSE_SSH=yes \
		--life-span=1d \
		$(OPTION_GCP_CREDENTIALS) $(OPTION_AWS_CREDENTIALS) $(OPTION_WANDB_CREDENTIALS) \
		$(CUSTOM_ENV) \
		sleep infinity

.PHONY: connect-develop
connect-develop:  ### Connect to the remote shell running on the development job
	$(NEURO) exec --no-key-check $(DEVELOP_JOB) bash

.PHONY: logs-develop
logs-develop:  ### Connect to the remote shell running on the development job
	$(NEURO) logs $(DEVELOP_JOB)

.PHONY: port-forward-develop
port-forward-develop:  ### Forward SSH port to localhost for remote debugging
	@test $(LOCAL_PORT) || { echo 'Please set up env var LOCAL_PORT'; false; }
	$(NEURO) port-forward $(DEVELOP_JOB) $(LOCAL_PORT):22

.PHONY: kill-develop
kill-develop:  ### Terminate the development job
	$(NEURO) kill $(DEVELOP_JOB) || :

.PHONY: train
train: _check_setup upload-code upload-config   ### Run a training job (set up env var 'RUN' to specify the training job),
	$(NEURO) run $(RUN_EXTRA) \
		--name $(TRAIN_JOB)-$(RUN) \
		--tag "target:train" $(_PROJECT_TAGS) \
		--preset $(PRESET) \
		--detach \
		$(TRAIN_WAIT_START_OPTION) \
		--volume $(DATA_DIR_STORAGE):$(PROJECT_PATH_ENV)/$(DATA_DIR):ro \
		--volume $(PROJECT_PATH_STORAGE)/$(CODE_DIR):$(PROJECT_PATH_ENV)/$(CODE_DIR):ro \
		--volume $(PROJECT_PATH_STORAGE)/$(CONFIG_DIR):$(PROJECT_PATH_ENV)/$(CONFIG_DIR):ro \
		--volume $(PROJECT_PATH_STORAGE)/$(RESULTS_DIR):$(PROJECT_PATH_ENV)/$(RESULTS_DIR):rw \
		--env PYTHONPATH=$(PROJECT_PATH_ENV) \
		--env EXPOSE_SSH=yes \
		--life-span=0 \
		$(OPTION_GCP_CREDENTIALS) $(OPTION_AWS_CREDENTIALS) $(OPTION_WANDB_CREDENTIALS) \
		$(CUSTOM_ENV) \
		bash -c 'cd $(PROJECT_PATH_ENV) && $(TRAIN_CMD)'
ifeq ($(TRAIN_STREAM_LOGS), yes)
	@echo "Streaming logs of the job $(TRAIN_JOB)-$(RUN)"
	$(NEURO) exec --no-key-check -T $(TRAIN_JOB)-$(RUN) "tail -f /output" || echo -e "Stopped streaming logs.\nUse 'neuro logs <job>' to see full logs."
endif

.PHONY: kill-train
kill-train:  ### Terminate the training job (set up env var 'RUN' to specify the training job)
	$(NEURO) kill $(TRAIN_JOB)-$(RUN) || :

.PHONY: kill-train-all
kill-train-all:  ### Terminate all training jobs you have submitted
	jobs=`neuro -q ps --tag "target:train" $(_PROJECT_TAGS) | tr -d "\r"` && \
	[ ! "$$jobs" ] || $(NEURO) kill $$jobs

.PHONY: hypertrain
hypertrain: _check_setup wandb-check-auth   ### Run jobs in parallel for hyperparameters search using W&B
	@echo "Initializing local wandb using config file './$(WANDB_SECRET_PATH_LOCAL)'"
	@wandb login `cat "./$(WANDB_SECRET_PATH_LOCAL)"`
	echo "Creating W&B Sweep..."
	echo "Using variable: WANDB_SWEEP_CONFIG_FILE='$(WANDB_SWEEP_CONFIG_FILE)'"
	@[ -f "$(WANDB_SWEEP_CONFIG_PATH)" ] \
		&& echo "Using W&B sweep file: ./$(WANDB_SWEEP_CONFIG_PATH)" \
		|| { echo "ERROR: W&B sweep config file not found: '$$PWD/$(WANDB_SWEEP_CONFIG_PATH)'" >&2; false; }
	WANDB_PROJECT=$(PROJECT) wandb sweep $(WANDB_SWEEP_CONFIG_PATH) 2>&1 | tee /proc/self/fd/2 | grep 'Created sweep with ID: ' | awk 'NF{ print $$NF }' >> $(WANDB_SWEEPS_FILE)
	@echo "Sweep created and saved to '$(WANDB_SWEEPS_FILE)'"
	@echo "Updating code and config directories on Neuro Storage..."
	$(NEURO) cp --recursive --update --no-target-directory $(CODE_DIR) $(PROJECT_PATH_STORAGE)/$(CODE_DIR)
	$(NEURO) cp --recursive --update --no-target-directory $(CONFIG_DIR) $(PROJECT_PATH_STORAGE)/$(CONFIG_DIR)
	@echo "Uploading wandb config file './wandb/settings' to Neuro Storage..."
	$(NEURO) mkdir -p $(PROJECT_PATH_STORAGE)/wandb
	$(NEURO) cp ./wandb/settings $(PROJECT_PATH_STORAGE)/wandb/
	sweep=`tail -1 $(WANDB_SWEEPS_FILE)` && \
	$(NEURO) mkdir -p $(PROJECT_PATH_STORAGE)/$(RESULTS_DIR)/sweep-$$sweep && \
	echo "Running $(N_HYPERPARAM_JOBS) jobs of sweep '$$sweep'..." && \
	for index in `seq 1 $(N_HYPERPARAM_JOBS)` ; do \
		echo -e "\nStarting job $$index..." ; \
		$(NEURO) run $(RUN_EXTRA) \
			--name $(TRAIN_JOB)-$$sweep-$$index \
			--tag "target:hypertrain" --tag "target:train" --tag "wandb-sweep:$$sweep" $(_PROJECT_TAGS) \
			--preset $(PRESET) \
			--detach \
			--volume $(DATA_DIR_STORAGE):$(PROJECT_PATH_ENV)/$(DATA_DIR):ro \
			--volume $(PROJECT_PATH_STORAGE)/$(CODE_DIR):$(PROJECT_PATH_ENV)/$(CODE_DIR):ro \
			--volume $(PROJECT_PATH_STORAGE)/$(CONFIG_DIR):$(PROJECT_PATH_ENV)/$(CONFIG_DIR):ro \
			--volume $(PROJECT_PATH_STORAGE)/sweep-$$sweep:$(PROJECT_PATH_ENV)/sweep-$$sweep:rw \
			--volume $(PROJECT_PATH_STORAGE)/wandb:$(PROJECT_PATH_ENV)/wandb:rw \
			--env PYTHONPATH=$(PROJECT_PATH_ENV) \
			--env EXPOSE_SSH=yes \
			--life-span=0 \
			$(OPTION_GCP_CREDENTIALS) $(OPTION_AWS_CREDENTIALS) $(OPTION_WANDB_CREDENTIALS) \
			$(CUSTOM_ENV) \
			bash -c "export WANDB_PROJECT=$(PROJECT) && cd $(PROJECT_PATH_ENV) && wandb status && wandb agent $$sweep"; \
	done; \
	echo -e "\nStarted $(N_HYPERPARAM_JOBS) hyper-parameter search jobs of sweep '$$sweep'.\nUse 'neuro ps' and 'neuro status <job>' to check."

.PHONY: kill-hypertrain
kill-hypertrain:  ### Terminate hyper-parameter search training jobs of the latest sweep
	sweep=`tail -1 $(WANDB_SWEEPS_FILE)` && \
	jobs=`neuro -q ps --tag "target:hypertrain" --tag "wandb-sweep:$$sweep" $(_PROJECT_TAGS) | tr -d "\r"` && \
	[ ! "$$jobs" ] || $(NEURO) kill $$jobs

.PHONY: kill-hypertrain-all
kill-hypertrain-all:  ### Terminate all hyper-parameter search training jobs of all the sweeps
	sweep=`tail -1 $(WANDB_SWEEPS_FILE)` && \
	jobs=`neuro -q ps --tag "target:hypertrain" $(_PROJECT_TAGS) | tr -d "\r"` && \
	[ ! "$$jobs" ] || $(NEURO) kill $$jobs

.PHONY: connect-train
connect-train: _check_setup  ### Connect to the remote shell running on the training job (set up env var 'RUN' to specify the training job)
	$(NEURO) exec --no-key-check $(TRAIN_JOB)-$(RUN) bash

.PHONY: jupyter
jupyter: _check_setup upload-config upload-code upload-notebooks ### Run a job with Jupyter Notebook and open UI in the default browser
	$(NEURO) run $(RUN_EXTRA) \
		--name $(JUPYTER_JOB) \
		--tag "target:jupyter" $(_PROJECT_TAGS) \
		--preset $(PRESET) \
		--http 8888 \
		$(HTTP_AUTH) \
		--browse \
		--detach \
		--volume $(DATA_DIR_STORAGE):$(PROJECT_PATH_ENV)/$(DATA_DIR):ro \
		--volume $(PROJECT_PATH_STORAGE)/$(CODE_DIR):$(PROJECT_PATH_ENV)/$(CODE_DIR):rw \
		--volume $(PROJECT_PATH_STORAGE)/$(CONFIG_DIR):$(PROJECT_PATH_ENV)/$(CONFIG_DIR):ro \
		--volume $(PROJECT_PATH_STORAGE)/$(NOTEBOOKS_DIR):$(PROJECT_PATH_ENV)/$(NOTEBOOKS_DIR):rw \
		--volume $(PROJECT_PATH_STORAGE)/$(RESULTS_DIR):$(PROJECT_PATH_ENV)/$(RESULTS_DIR):rw \
		--life-span=1d \
		--env PYTHONPATH=$(PROJECT_PATH_ENV) \
		$(OPTION_GCP_CREDENTIALS) $(OPTION_AWS_CREDENTIALS) $(OPTION_WANDB_CREDENTIALS) \
		$(CUSTOM_ENV) \
		jupyter $(JUPYTER_MODE) \
			--no-browser \
			--ip=0.0.0.0 \
			--allow-root \
			--NotebookApp.token= \
			--notebook-dir=$(PROJECT_PATH_ENV)/$(NOTEBOOKS_DIR)

.PHONY: kill-jupyter
kill-jupyter:  ### Terminate the job with Jupyter Notebook
	$(NEURO) kill $(JUPYTER_JOB) || :

.PHONY: jupyterlab
jupyterlab:  ### Run a job with JupyterLab and open UI in the default browser
	@make --silent jupyter JUPYTER_MODE=lab

.PHONY: kill-jupyterlab
kill-jupyterlab:  ### Terminate the job with JupyterLab
	@make --silent kill-jupyter

.PHONY: tensorboard
tensorboard: _check_setup  ### Run a job with TensorBoard and open UI in the default browser
	$(NEURO) run $(RUN_EXTRA) \
		--name $(TENSORBOARD_JOB) \
		--preset cpu-small \
		--tag "target:tensorboard" $(_PROJECT_TAGS) \
		--http 6006 \
		$(HTTP_AUTH) \
		--browse \
		--life-span=1d \
		--volume $(PROJECT_PATH_STORAGE)/$(RESULTS_DIR):$(PROJECT_PATH_ENV)/$(RESULTS_DIR):ro \
		tensorflow/tensorflow:latest \
		tensorboard --host=0.0.0.0 --logdir=$(PROJECT_PATH_ENV)/$(RESULTS_DIR)

.PHONY: kill-tensorboard
kill-tensorboard:  ### Terminate the job with TensorBoard
	$(NEURO) kill $(TENSORBOARD_JOB) || :

.PHONY: filebrowser
filebrowser: _check_setup  ### Run a job with File Browser and open UI in the default browser
	$(NEURO) run $(RUN_EXTRA) \
		--name $(FILEBROWSER_JOB) \
		--tag "target:filebrowser" $(_PROJECT_TAGS) \
		--preset cpu-small \
		--http 80 \
		$(HTTP_AUTH) \
		--browse \
		--life-span=1d \
		--volume $(PROJECT_PATH_STORAGE):/srv:rw \
		filebrowser/filebrowser:latest \
		--noauth

.PHONY: kill-filebrowser
kill-filebrowser:  ### Terminate the job with File Browser
	$(NEURO) kill $(FILEBROWSER_JOB) || :

.PHONY: kill-all
kill-all:  ### Terminate all jobs of this project
	jobs=`neuro -q ps $(_PROJECT_TAGS) | tr -d "\r"` && \
	[ ! "$$jobs" ] || $(NEURO) kill $$jobs

##### LOCAL #####

.PHONY: setup-local
setup-local:  ### Install pip requirements locally
	pip install -r requirements.txt

.PHONY: format-local
format-local:  ### Automatically format the code
	isort -rc {{cookiecutter.code_directory}}
	black {{cookiecutter.code_directory}}

.PHONY: lint-local
lint-local:  ### Run static code analysis locally
	isort -c -rc {{cookiecutter.code_directory}}
	black --check {{cookiecutter.code_directory}}
	mypy {{cookiecutter.code_directory}}
	flake8 {{cookiecutter.code_directory}}

##### MISC #####

.PHONY: ps
ps:  ### List all running and pending jobs
	$(NEURO) ps $(_PROJECT_TAGS)

.PHONY: ps-hypertrain
ps-hypertrain:  ### List running and pending jobs of the latest hyper-parameter search sweep
	sweep=`tail -1 $(WANDB_SWEEPS_FILE)` && \
	echo "Using sweep '$$sweep'" && \
	$(NEURO) ps --tag "target:hypertrain" --tag "wandb-sweep:$$sweep" $(_PROJECT_TAGS)

.PHONY: ps-train-all
ps-train-all:  ### List all running and pending training jobs
	$(NEURO) ps --tag "target:train" $(_PROJECT_TAGS)


.PHONY: _upgrade
_upgrade:
	@if ! (git status | grep "nothing to commit"); then echo "Please commit or stash changes before upgrade."; exit 1; fi
	@echo "Applying the latest Neuro Project Template to this project..."
	cookiecutter \
		--output-dir .. \
		--no-input \
		--overwrite-if-exists \
		--checkout release \
		gh:neuromation/cookiecutter-neuro-project \
		project_slug=$(PROJECT) \
		code_directory=$(CODE_DIR)
	git checkout -- $(DATA_DIR) $(CODE_DIR) $(CONFIG_DIR) $(NOTEBOOKS_DIR) $(RESULTS_DIR)
	git checkout -- .gitignore requirements.txt apt.txt setup.cfg README.md
	@echo "Some files are successfully changed. Please review the changes using git diff."
