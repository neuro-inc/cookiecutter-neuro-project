import textwrap
from datetime import timedelta
from typing import Awaitable, Callable

import pytest
from neuro_flow.context import JobCtx
from neuro_flow.live_runner import LiveRunner


DEFAULT_PRESET = "gpu-small-p"
DEFAULT_LIFESPAN = timedelta(days=1).total_seconds()


@pytest.mark.asyncio
async def test_volumes_found(live_runner: LiveRunner) -> None:
    names = sorted(live_runner.ctx.volumes.keys())
    assert names == ["code", "config", "data", "notebooks", "project", "results"]


@pytest.mark.asyncio
async def test_images_found(live_runner: LiveRunner) -> None:
    names = sorted(live_runner.ctx.images.keys())
    assert names == ["myimage"]


@pytest.mark.asyncio
async def test_jobs_found(live_runner: LiveRunner) -> None:
    names = sorted(live_runner.ctx.job_ids)
    assert names == [
        "develop",
        "filebrowser",
        "jupyter",
        "jupyter_lab",
        "multitrain",
        "tensorboard",
        "train",
    ]


@pytest.mark.asyncio
async def test_jobs_develop(
    live_runner: LiveRunner, get_live_job: Callable[[str], Awaitable[JobCtx]]
) -> None:
    job = await get_live_job("develop")
    assert job == JobCtx(
        title="my_project.develop",
        name=None,
        image="image:my_project/develop",
        preset=DEFAULT_PRESET,
        http_port=None,
        http_auth=None,
        entrypoint=None,
        cmd="bash",
        workdir=None,
        volumes=[
            "storage:my_project/data:/project/data:ro",
            "storage:my_project/modules:/project/modules:rw",
            "storage:my_project/config:/project/config:rw",
            "storage:my_project/results:/project/results:rw",
        ],
        life_span=DEFAULT_LIFESPAN,
        id="develop",
        detach=False,
        browse=False,
        port_forward=["2211:22"],
        multi=False,
    )


@pytest.mark.asyncio
async def test_jobs_train(
    live_runner: LiveRunner, get_live_job: Callable[[str], Awaitable[JobCtx]]
) -> None:
    job = await get_live_job("train")
    assert job == JobCtx(
        title="my_project.train",
        name=None,
        image="image:my_project/develop",
        preset=DEFAULT_PRESET,
        http_port=None,
        http_auth=None,
        entrypoint=None,
        cmd=(
            "bash -euo pipefail -c 'cd /project\n"
            "python -u /project/modules/train.py --data /project/data\n'"
        ),
        workdir=None,
        volumes=[
            "storage:my_project/data:/project/data:ro",
            "storage:my_project/modules:/project/modules:ro",
            "storage:my_project/config:/project/config:ro",
            "storage:my_project/results:/project/results:rw",
        ],
        life_span=timedelta(days=10).total_seconds(),
        id="train",
        detach=True,
        browse=False,
        port_forward=[],
        multi=False,
    )


# TODO: test_jobs_multitrain


@pytest.mark.asyncio
async def test_jobs_jupyter(
    live_runner: LiveRunner, get_live_job: Callable[[str], Awaitable[JobCtx]]
) -> None:
    job = await get_live_job("jupyter")
    assert job == JobCtx(
        title="my_project.jupyter",
        name=None,
        image="image:my_project/develop",
        preset=DEFAULT_PRESET,
        http_port=8888,
        http_auth=True,
        entrypoint=None,
        cmd=textwrap.dedent(
            """\
            jupyter notebook
              --no-browser
              --ip=0.0.0.0
              --allow-root
              --NotebookApp.token=
              --notebook-dir=/project/notebooks"""
        ),
        workdir=None,
        volumes=[
            "storage:my_project/data:/project/data:ro",
            "storage:my_project/modules:/project/modules:rw",
            "storage:my_project/config:/project/config:ro",
            "storage:my_project/notebooks:/project/notebooks:rw",
            "storage:my_project/results:/project/results:rw",
        ],
        life_span=DEFAULT_LIFESPAN,
        id="jupyter",
        detach=True,
        browse=True,
        port_forward=[],
        multi=False,
    )


@pytest.mark.asyncio
async def test_jobs_jupyter_lab(
    live_runner: LiveRunner, get_live_job: Callable[[str], Awaitable[JobCtx]]
) -> None:
    job = await get_live_job("jupyter_lab")
    assert job == JobCtx(
        title="my_project.jupyter_lab",
        name=None,
        image="image:my_project/develop",
        preset=DEFAULT_PRESET,
        http_port=8888,
        http_auth=True,
        entrypoint=None,
        cmd=textwrap.dedent(
            """\
            jupyter lab
              --no-browser
              --ip=0.0.0.0
              --allow-root
              --NotebookApp.token=
              --notebook-dir=/project/notebooks"""
        ),
        workdir=None,
        volumes=[
            "storage:my_project/data:/project/data:ro",
            "storage:my_project/modules:/project/modules:rw",
            "storage:my_project/config:/project/config:ro",
            "storage:my_project/notebooks:/project/notebooks:rw",
            "storage:my_project/results:/project/results:rw",
        ],
        life_span=DEFAULT_LIFESPAN,
        id="jupyter_lab",
        detach=True,
        browse=True,
        port_forward=[],
        multi=False,
    )


@pytest.mark.asyncio
async def test_jobs_tensorboard(
    live_runner: LiveRunner, get_live_job: Callable[[str], Awaitable[JobCtx]]
) -> None:
    job = await get_live_job("tensorboard")
    assert job == JobCtx(
        title="my_project.tensorboard",
        name=None,
        image="tensorflow/tensorflow:latest",
        preset="cpu-small",
        http_port=6006,
        http_auth=True,
        entrypoint=None,
        cmd="tensorboard --host=0.0.0.0 --logdir=/project/results",
        workdir=None,
        volumes=["storage:my_project/results:/project/results:ro"],
        life_span=DEFAULT_LIFESPAN,
        id="tensorboard",
        detach=True,
        browse=True,
        port_forward=[],
        multi=False,
    )


@pytest.mark.asyncio
async def test_jobs_filebrowser(
    live_runner: LiveRunner, get_live_job: Callable[[str], Awaitable[JobCtx]]
) -> None:
    job = await get_live_job("filebrowser")
    assert job == JobCtx(
        title="my_project.filebrowser",
        name=None,
        image="filebrowser/filebrowser:latest",
        preset="cpu-small",
        http_port=80,
        http_auth=True,
        entrypoint=None,
        cmd="--noauth",
        workdir=None,
        volumes=["storage:my_project:/srv:rw"],
        life_span=DEFAULT_LIFESPAN,
        id="filebrowser",
        detach=True,
        browse=True,
        port_forward=[],
        multi=False,
    )
