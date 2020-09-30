import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable, Iterator

import pytest
from neuro_flow.context import JobCtx
from neuro_flow.live_runner import LiveRunner
from neuro_flow.parser import ConfigDir, ConfigPath, find_live_config


@contextmanager
def inside_dir(dirpath: str) -> Iterator[None]:
    """
    Execute code from inside the given directory
    :param dirpath: String, path of the directory the command is being run.
    """
    old_path = os.getcwd()
    try:
        os.chdir(dirpath)
        yield
    finally:
        os.chdir(old_path)


@pytest.fixture
def project_path(cookies: Any) -> Path:
    result = cookies.bake(extra_context={"project_slug": "my-project"})
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project.basename == "my-project"
    return Path(result.project)


@pytest.fixture
def live_config_path(project_path: Path) -> ConfigPath:
    return find_live_config(ConfigDir(project_path, project_path / ".neuro"))


@pytest.fixture
async def live_runner(live_config_path: ConfigPath) -> AsyncIterator[LiveRunner]:
    config = live_config_path
    async with LiveRunner(config.workspace, config.config_file) as runner:
        yield runner


@pytest.fixture
async def get_live_job(live_runner: LiveRunner) -> Callable[[str], Awaitable[JobCtx]]:
    async def _f(name: str) -> JobCtx:
        is_multi = await live_runner.ctx.is_multi(name)
        assert not is_multi
        meta_ctx = await live_runner._ensure_meta(name, suffix=None)
        job_ctx = await meta_ctx.with_job(name)
        return job_ctx.job

    return _f


@pytest.fixture
def get_live_multi_job() -> None:
    raise NotImplementedError
