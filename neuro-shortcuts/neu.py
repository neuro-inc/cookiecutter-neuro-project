#!/usr/bin/env python

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


def setup():
    run(f"neuro kill {SETUP_NAME}", assert_success=False)
    command = "sleep 1h"
    run(
        f"neuro run --name {SETUP_NAME} --preset cpu-small --detach "
        f"--volume {PROJECT_PATH_STORAGE}:{PROJECT_PATH_ENV}:ro "
        f"{BASE_ENV_NAME} '{command}'"
    )
    run(f"neuro cp -r {REQUIREMENTS_PATH} {REQUIREMENTS_PATH_STORAGE}")
    # TODO: fix commands below
    # For some reason the second command fail
    # neuro exec {SETUP_NAME} 'apt-get update'
    # neuro exec {SETUP_NAME} 'cat {REQUIREMENTS_PATH_ENV}/apt.txt | xargs apt-get install -y'  # noqa
    run(f"neuro exec {SETUP_NAME} 'pip install -r {REQUIREMENTS_PATH_ENV}/pip.txt'")
    run(f"neuro job save {SETUP_NAME} {CUSTOM_ENV_NAME}")
    run(f"neuro kill {SETUP_NAME}", assert_success=False)


#  ##### STORAGE #####


def upload_code() -> None:
    run(f"neuro cp -r -T {CODE_PATH} {CODE_PATH_STORAGE}")


def clean_code() -> None:
    run(f"neuro rm -r {CODE_PATH_STORAGE}")


def upload_data() -> None:
    run(f"neuro storage load -p -u -T {DATA_PATH} {DATA_PATH_STORAGE}")


def clean_data() -> None:
    run(f"neuro rm -r {DATA_PATH_STORAGE}")


def upload_notebooks() -> None:
    run(f"neuro cp -r -T {NOTEBOOKS_PATH} {NOTEBOOKS_PATH_STORAGE}")


def download_notebooks() -> None:
    run(f"neuro cp -r {NOTEBOOKS_PATH_STORAGE} {NOTEBOOKS_PATH}")


def clean_notebooks() -> None:
    run(f"neuro rm -r {NOTEBOOKS_PATH_STORAGE}")


def upload() -> None:
    upload_code()
    upload_data()
    upload_notebooks()


def clean() -> None:
    clean_code()
    clean_data()
    clean_notebooks()


#  ##### JOBS #####


def training() -> None:
    cmd = (
        f"python {CODE_PATH_ENV}/train.py --log_dir "
        f"{RESULTS_PATH_ENV} --data_root {DATA_PATH_ENV}/cifar10"
    )
    run(
        f"neuro run --name {TRAINING_NAME} --preset gpu-small "
        f"--volume {DATA_PATH_STORAGE}:{DATA_PATH_ENV}:ro "
        f"--volume {CODE_PATH_STORAGE}:{CODE_PATH_ENV}:ro "
        f"--volume {RESULTS_PATH_STORAGE}:{RESULTS_PATH_ENV}:rw "
        f"{CUSTOM_ENV_NAME} "
        f"'{cmd}'"
    )


def kill_training() -> None:
    run(f"neuro kill {TRAINING_NAME}")


def connect_training() -> None:
    run(f"neuro exec {TRAINING_NAME} bash")


def jupyter() -> None:
    cmd = (
        f"jupyter notebook --no-browser --ip=0.0.0.0 --allow-root "
        f"--NotebookApp.token= --notebook-dir={NOTEBOOKS_PATH_ENV}"
    )
    run(
        f"neuro run "
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
    run(f"neuro job browse {JUPYTER_NAME}")


def kill_jupyter() -> None:
    run(f"neuro kill {JUPYTER_NAME}")


def tensorboard() -> None:
    cmd = f"tensorboard --logdir={RESULTS_PATH_ENV}"
    run(
        f"neuro run "
        f"--name {TENSORBOARD_NAME} "
        f"--preset cpu-small "
        f"--http 6006 --no-http-auth --detach "
        f"--volume {RESULTS_PATH_STORAGE}:{RESULTS_PATH_ENV}:ro "
        f"{CUSTOM_ENV_NAME} "
        f"'{cmd}'"
    )
    run(f"neuro job browse {TENSORBOARD_NAME}")


def kill_tensorboard() -> None:
    run(f"neuro kill {TENSORBOARD_NAME}")


def filebrowser() -> None:
    run(
        f"neuro run "
        f"--name {FILEBROWSER_NAME} "
        f"--preset cpu-small "
        f"--http 80 --no-http-auth --detach "
        f"--volume {PROJECT_PATH_STORAGE}:/srv:rw "
        f"filebrowser/filebrowser"
    )
    run(f"neuro job browse {FILEBROWSER_NAME}")


def kill_filebrowser() -> None:
    run(f"neuro kill {FILEBROWSER_NAME}")


def kill() -> None:
    kill_training()
    kill_jupyter()
    kill_tensorboard()
    kill_filebrowser()


#  ##### LOCAL #####


def setup_local() -> None:
    run("pip install -r requirements/pip.txt")


def lint() -> None:
    run("flake8 .")
    run("mypy .")


def install() -> None:
    run("python setup.py install --user")


#  ##### MISC #####


def ps() -> None:
    run(f"neuro ps")


#  ############################# INTERNALS BELOW ##############################

RESERVED_ACTION_NAMES = ("run", "main")


def run(cmd: str, assert_success: bool = True) -> None:
    # local import so that only user-defined actions are declared in this file
    import shlex
    import subprocess
    import sys

    DEFAULT_TIMEOUT = 5 * 60

    print(f"Runing command: '{cmd}'")
    args = shlex.split(cmd)
    proc = subprocess.run(
        args,
        timeout=DEFAULT_TIMEOUT,
        encoding="utf8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(proc.stdout)
    if assert_success:
        try:
            proc.check_returncode()
        except subprocess.CalledProcessError:
            sys.stderr.write(f"ERROR: {proc.stderr}")
            exit(proc.returncode)


def main() -> None:
    # local import so that only user-defined actions are declared in this file
    from argparse import ArgumentParser
    import importlib
    import sys
    import typing as t

    def collect_entrypoints(module_name: str) -> t.Dict[str, t.Callable[[], None]]:
        """ collect all callable object from module `module_name`
        whose names start with a lowerase english alphabet character
        """
        importlib.import_module(module_name)
        module = sys.modules[module_name]
        result: t.Dict[str, t.Callable] = {}
        for name in dir(module):
            if "a" <= name[0] <= "z" and name not in RESERVED_ACTION_NAMES:
                obj = getattr(module, name)
                if callable(obj):
                    result[name] = obj
        return result

    def create_parser() -> ArgumentParser:
        parser = ArgumentParser(description="Neuromation shortcuts script")
        parser.add_argument(
            "action",
            metavar="ACTION",
            type=str,
            help="Shortcut action (`help` for help)",
        )
        return parser

    parser = create_parser()
    args = parser.parse_args()
    action_name = args.action

    module_name = __name__
    entrypoints = collect_entrypoints(module_name)
    action = entrypoints.get(action_name)

    help_message = f"Available actions: {', '.join(entrypoints.keys())}"
    if action_name == "help":
        # TODO: add help messages
        print(help_message)
        return

    if not action:
        print(f"ERROR: Cannot find action '{action_name}'")
        print()
        exit(1)

    try:
        action()
    except (TypeError, AttributeError) as e:
        sys.stderr.write(f"ERROR: Could not execute action '{action_name}': {e}")
        exit(2)


if __name__ == "__main__":
    main()
