from .utils import run


CODE_PATH = "__test_project"
DATA_PATH = "data"
NOTEBOOKS_PATH = "notebooks"
REQUIREMENTS_PATH = "requirements"
RESULTS_PATH = "results"
PROJECT_PATH_STORAGE = "storage:__test_project"  # TODO : <- change htis value
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


##### SETUP #####


def setup():
    run(f"neuro kill {SETUP_NAME}")
    cmd = (
        f"neuro run --name {SETUP_NAME} --preset cpu-small --detach "
        f"--volume {PROJECT_PATH_STORAGE}:{PROJECT_PATH_ENV}:ro "
        f"{BASE_ENV_NAME} 'tail -f /dev/null'"  # TODO: must be 'sleep 1h'
    )
    run(cmd)
    run(f"neuro cp -r {REQUIREMENTS_PATH} {REQUIREMENTS_PATH_STORAGE}")
    # For some reason the second command fail
    # neuro exec {SETUP_NAME} 'apt-get update'
    # neuro exec {SETUP_NAME} 'cat {REQUIREMENTS_PATH_ENV}/apt.txt | xargs apt-get install -y'
    run(f"neuro exec {SETUP_NAME} 'pip install -r {REQUIREMENTS_PATH_ENV}/pip.txt'")
    run(f"neuro job save {SETUP_NAME} {CUSTOM_ENV_NAME}")
    run(f"neuro kill {SETUP_NAME}")


##### STORAGE #####


def upload_code():
    run(f"neuro cp -r -T {CODE_PATH} {CODE_PATH_STORAGE}")


def clean_code():
    run(f"neuro rm -r {CODE_PATH_STORAGE}")


def upload_data():
    run(f"neuro storage load -p -u -T {DATA_PATH} {DATA_PATH_STORAGE}")


def clean_data():
    run(f"neuro rm -r {DATA_PATH_STORAGE}")


def upload_notebooks():
    run(f"neuro cp -r -T {NOTEBOOKS_PATH} {NOTEBOOKS_PATH_STORAGE}")


def download_notebooks():
    run(f"neuro cp -r {NOTEBOOKS_PATH_STORAGE} {NOTEBOOKS_PATH}")


def clean_notebooks():
    run(f"neuro rm -r {NOTEBOOKS_PATH_STORAGE}")


def upload():
    upload_code()
    upload_data()
    upload_notebooks()


def clean():
    clean_code()
    clean_data()
    clean_notebooks()


##### JOBS #####


def run_training():
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


def kill_training():
    run(f"neuro kill {TRAINING_NAME}")


def connect_training():
    run(f"neuro exec {TRAINING_NAME} bash")


def run_jupyter():
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


def kill_jupyter():
    run(f"neuro kill {JUPYTER_NAME}")


def run_tensorboard():
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


def kill_tensorboard():
    run(f"neuro kill {TENSORBOARD_NAME}")


def run_filebrowser():
    run(
        f"neuro run "
        f"--name {FILEBROWSER_NAME} "
        f"--preset cpu-small "
        f"--http 80 --no-http-auth --detach "
        f"--volume {PROJECT_PATH_STORAGE}:/srv:rw "
        f"filebrowser/filebrowser"
    )
    run(f"neuro job browse {FILEBROWSER_NAME}")


def kill_filebrowser():
    run(f"neuro kill {FILEBROWSER_NAME}")


def kill():
    kill_training()
    kill_jupyter()
    kill_tensorboard()
    kill_filebrowser()


##### LOCAL #####


def setup_local():
    run("pip install -r requirements/pip.txt")


def lint():
    run("flake8 .")
    run("mypy .")


def install():
    run("python setup.py install --user")


##### MISC #####


def ps():
    run(f"neuro ps")


if __name__ == "__main__":
    setup()
