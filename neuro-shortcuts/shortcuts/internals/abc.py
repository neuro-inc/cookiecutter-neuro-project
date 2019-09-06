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
    storage: StorageProject
    container: ContainerProject

    # TODO: cleanup
    SETUP_NAME: str
    TRAINING_NAME: str
    JUPYTER_NAME: str
    TENSORBOARD_NAME: str
    FILEBROWSER_NAME: str
    BASE_ENV_NAME: str
    CUSTOM_ENV_NAME: str
