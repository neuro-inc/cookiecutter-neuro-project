#!/usr/bin/env python

from invoke import task as task


PROJECT_NAME = "{{cookiecutter.project_slug}}"

CODE_PATH = PROJECT_NAME
DATA_PATH = "data"
NOTEBOOKS_PATH = "notebooks"
REQUIREMENTS_PATH = "requirements"
RESULTS_PATH = "results"
PROJECT_PATH_STORAGE = f"storage:{PROJECT_NAME}"
CODE_PATH_STORAGE = f"{PROJECT_PATH_STORAGE}/{CODE_PATH}"
DATA_PATH_STORAGE = f"{PROJECT_PATH_STORAGE}/{DATA_PATH}"
NOTEBOOKS_PATH_STORAGE = f"{PROJECT_PATH_STORAGE}/{NOTEBOOKS_PATH}"
REQUIREMENTS_PATH_STORAGE = f"{PROJECT_PATH_STORAGE}/{REQUIREMENTS_PATH}"
RESULTS_PATH_STORAGE = f"{PROJECT_PATH_STORAGE}/{RESULTS_PATH}"

PROJECT_PATH_ENV = "/project"
CODE_PATH_ENV = f"{PROJECT_PATH_ENV}/{CODE_PATH}"
DATA_PATH_ENV = f"{PROJECT_PATH_ENV}/{DATA_PATH}"
NOTEBOOKS_PATH_ENV = f"{PROJECT_PATH_ENV}/{NOTEBOOKS_PATH}"
REQUIREMENTS_PATH_ENV = f"{PROJECT_PATH_ENV}/{REQUIREMENTS_PATH}"
RESULTS_PATH_ENV = f"{PROJECT_PATH_ENV}/{RESULTS_PATH}"

SETUP_NAME = "setup"
TRAINING_NAME = "training"
JUPYTER_NAME = "jupyter"
TENSORBOARD_NAME = "tensorboard"
FILEBROWSER_NAME = "filebrowser"

BASE_ENV_NAME = "image:neuro/base"
CUSTOM_ENV_NAME = "image:neuro/custom"


#  ##### SETUP #####


@task
def help(context):
    context.run("invoke --list")


@task
def setup(context):
    """ This is documentation for setup
    """
    context.run(f"neuro kill {SETUP_NAME}")
    command = "sleep 1h"
    context.run(
        f"neuro run --name {SETUP_NAME} --preset cpu-small --detach "
        f"--volume {PROJECT_PATH_STORAGE}:{PROJECT_PATH_ENV}:ro "
        f"{BASE_ENV_NAME} '{command}'"
    )
    context.run(f"neuro cp -r {REQUIREMENTS_PATH} {REQUIREMENTS_PATH_STORAGE}")
    # TODO: fix commands below
    # For some reason the second command fail
    # neuro exec {SETUP_NAME} 'apt-get update'
    # neuro exec {SETUP_NAME} 'cat {REQUIREMENTS_PATH_ENV}/apt.txt | xargs apt-get install -y'  # noqa
    context.run(
        f"neuro exec {SETUP_NAME} 'pip install -r {REQUIREMENTS_PATH_ENV}/pip.txt'"
    )
    context.run(f"neuro job save {SETUP_NAME} {CUSTOM_ENV_NAME}")
    context.run(f"neuro kill {SETUP_NAME}")


#  ##### STORAGE #####


@task
def upload_code(context):
    context.run(f"neuro cp -r -T {CODE_PATH} {CODE_PATH_STORAGE}")


@task
def clean_code(context):
    context.run(f"neuro rm -r {CODE_PATH_STORAGE}")


@task
def upload_data(context):
    context.run(f"neuro storage load -p -u -T {DATA_PATH} {DATA_PATH_STORAGE}")


@task
def clean_data(context):
    context.run(f"neuro rm -r {DATA_PATH_STORAGE}")


@task
def upload_notebooks(context):
    context.run(f"neuro cp -r -T {NOTEBOOKS_PATH} {NOTEBOOKS_PATH_STORAGE}")


@task
def download_notebooks(context):
    context.run(f"neuro cp -r {NOTEBOOKS_PATH_STORAGE} {NOTEBOOKS_PATH}")


@task
def clean_notebooks(context):
    context.run(f"neuro rm -r {NOTEBOOKS_PATH_STORAGE}")


@task
def upload(context):
    upload_code()
    upload_data()
    upload_notebooks()


@task
def clean(context):
    clean_code()
    clean_data()
    clean_notebooks()


#  ##### JOBS #####


@task
def training(context):
    cmd = (
        f"python {CODE_PATH_ENV}/train.py --log_dir "
        f"{RESULTS_PATH_ENV} --data_root {DATA_PATH_ENV}/cifar10"
    )
    context.run(
        f"neuro context.run --name {TRAINING_NAME} --preset gpu-small "
        f"--volume {DATA_PATH_STORAGE}:{DATA_PATH_ENV}:ro "
        f"--volume {CODE_PATH_STORAGE}:{CODE_PATH_ENV}:ro "
        f"--volume {RESULTS_PATH_STORAGE}:{RESULTS_PATH_ENV}:rw "
        f"{CUSTOM_ENV_NAME} "
        f"'{cmd}'"
    )


@task
def kill_training(context):
    context.run(f"neuro kill {TRAINING_NAME}")


@task
def connect_training(context):
    context.run(f"neuro exec {TRAINING_NAME} bash")


@task
def jupyter(context):
    cmd = (
        f"jupyter notebook --no-browser --ip=0.0.0.0 --allow-root "
        f"--NotebookApp.token= --notebook-dir={NOTEBOOKS_PATH_ENV}"
    )
    context.run(
        f"neuro context.run "
        f"--name {JUPYTER_NAME} "
        f"--preset gpu-small "
        f"--http 8888 --no-http-auth --detach "
        f"--volume {DATA_PATH_STORAGE}:{DATA_PATH_ENV}:ro "
        f"--volume {CODE_PATH_STORAGE}:{CODE_PATH_ENV}:rw "
        f"--volume {NOTEBOOKS_PATH_STORAGE}:{NOTEBOOKS_PATH_ENV}:rw "
        f"--volume {RESULTS_PATH_STORAGE}:{RESULTS_PATH_ENV}:rw "
        f"{CUSTOM_ENV_NAME} "
        f"'{cmd}'"
    )
    context.run(f"neuro job browse {JUPYTER_NAME}")


@task
def kill_jupyter(context):
    context.run(f"neuro kill {JUPYTER_NAME}")


@task
def tensorboard(context):
    cmd = f"tensorboard --logdir={RESULTS_PATH_ENV}"
    context.run(
        f"neuro context.run "
        f"--name {TENSORBOARD_NAME} "
        f"--preset cpu-small "
        f"--http 6006 --no-http-auth --detach "
        f"--volume {RESULTS_PATH_STORAGE}:{RESULTS_PATH_ENV}:ro "
        f"{CUSTOM_ENV_NAME} "
        f"'{cmd}'"
    )
    context.run(f"neuro job browse {TENSORBOARD_NAME}")


@task
def kill_tensorboard(context):
    context.run(f"neuro kill {TENSORBOARD_NAME}")


@task
def filebrowser(context):
    context.run(
        f"neuro context.run "
        f"--name {FILEBROWSER_NAME} "
        f"--preset cpu-small "
        f"--http 80 --no-http-auth --detach "
        f"--volume {PROJECT_PATH_STORAGE}:/srv:rw "
        f"filebrowser/filebrowser"
    )
    context.run(f"neuro job browse {FILEBROWSER_NAME}")


@task
def kill_filebrowser(context):
    context.run(f"neuro kill {FILEBROWSER_NAME}")


@task(pre=[kill_training, kill_jupyter, kill_tensorboard, kill_filebrowser])
def kill(context):
    pass


#  ##### LOCAL #####


@task
def setup_local(context):
    context.run("pip install -r requirements/pip.txt")


@task
def lint(context):
    context.run("flake8 .")
    context.run("mypy .")


@task
def install(context):
    context.run("python setup.py install --user")


#  ##### MISC #####


@task
def ps(context):
    context.run(f"neuro ps")
