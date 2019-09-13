import typing as t

# TODO: move runners logs from tests
from tests.e2e.conftest import LOCAL_SUBMITTED_JOBS_FILE, run_command


def cleanup_jobs() -> None:
    path = LOCAL_SUBMITTED_JOBS_FILE
    print(f"Reading jobs from file: {path.absolute()}")
    jobs: t.List[str] = []
    with path.open("r") as f:
        for job in f.readlines():
            job = job.strip()
            if job:
                jobs.append(job)

    _dump_jobs("About to kill", jobs)

    killed: t.List[str] = []
    failed_to_kill: t.List[str] = []
    for job in jobs:
        try:
            print("-" * 53)

            cmd = f"neuro status {job}"
            out = run_command(cmd, detect_new_jobs=False)
            print(f"`{cmd}` => {repr(out)}")

            cmd = f"neuro kill {job}"
            out = run_command(cmd, detect_new_jobs=False)
            print(f"`{cmd}` => {repr(out)}")
            killed.append(job)

        except Exception as e:
            print(f"Failed to kill job {job}: {e}")
            failed_to_kill.append(job)

    print("=" * 53)
    _dump_jobs(f"KILLED", killed)
    _dump_jobs(f"FAILED TO KILL", failed_to_kill)
    with path.open("w"):
        path.write_text("" + "\n".join(failed_to_kill))


def _dump_jobs(message: str, jobs: t.List[str]) -> None:
    print(f"{message}: {len(jobs)} jobs:")
    for job in jobs:
        print(f"  {job}")


if __name__ == "__main__":
    cleanup_jobs()
