# Neuro Project Template Reference

## Development environment

This template runs on the [Neuro Platform](https://neu.ro).

To dive into problem solving, you need to sign up at the [Neuro Platform](https://neu.ro) website, set up your local machine according to the [instructions](https://neu.ro/docs), and login to Neuro CLI:

```shell
neuro login
```

## Directory structure

| Local directory | Description | Storage URI | Environment mounting point |
|:--------------- |:----------- |:----------- |:-------------------------- |
| `data/` | Data | `storage:{{ cookiecutter.flow_id }}/data/` | `/{{ cookiecutter.flow_id }}/data/` |
| `{{ cookiecutter.code_directory }}/` | Python modules | `storage:{{ cookiecutter.flow_id }}/{{ cookiecutter.code_directory }}/` | `/{{ cookiecutter.flow_id }}/{{ cookiecutter.code_directory }}/` |
| `config/` | Configuration files | `storage:{{ cookiecutter.flow_id }}/config/` | `/{{ cookiecutter.flow_id }}/config/` |
| `notebooks/` | Jupyter notebooks | `storage:{{ cookiecutter.flow_id }}/notebooks/` | `/{{ cookiecutter.flow_id }}/notebooks/` |
| `results/` | Logs and results | `storage:{{ cookiecutter.flow_id }}/results/` | `/{{ cookiecutter.flow_id }}/results/` |

## Development

Follow the instructions below to set up the environment on Neuro and start a Jupyter development session.

### Setting up the development environment

```shell
neuro-flow build myimage
```
Command results:

* The `requirements.txt`, `apt.txt`, and `setup.cfg` files from the local project are uploaded to the platform storage.
* A new job is started in our [base environment](https://hub.docker.com/r/neuromation/base).
* Pip requirements from `requirements.txt` and `apt` applications from `apt.txt` are installed in the same environment.
* The updated environment is saved under a new project-dependent name to be used further on.

### Running Jupyter with GPU

```shell
neuro-flow run jupyter
```

Command results:

* The contents of the `{{ cookiecutter.code_directory }}` and `notebooks` directories are uploaded to the platform storage.
* A job with Jupyter is started, and its web interface is opened in a new window of a local web browser.

### Killing Jupyter

```shell
neuro-flow kill jupyter
```

Command results:

* The job with Jupyter Notebooks is terminated. The notebooks are saved on the platform storage. You may run `neuro-flow download notebooks` to download them to the local `notebooks/` directory.

### Memory management

If you're not using the default `neuromation/base` base image, you may want to protect the main processes in your jobs from being killed when there's not enough memory for them.

You can do this in two steps:

1. Create an `oom_guard.sh` executable file with the following contents:

```shell
#!/bin/sh

for pid in $(ps x | awk 'NR>1 {print $1}' | xargs)
 do
   if [ "$pid" != "1" ]
   then
     echo 1000 > /proc/"$pid"/oom_score_adj
   fi
 done
```

The script above tells `oom_killer` to avoid killing the process with `pid = 1` for as long as possible.

2. Add the following lines to your `Dockerfile`:

```dockerfile
COPY oom_guard.sh /root/oom_guard.sh
RUN chmod +x /root/oom_guard.sh
RUN crontab -l 2>/dev/null | { cat; echo '* * * * * /root/oom_guard.sh'; } | crontab
```

This will ensure the script from step 1 is executed every minute.

### Help

```shell
neuro-flow ps
```

Command results:

* The list of all available template jobs is printed along with their statuses.


## Data

### Uploading to the Storage via Web UI

On a local machine, run `neuro-flow run filebrowser` and open the job's URL on your mobile device or desktop.
Through a simple file explorer interface, you can upload test images and perform various file operations.

### Uploading to the Storage via CLI

On a local machine, run `neuro-flow mkvolumes`. This command creates storage folders for all defined volumes. You only need to run this once.

After the storage folders have been created, run `neuro-flow upload data` from the a local machine as well. This command pushes local files stored in `./data` into the `storage:{{ cookiecutter.flow_id }}/data` volume mounted to your development environment's `/project/data`.

You can upload (or download) every folder for which the `local` parameter is specified in the [live.yml file](./.neuro/live.yml).

### Uploading data from Google Cloud Storage to a job

Google Cloud SDK is pre-installed on all jobs produced from the base image.

Feel free to refer to the [documentation](https://docs.neu.ro/toolbox/accessing-object-storage-in-gcp) explaining how to start using GCP with the template.

### Uploading data from AWS S3 to a job

AWS CLI is pre-installed on all jobs produced from the base image.

Feel free to refer to the [documentation](https://docs.neu.ro/toolbox/accessing-object-storage-in-aws) explaining how to start using AWS with the template.

### Running a development job

If you want to debug your code on GPU, you can run a sleeping job via `neuro-flow run remote_debug` which will also open a shell to the job. You can also see job logs via `neuro-flow logs remote_debug`. The job forwards your local port 2211 to its port 22 for remote debugging.
You can find the instructions on remote debugging via PyCharm Pro in the [documentation](https://neu.ro/docs/remote_debugging_pycharm).

Please don't forget to kill your job via `neuro-flow kill remote_debug` to not waste your quota!

### Weights & Biases integration

The Neuro Platform offers easy integration with [Weights & Biases](https://www.wandb.com), an experiment tracking tool for deep learning.

Here you can find [documentation](https://docs.neu.ro/toolbox/experiment-tracking-with-weights-and-biases) for using W&B for experiment tracking with the template.

You can also refer to instructions on using Weights & Biases in your code in the [W&B documentation](https://docs.wandb.com/library/api/examples).
There are also [W&B example projects](https://github.com/wandb/examples) or an example of a Neuro Project Template-based
[ML Recipe that uses W&B as a part of the workflow](https://neu.ro/docs/cookbook/ml-recipe-hier-attention).


### Training machine types

```yaml
defaults:
  preset: gpu-small-p
```

There are several machine types available on the platform. Run `neuro config show` to see the full list. You can also override default presets for each job:

```yaml
jobs:
 train:
    image: $[[ images.myimage.ref ]]
    preset: gpu-large
    ...
```

### HTTP authentication

When jobs with an HTTP interface are executed (for example, with Jupyter Notebooks or TensorBoard), this interface requires a user to be authenticated on the platform. However, if you want to share the link with someone who is not registered on the platform, you may disable the authentication adding this argument to your job configuration:

```yaml
args:
    http_auth: "False"
```

### Storage uploads

Running `neuro-flow upload ALL` from a local machine will upload all of your code, configs, and notebooks to the storage so that these folders can be used by your jobs.

### The training command

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

After this, just run `neuro-flow run train`.

### Multiple training jobs

You can run multiple training experiments simultaneously.

```shell
neuro-flow run multitrain -s myidea-1
```

Note that this label becomes a suffix of the job name which can only contain alphanumeric characters and hyphens `-`, cannot end with a hyphen, and cannot be longer than 40 characters. You can use suffixed job names to access jobs: `neuro-flow status multitrain myidea-1`, `neuro-flow logs multitrain myidea-1`, and so on.

Please don't forget to kill the jobs you started:
- `neuro-flow kill train` to kill the training job started via `neuro-flow run train`,
- `neuro-flow kill multitrain` to kill the training job started via `neuro-flow run multitrain`,
- `neuro-flow kill jupyter` to kill the job started via `neuro-flow run jupyter`,
- ...
- `neuro-flow kill ALL` to kill all jobs started in the current project.

### Multi-threaded hyperparameter tuning

The Neuro Platform supports hyperparameter tuning via [Weights & Biases](https://www.wandb.com/articles/running-hyperparameter-sweeps-to-pick-the-best-model-using-w-b).

Please refer to the corresponding [documentation](https://docs.neu.ro/toolbox/hyperparameter-tuning-with-weights-and-biases) for more information.
