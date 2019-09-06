from ._internals.abc import Config
from ._internals.runner import run


##### SETUP #####


def setup(cfg: Config):
    run(f"neuro kill {cfg.SETUP_NAME}")
    cmd = (
        f"neuro run --name {cfg.SETUP_NAME} --preset cpu-small --detach "
        f"--volume {cfg.storage.root}:{cfg.container.root}:ro "
        f"{cfg.BASE_ENV_NAME} 'tail -f /dev/null'"  # TODO: must be 'sleep 1h'
    )
    run(cmd)
    run(f"neuro cp -r {cfg.local.requirements} {cfg.storage.requirements}")
    # TODO: see below
    # For some reason the second command fail
    # neuro exec {cfg.SETUP_NAME} 'apt-get update'
    # neuro exec {cfg.SETUP_NAME} 'cat {REQUIREMENTS_PATH_ENV}/apt.txt | xargs apt-get install -y'
    run(
        f"neuro exec {cfg.SETUP_NAME} 'pip install -r {cfg.container.requirements}/pip.txt'"
    )
    run(f"neuro job save {cfg.SETUP_NAME} {cfg.CUSTOM_ENV_NAME}")
    run(f"neuro kill {cfg.SETUP_NAME}")


##### STORAGE #####


def upload_code(cfg: Config) -> None:
    run(f"neuro cp -r -T {cfg.local.code} {cfg.container.code}")


# TODO: redundant? clean where? locally?
def clean_code(cfg: Config) -> None:
    # run(f"neuro rm -r {CODE_PATH_STORAGE}")
    raise NotImplemented()


def upload_data(cfg: Config) -> None:
    # run(f"neuro storage load -p -u -T {DATA_PATH} {DATA_PATH_STORAGE}")
    raise NotImplemented()


def clean_data(cfg: Config) -> None:
    # run(f"neuro rm -r {DATA_PATH_STORAGE}")
    raise NotImplemented()


def upload_notebooks(cfg: Config) -> None:
    # run(f"neuro cp -r -T {NOTEBOOKS_PATH} {NOTEBOOKS_PATH_STORAGE}")
    raise NotImplemented()


def download_notebooks(cfg: Config) -> None:
    # run(f"neuro cp -r {NOTEBOOKS_PATH_STORAGE} {NOTEBOOKS_PATH}")
    raise NotImplemented()


def clean_notebooks(cfg: Config) -> None:
    # run(f"neuro rm -r {NOTEBOOKS_PATH_STORAGE}")
    raise NotImplemented()


def upload(cfg: Config) -> None:
    # upload_code()
    # upload_data()
    # upload_notebooks()
    raise NotImplemented()


def clean(cfg: Config) -> None:
    # clean_code()
    # clean_data()
    # clean_notebooks()
    raise NotImplemented()


##### JOBS #####


def run_training(cfg: Config) -> None:
    # cmd = (
    #     f"python {CODE_PATH_ENV}/train.py --log_dir "
    #     f"{RESULTS_PATH_ENV} --data_root {DATA_PATH_ENV}/cifar10"
    # )
    # run(
    #     f"neuro run --name {cfg.TRAINING_NAME} --preset gpu-small "
    #     f"--volume {DATA_PATH_STORAGE}:{DATA_PATH_ENV}:ro "
    #     f"--volume {CODE_PATH_STORAGE}:{CODE_PATH_ENV}:ro "
    #     f"--volume {RESULTS_PATH_STORAGE}:{RESULTS_PATH_ENV}:rw "
    #     f"{cfg.CUSTOM_ENV_NAME} "
    #     f"'{cmd}'"
    # )
    raise NotImplemented()


def kill_training(cfg: Config) -> None:
    # run(f"neuro kill {cfg.TRAINING_NAME}")
    raise NotImplemented()


def connect_training(cfg: Config) -> None:
    # run(f"neuro exec {cfg.TRAINING_NAME} bash")
    raise NotImplemented()


def run_jupyter(cfg: Config) -> None:
    # cmd = (
    #     f"jupyter notebook --no-browser --ip=0.0.0.0 --allow-root "
    #     f"--NotebookApp.token= --notebook-dir={NOTEBOOKS_PATH_ENV}"
    # )
    # run(
    #     f"neuro run "
    #     f"--name {cfg.JUPYTER_NAME} "
    #     f"--preset gpu-small "
    #     f"--http 8888 --no-http-auth --detach "
    #     f"--volume {DATA_PATH_STORAGE}:{DATA_PATH_ENV}:ro "
    #     f"--volume {CODE_PATH_STORAGE}:{CODE_PATH_ENV}:rw "
    #     f"--volume {NOTEBOOKS_PATH_STORAGE}:{NOTEBOOKS_PATH_ENV}:rw "
    #     f"--volume {RESULTS_PATH_STORAGE}:{RESULTS_PATH_ENV}:rw "
    #     f"{cfg.CUSTOM_ENV_NAME} "
    #     f"'{cmd}'"
    # )
    # run(f"neuro job browse {cfg.JUPYTER_NAME}")
    raise NotImplemented()


def kill_jupyter(cfg: Config) -> None:
    # run(f"neuro kill {cfg.JUPYTER_NAME}")
    raise NotImplemented()


def run_tensorboard(cfg: Config) -> None:
    # cmd = f"tensorboard --logdir={RESULTS_PATH_ENV}"
    # run(
    #     f"neuro run "
    #     f"--name {cfg.TENSORBOARD_NAME} "
    #     f"--preset cpu-small "
    #     f"--http 6006 --no-http-auth --detach "
    #     f"--volume {RESULTS_PATH_STORAGE}:{RESULTS_PATH_ENV}:ro "
    #     f"{cfg.CUSTOM_ENV_NAME} "
    #     f"'{cmd}'"
    # )
    # run(f"neuro job browse {cfg.TENSORBOARD_NAME}")
    raise NotImplemented()


def kill_tensorboard(cfg: Config) -> None:
    # run(f"neuro kill {cfg.TENSORBOARD_NAME}")
    raise NotImplemented()


def run_filebrowser(cfg: Config) -> None:
    # run(
    #     f"neuro run "
    #     f"--name {cfg.FILEBROWSER_NAME} "
    #     f"--preset cpu-small "
    #     f"--http 80 --no-http-auth --detach "
    #     f"--volume {PROJECT_PATH_STORAGE}:/srv:rw "
    #     f"filebrowser/filebrowser"
    # )
    # run(f"neuro job browse {cfg.FILEBROWSER_NAME}")
    raise NotImplemented()


def kill_filebrowser(cfg: Config) -> None:
    # run(f"neuro kill {cfg.FILEBROWSER_NAME}")
    raise NotImplemented()


def kill(cfg: Config) -> None:
    # kill_training()
    # kill_jupyter()
    # kill_tensorboard()
    # kill_filebrowser()
    raise NotImplemented()


##### LOCAL #####


def setup_local(cfg: Config) -> None:
    # run("pip install -r requirements/pip.txt")
    raise NotImplemented()


def lint(cfg: Config) -> None:
    # run("flake8 .")
    # run("mypy .")
    raise NotImplemented()


def install(cfg: Config) -> None:
    # run("python setup.py install --user")
    raise NotImplemented()


##### MISC #####


def ps(cfg: Config) -> None:
    # run(f"neuro ps")
    raise NotImplemented()


if __name__ == "__main__":
    setup()
