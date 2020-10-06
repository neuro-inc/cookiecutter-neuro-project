from datetime import timedelta

import pytest
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
