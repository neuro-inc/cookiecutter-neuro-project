# {{ cookiecutter.project_name }}

The project description is here.

## Quick Start

Sign up at [neu.ro](https://neu.ro) and setup your local machine according to [instructions](https://neu.ro/docs).
 
Then run:

```shell
neuro login
make setup
make jupyter
```
TRAIN_CMD=bash -c "cd $(PROJECT_PATH_ENV) && python -u $(CODE_DIR)/train.py --data $(DATA_DIR)"
```

See [Help.md](HELP.md) for the detailed Neuro Project Template Reference.

```
make train TRAIN_CMD="cd /project && python -u ./modules/train.py --data ./data/"
```

Notes:
- on Unix systems, if the command is wrapped with single quotes, then local `bash` won't resolve environment variables.
- On Windows, no strings can be enclosed with single quotes -- it will produce a parsing error. 


### Multiple training jobs

You can run multiple training experiments simultaneously by setting up `RUN` environment variable:
```
make train RUN=new-idea
```
Note, this label becomes a postfix of the job name, which may contain only alphanumeric characters and hyphen `-`, and cannot end with hyphen or be longer than 40 characters.

Please, don't forget to kill the jobs you started:
- `make kill-train` to kill the training job started via `make train`,
- `make kill-train RUN=new-idea` to kill the training job started via `make train RUN=new-idea`,
- `make kill-train-all` to kill all training jobs started in current project,
- `make kill-jupyter` to kill the job started via `make jupyter`,
- ...
- `make kill-all` to kill all jobs started in current project.

### Multi-threaded hyper-parameter tuning

Neuro Platform supports hyper-parameter tuning via [Weights & Biases](https://www.wandb.com/articles/running-hyperparameter-sweeps-to-pick-the-best-model-using-w-b).

To run hyper-parameter tuning for your model you need to define the list of hyper-parameters and send the metrics to WandB after each run. Your code may look as follows:

```python
import wandb

def train() -> None:
    hyperparameter_defaults = dict(
        lr=0.1,
        optimizer='sgd',
        scheduler='const'
    )
    wandb.init(config=hyperparameter_defaults)
    # your model training code here
    metrics = {'accuracy': accuracy, 'loss': loss}
    wandb.log(metrics)

if __name__ == "__main__":
    train()
```   

This list of hyper-parameters corresponds to the default configuration we provide in `{{ cookiecutter.code_directory }}/wandb-sweep.yaml` file. See [W&B documentation page](https://docs.wandb.com/library/sweeps) for more details. The name of the sweep file can be modified in `Makefile` or as environment variable `WANDB_SWEEP_FILE`.

You also need to put your WandB token in `config/wandb-token.txt` file.

After that you can run `make hypertrain`, which submits `N_HYPERPARAMETER_JOBS` (`3` by default) jobs on Neuro Platform (number of jobs can be modified in `Makefile` or as corresponding environment variable). To monitor the hyper-parameter tuning process follow the link which `wandb` provides at the beginning of the process.

To terminate all jobs of the latest hyper-parameter tuning sweep, run `make kill-hypertrain` or specify the sweep manually: `make kill-hypertrain SWEEP=sweep-id`.

All sweeps you ran are stored in the local file `.wandb_sweeps`.