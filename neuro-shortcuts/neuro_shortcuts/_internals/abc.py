import abc
from dataclasses import dataclass


class Project(abc.ABC):
    @abc.abstractmethod
    def root(self) -> str:
        pass

    @property
    def data(self) -> str:
        return f"{self.root}/data"

    @property
    def code(self) -> str:
        return f"{self.root}/code"

    @property
    def notebooks(self) -> str:
        return f"{self.root}/notebooks"

    @property
    def requirements(self) -> str:
        return f"{self.root}/requirements"

    @property
    def results(self) -> str:
        return f"{self.root}/results"


class StorageProject(Project):
    def __init__(self, project_name: str) -> None:
        self._project_name = project_name

    def root(self) -> str:
        return f"storage:{self._project_name}"


class LocalProject(Project):
    def __init__(self):
        # TODO (artem) remember `pwd` as `self._project_path`
        pass

    def root(self) -> str:
        # TODO: return self._project_path
        raise NotImplemented()


class ContainerProject(Project):
    def root(self) -> str:
        # TODO: always in the root?
        return "/project"


@dataclass
class Config:
    local: LocalProject
    storage: LocalProject
    container: LocalProject

    # TODO
    SETUP_NAME = "setup"
    TRAINING_NAME = "training"
    JUPYTER_NAME = "jupyter"
    TENSORBOARD_NAME = "tensorboard"
    FILEBROWSER_NAME = "filebrowser"
    BASE_ENV_NAME = "image:neuro/base"
    CUSTOM_ENV_NAME = "image:neuro/custom"
