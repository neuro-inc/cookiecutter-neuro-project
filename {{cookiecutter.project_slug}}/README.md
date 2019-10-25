# {{ cookiecutter.project_name }}

# Description

This project is created from 
[Neuro Platform Project Template](https://github.com/neuromation/cookiecutter-neuro-project).

# Development Environment

This project is designed to run on [Neuro Platform](https://neu.ro), so you can jump into problem-solving right away.

## Directory Structure

| Mount Point                                  | Description           | Storage URI                                                                  |
|:-------------------------------------------- |:--------------------- |:---------------------------------------------------------------------------- |
|`{{ cookiecutter.project_slug }}/data/`                              | Data                  | `storage:{{ cookiecutter.project_slug }}/data/`                              |
|`{{ cookiecutter.project_slug }}/{{ cookiecutter.code_directory }}/` | Python modules        | `storage:{{ cookiecutter.project_slug }}/{{ cookiecutter.code_directory }}/` |
|`{{ cookiecutter.project_slug }}/notebooks/`                         | Jupyter notebooks     | `storage:{{ cookiecutter.project_slug }}/notebooks/`                         |
|`{{ cookiecutter.project_slug }}/results/`                           | Logs and results      | `storage:{{ cookiecutter.project_slug }}/results/`                           |

## Development

Follow the instructions below in order to setup the environment and start Jupyter development session.

## Neuro Platform

* Setup development environment `make setup`
* Run Jupyter with GPU: `make jupyter`
* Kill Jupyter: `make kill-jupyter`
* Get the list of available template commands: `make help`

# Data

## Uploading via Web UI

On local machine run `make filebrowser` and open job's URL on your mobile device or desktop.
Through a simple file explorer interface you can upload test images and perform file operations.

## Uploading via CLI

On local machine run `make upload-data`. This command pushes local files stored in `./data`
into `storage:{{ cookiecutter.project_slug }}/data` mounted to your development environment's `/project/data`.
