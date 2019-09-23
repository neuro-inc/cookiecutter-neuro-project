# {{ cookiecutter.project_name }}

# Description

{{ cookiecutter.project_short_description }}

Created by {{ cookiecutter.full_name }} ({{ cookiecutter.email }})

# Development Environment

This project is designed to run on [Neuro Platform](https://neu.ro), so you can jump into problem-solving right away.

## Directory Structure

| Mount Point                                  | Description           | Storage URI                                                                  |
|:-------------------------------------------- |:--------------------- |:---------------------------------------------------------------------------- |
|`/project/data/`                              | Data                  | `storage:{{ cookiecutter.project_slug }}/data/`                              |
|`/project/{{ cookiecutter.code_directory }}/` | Python modules        | `storage:{{ cookiecutter.project_slug }}/{{ cookiecutter.code_directory }}/` |
|`/project/notebooks/`                         | Jupyter notebooks     | `storage:{{ cookiecutter.project_slug }}/notebooks/`                         |
|`/project/results/`                           | Logs and results      | `storage:{{ cookiecutter.project_slug }}/results/`                           |

## Development

Follow the instructions below to setup the environment and start Jupyter development session.

## Neuro Platform

* Setup development environment `make setup`
* Run Jupyter with GPU: `make jupyter`
* Kill Jupyter: `make kill_jupyter`

# Data

## Uploading via Web UI

From local machine run `make filebrowser` and open job's URL from your mobile device or desktop. 
Through a simple file explorer interface you can upload test images and perform file operations.

## Uploading via CLI

From local machine run `make upload_data`. This will push local files stored in `./data` 
into `storage:{{ cookiecutter.project_slug }}/data` mounted to your development environment's `/project/data`.
