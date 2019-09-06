from .internals.abc import Config, StorageProject, LocalProject, ContainerProject

SETUP_NAME = "setup"
TRAINING_NAME = "training"
JUPYTER_NAME = "jupyter"
TENSORBOARD_NAME = "tensorboard"
FILEBROWSER_NAME = "filebrowser"
BASE_ENV_NAME = "image:neuro/base"
CUSTOM_ENV_NAME = "image:neuro/custom"


def create_config(project_name: str) -> Config:
    return Config(
        local=LocalProject(),
        storage=StorageProject(project_name),
        container=ContainerProject(),
        SETUP_NAME=SETUP_NAME,
        TRAINING_NAME=TRAINING_NAME,
        JUPYTER_NAME=JUPYTER_NAME,
        TENSORBOARD_NAME=TENSORBOARD_NAME,
        FILEBROWSER_NAME=FILEBROWSER_NAME,
        BASE_ENV_NAME=BASE_ENV_NAME,
        CUSTOM_ENV_NAME=CUSTOM_ENV_NAME,
    )