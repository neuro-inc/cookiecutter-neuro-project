import typing as t

from tests.conftest import get_submitted_jobs_file, run_once


def cleanup_jobs() -> None:
    path = get_submitted_jobs_file()
    print(f"Reading jobs from file: {path.absolute()}")
    jobs: t.List[str] = []
    with path.open() as f:
        for job in f.readlines():
            job = job.strip()
            if job:
                jobs.append(job)

    print(f"About to kill {len(jobs)} jobs:\n")
    for job in jobs:
        print(f"  {job}")

    failed_to_kill: t.List[str] = []
    for job in jobs:
        try:
            print("-" * 53)
            cap = run_once(f"neuro status {job}")
            print(f"stderr: `{cap.err}`")
            print(f"stdout: `{cap.out}`")
            print()
            print(f"Killing job: {job}")
            cap = run_once(f"neuro kill {job}")
            print(f"stderr: `{cap.err}`")
            print(f"stdout: `{cap.out}`")
        except Exception as e:
            print(f"FAILED TO KILL {job}: {e}")
            failed_to_kill.append(job)
    with path.open("w"):
        path.write_text("\n".join(failed_to_kill))


if __name__ == "__main__":
    cleanup_jobs()
