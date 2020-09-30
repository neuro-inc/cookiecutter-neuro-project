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
make setup
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

* The job with Jupyter Notebooks is terminated. The notebooks are saved on the platform storage. You may run `make download-notebooks` to download them to the local `notebooks/` directory.
