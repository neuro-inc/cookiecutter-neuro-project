# Neuro Project Template Reference

## Development Environment

This template runs on [Neuro Platform](https://neu.ro). 

To dive into the problem solving, you need to sign up at [Neuro Platform](https://neu.ro) website, set up your local machine according to [instructions](https://neu.ro/docs) and log into the Neuro CLI:

```shell
neuro login
```

## Directory structure

| Local directory | Description | Storage URI | Environment mounting point |
|:--------------- |:----------- |:----------- |:-------------------------- | 
| `data/` | Data | `storage:{{ cookiecutter.project_slug }}/data/` | `/{{ cookiecutter.project_slug }}/data/` | 
| `{{ cookiecutter.code_directory }}/` | Python modules | `storage:{{ cookiecutter.project_slug }}/{{ cookiecutter.code_directory }}/` | `/{{ cookiecutter.project_slug }}/{{ cookiecutter.code_directory }}/` |
| `config/` | Configuration files | `storage:{{ cookiecutter.project_slug }}/config/` | `/{{ cookiecutter.project_slug }}/config/` |
| `notebooks/` | Jupyter notebooks | `storage:{{ cookiecutter.project_slug }}/notebooks/` | `/{{ cookiecutter.project_slug }}/notebooks/` |
| `results/` | Logs and results | `storage:{{ cookiecutter.project_slug }}/results/` | `/{{ cookiecutter.project_slug }}/results/` |

## Development

Follow the instructions below to set up the environment on Neuro and start a Jupyter development session.

### Setup development environment 

```shell
neuro-flow build myimage
```

* Several files from the local project are uploaded to the platform storage (namely, `requirements.txt`,  `apt.txt`, `setup.cfg`).
* A new job is started in our [base environment](https://hub.docker.com/r/neuromation/base). 
* Pip requirements from `requirements.txt` and apt applications from `apt.txt` are installed in this environment.
* The updated environment is saved under a new project-dependent name and is used further on.

### Run Jupyter with GPU 

```shell
neuro-flow run jupyter
```

* The content of the `{{ cookiecutter.code_directory }}` and `notebooks` directories is uploaded to the platform storage.
* A job with Jupyter is started, and its web interface is opened in the local web browser window.

### Kill Jupyter

```shell 
neuro-flow kill jupyter
```

* The job with Jupyter Notebooks is terminated. The notebooks are saved on the platform storage. You may run `neuro-flow download notebooks` to download them to the local `notebooks/` directory.

### Help

```shell 
neuro-flow ps
```

* The list of all available template jobs is printed along with their statuses.


## Data

### Uploading to the Storage via Web UI

On local machine, run `neuro-flow run filebrowser` and open the job's URL on your mobile device or desktop.
Through a simple file explorer interface, you can upload test images and perform file operations.

### Uploading to the Storage via CLI

On local machine run `neuro-flow mkvolumes`. This commands creates storage folders for all defined volumes. You only need to run this once.

After storage folders have been created run `neuro-flow upload data` from the local machine as well. This command pushes local files stored in ./data into storage:{{ cookiecutter.project_slug }}/data mounted to your development environment's /project/data.

You can upload (or download) every folder for which the `local` parameter is specified in [live.yml file](./.neuro/live.yml).

### Uploading data to the Job from Google Cloud Storage

Google Cloud SDK is pre-installed on all jobs produced from the Base Image.

Please refer to the [documentation](https://docs.neu.ro/toolbox/accessing-object-storage-in-gcp) explaining how to start using GCP with the template.

### Uploading data to the Job from AWS S3

AWS CLI is pre-installed on all jobs produced from the Base Image.

Please refer to the [documentation](https://docs.neu.ro/toolbox/accessing-object-storage-in-aws) explaining how to start using AWS with the template.

### Run development job

If you want to debug your code on GPU, you can run a sleeping job via `neuro-flow run remote_debug`, which will also open a shell to the job. You can also see job logs via `neuro-flow logs remote_debug`. The job forwards your local port 2211 to its port 22for remote debugging.
Please find instructions on remote debugging via PyCharm Pro in the [documentation](https://neu.ro/docs/remote_debugging_pycharm). 

Please don't forget to kill your job via `make kill remote_debug` not to waste your quota!   

### Weights & Biases integration

Neuro Platform offers easy integration with [Weights & Biases](https://www.wandb.com), an experiment tracking tool for deep learning.

Here you can find [documentation](https://docs.neu.ro/toolbox/experiment-tracking-with-weights-and-biases) for using W&B for experiment tracking with the template.
 
Please find instructions on using Weights & Biases in your code in [W&B documentation](https://docs.wandb.com/library/api/examples).
You can also find [W&B example projects](https://github.com/wandb/examples) or an example of Neuro Project Template-based 
[ML Recipe that uses W&B as a part of the workflow](https://neu.ro/docs/cookbook/ml-recipe-hier-attention). 


### Training machine type

```yaml
defaults:
  preset: gpu-small-p
```

There are several machine types supported on the platform. Run `neuro config show` to see the list. You can also override default preset per job:

```yaml
jobs:
 train:
    image: $[[ images.myimage.ref ]]
    preset: gpu-large
    ...
```

### HTTP authentication

```yaml
args:
    http_auth: "False"
```

When jobs with HTTP interface are executed (for example, with Jupyter Notebooks or TensorBoard), this interface requires a user to be authenticated on the platform. However, if you want to share the link with someone who is not registered on the platform, you may disable the authentication adding this arg to your job configuration `http_auth: "False"`.

### Storage uploads

Running `neuro-flow upload ALL` from local machine uploads all of your code, config and notebooks to storage so that these folders can be used by your jobs.

### Training command

To tweak the training command, change the last line in this section of `live.yaml`:
 
```yaml
  train:
    image: $[[ images.myimage.ref ]]
    detach: True
    life_span: 10d
    volumes:
      - $[[ volumes.data.ref_ro ]]
      - $[[ volumes.code.ref_ro ]]
      - $[[ volumes.config.ref_ro ]]
      - $[[ volumes.results.ref_rw ]]
    env:
      EXPOSE_SSH: "yes"
      PYTHONPATH: $[[ volumes.code.mount ]]
    bash: |
        cd $[[ flow.workspace ]]
        python -u $[[ volumes.code.mount ]]/train.py --data $[[ volumes.data.mount ]]
```

And then, just run `neuro-flow run train`.

### Multiple training jobs

You can run multiple training experiments simultaneously.

```shell
neuro-flow run multitrain -s myidea-1
```

Note, this label becomes a suffix of the job name, which may contain only alphanumeric characters and hyphen `-`, and cannot end with hyphen or be longer than 40 characters. You can use suffixed job name to access the job: `neuro-flow status multitrain myidea-1`, `neuro-flow logs multitrain myidea-1` and so on.

Please, don't forget to kill the jobs you started:
- `neuro-flow kill train` to kill the training job started via `neuro-flow run train`,
- `neuro-flow kill multistrain` to kill the training job started via `neuro-flow run multitrain`,
- `neuro-flow kill jupyter` to kill the job started via `neuro-flow run jupyter`,
- ...
- `neuro-flow kill ALL` to kill all jobs started in the current project.

### Multi-threaded hyperparameter tuning

Neuro Platform supports hyperparameter tuning via [Weights & Biases](https://www.wandb.com/articles/running-hyperparameter-sweeps-to-pick-the-best-model-using-w-b).

Please refer to the corresponding [documentation](https://docs.neu.ro/toolbox/hyperparameter-tuning-with-weights-and-biases).
