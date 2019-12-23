# {{ cookiecutter.project_name }}

# Description

This project is created from 
[Neuro Platform Project Template](https://github.com/neuromation/cookiecutter-neuro-project).

# Development Environment

This project is designed to run on [Neuro Platform](https://neu.ro), so you can jump into problem-solving right away.

## Directory structure

| Local directory                      | Description       | Storage URI                                                                  | Environment mounting point |
|:------------------------------------ |:----------------- |:---------------------------------------------------------------------------- |:-------------------------- | 
| `data/`                              | Data              | `storage:{{ cookiecutter.project_slug }}/data/`                              | `/{{ cookiecutter.project_slug }}/data/` | 
| `{{ cookiecutter.code_directory }}/` | Python modules    | `storage:{{ cookiecutter.project_slug }}/{{ cookiecutter.code_directory }}/` | `/{{ cookiecutter.project_slug }}/{{ cookiecutter.code_directory }}/` |
| `config/`                            | Configuration files | `storage:{{ cookiecutter.project_slug }}/config/`                          | `/{{ cookiecutter.project_slug }}/{{ cookiecutter.code_directory }}/` |
| `notebooks/`                         | Jupyter notebooks | `storage:{{ cookiecutter.project_slug }}/notebooks/`                         | `/{{ cookiecutter.project_slug }}/notebooks/` |
| No directory                         | Logs and results  | `storage:{{ cookiecutter.project_slug }}/results/`                           | `/{{ cookiecutter.project_slug }}/results/` |

## Development

Follow the instructions below to set up the environment and start Jupyter development session.

### Setup development environment 

`make setup`

* Several files from the local project are uploaded to the platform storage (namely, `requirements.txt`, 
  `apt.txt`, `setup.cfg`).
* A new job is started in our [base environment](https://hub.docker.com/r/neuromation/base). 
* Pip requirements from `requirements.txt` and apt applications from `apt.txt` are installed in this environment.
* The updated environment is saved under a new project-dependent name and is used further on.

### Run Jupyter with GPU 

`make jupyter`

* The content of `{{ cookiecutter.code_directory }}` and `notebooks` directories is uploaded to the platform storage.
* A job with Jupyter is started, and its web interface is opened in the local web browser window.

### Kill Jupyter

`make kill-jupyter`

* The job with Jupyter Notebooks is terminated. The notebooks are saved on the platform storage. You may run 
  `make download-notebooks` to download them to the local `notebooks/` directory.

### Help

`make help`

## Data

### Uploading to the Storage via Web UI

On local machine, run `make filebrowser` and open job's URL on your mobile device or desktop.
Through a simple file explorer interface, you can upload test images and perform file operations.

### Uploading to the Storage via CLI

On local machine, run `make upload-data`. This command pushes local files stored in `./data`
into `storage:{{ cookiecutter.project_slug }}/data` mounted to your development environment's `/project/data`.

### Uploading to the Job from Google Cloud

Google Cloud SDK is pre-installed on all jobs produced from the Base Image.

Neuro Project Template provides a fast way to authenticate Google Cloud SDK to work with Google Service Account (see instructions on setting up your Google Project and Google Service Account and creating the secret key for this Service Account in [documentation](https://neu.ro/docs/google_cloud_storage)).

Download service account key to the local config directory `./config/` and set appropriate permissions on it:

```bash
$ SA_NAME="neuro-job"
$ gcloud iam service-accounts keys create ./config/$SA_NAME-key.json \
  --iam-account $SA_NAME@$PROJECT_ID.iam.gserviceaccount.com
$ chmod 600 ./config/$SA_NAME-key.json
```

Inform Neuro about this file:

```bash
$ export GCP_SECRET_FILE=$SA_NAME-key.json
```

Alternatively, set this value directly in `Makefile`.

Check that Neuro can access and use this file for authentication:

```bash
$ make gcloud-check-auth
Using variable: GCP_SECRET_FILE='neuro-job-key.json'
Google Cloud will be authenticated via service account key file: '/path/to/project/config/neuro-job-key.json'
```

Now, if you run a `develop`, `train`, or `jupyter` job, Neuro will authenticate Google Cloud SDK via your secret file, so you will be able to use `gsutil` or `gcloud` there:

```bash
$ make develop
...
$ make connect-develop
...
root@job-56e9b297-5034-4492-ba1a-2284b8dcd613:/# gsutil cat gs://my-neuro-bucket-42/hello.txt
Hello World
```

Also, environment variable `GOOGLE_APPLICATION_CREDENTIALS` is set up for these jobs, so that you an access your data on Google Cloud Storage via Python API (see example in [Google Cloud Storage documentation](https://cloud.google.com/storage/docs/reference/libraries)).

## Customization

Several variables in `Makefile` are intended to be modified according to the project specifics. 
To change them, find the corresponding line in `Makefile` and update.

### Data location

`DATA_DIR_STORAGE?=$(PROJECT_PATH_STORAGE)/$(DATA_DIR)`

This project template implies that your data is stored alongside the project. If this is the case, you don't 
have to change this variable. However, if your data is shared between several projects on the platform, 
you need to change the following line to point to its location. For example:

`DATA_DIR_STORAGE?=storage:datasets/cifar10`

### Run development job

If you want to debug your code on GPU, you can run a sleeping job via `make develop`, then connect to its bash over SSH
via `make connect-develop` (type `exit` or `^D` to close SSH connection), see its logs via `make logs-develop`, or 
forward port 22 from the job to localhost via `make port-forward-develop` to use it for remote debugging.
Please find instructions on remote debugging via PyCharm Pro in the [documentation](https://neu.ro/docs/remote_debugging_pycharm). 

Please don't forget to kill your job via `make kill-develop` not to waste your quota!   

### Weights & Biases integration

Neuro Platform offers easy integration with [Weights & Biases](https://www.wandb.com), an experiment tracking tool for deep learning.
The instructions look similar to ones for Google Cloud integration above. 
First, you need to [register your W&B account](https://app.wandb.ai/login?signup=true). 
Then, find your API key on [W&B's settings page](https://app.wandb.ai/settings) (section "API keys"),
save it to a file in local directory `./config/`, protect by setting appropriate permissions 
and check that Neuro can access and use this file for authentication:

```
$ export WANDB_SECRET_FILE=wandb-token.txt
$ echo "cf23df2207d99a74fbe169e3eba035e633b65d94" > config/$WANDB_SECRET_FILE
$ chmod 600 config/$WANDB_SECRET_FILE
$ make wandb-check-auth 
Using variable: WANDB_SECRET_FILE=wandb-token.txt
Weights & Biases will be authenticated via key file: '/path/to/project/config/wandb-token.txt'
```

Now, if you run `develop`, `train`, or `jupyter` job, Neuro will authenticate W&B via your API key, 
so that you will be able to use `wandb` there:

```bash
$ make develop
...
$ make connect-develop
...
root@job-fe752aaf-5f76-4ba8-a477-0809632c4a59:/# wandb status
Logged in? True
...
```

So now, you can do `import wandb; api = wandb.Api()` in your Python code and use W&B.

Technically, authentication is being done as follows: 
when you start any job derived from the base environment, Neuro Platform checks if the env var `NM_WANDB_TOKEN_PATH`
is set and stores path to existing file, and then it runs the command `wandb login $(cat $NM_WANDB_TOKEN_PATH)`
before the job starts.
 
Please find instructions on using Weights & Biases in your code in [W&B documentation](https://docs.wandb.com/library/api/examples).
You can also find [W&B example projects](https://github.com/wandb/examples) or an example of Neuro Project Template-based 
[ML Recipe that uses W&B as a part of the workflow](https://neu.ro/docs/cookbook/ml-recipe-hier-attention). 

### Training machine type

`PRESET?=gpu-small`

There are several machine types supported on the platform. Run `neuro config show` to see the list.

### HTTP authentication

`HTTP_AUTH?=--http-auth`

When jobs with HTTP interface are executed (for example, with Jupyter Notebooks or TensorBoard), this interface requires
a user to be authenticated on the platform. However, if you want to share the link with someone who is not registered on
the platform, you may disable the authentication updating this line to `HTTP_AUTH?=--no-http-auth`.

### Training command

`TRAINING_COMMAND?='echo "Replace this placeholder with a training script execution"'`

If you want to train some models from code instead of Jupyter Notebooks, you need to update this line. For example:

`TRAINING_COMMAND="bash -c 'cd $(PROJECT_PATH_ENV) && python -u $(CODE_DIR)/train.py --data $(DATA_DIR)'"`

Please note that commands with arguments should be wrapped with either quotes `'` or double quotes `"` 
in order to be processed correctly.  