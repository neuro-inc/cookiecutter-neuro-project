import re
import shutil
import sys
from pathlib import Path


# >>> Handling project name
PROJECT_NAME = ""
try:
    import asyncio

    import neuro_sdk

    async def get_project_name() -> str:
        async with await neuro_sdk.get() as client:
            return client.config.project_name_or_raise

    PROJECT_NAME = asyncio.run(get_project_name())

except Exception:
    import subprocess

    if shutil.which("neuro"):
        result = subprocess.run(
            ["neuro", "config", "show"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            cli_output = result.stdout.decode().splitlines()
            for line in cli_output:
                if "current project" in line.lower():
                    PROJECT_NAME = line.split()[2]
if PROJECT_NAME:
    proj_file = Path("./.neuro/project.yml")
    content = proj_file.read_text()
    content = content.replace(
        "# project_name: {project_name}", f"project_name: {PROJECT_NAME}"
    )
    proj_file.write_text("".join(content))
else:
    live_file = Path("./.neuro/live.yml")
    content = live_file.read_text()
    content = content.replace("/$[[ project.project_name ]]/", "")
    live_file.write_text("".join(content))
# <<< Handling project name


# >>> Optionally clearing comments
COMMENTS_STRUCTURE = {
    "./.neuro/live.yml": r"(\s*#.*)",
    "./.neuro/project.yml": r"(\s*#.*)",
}
PRESERVE_HINTS_VARIANS = {
    "yes": True,
    "y": True,
    "true": True,
    "no": False,
    "n": False,
    "false": False,
}
PRESERVE_HINTS_ANSWER = (
    "{{ cookiecutter['preserve Neuro Flow template hints'] | lower }}"
)
if PRESERVE_HINTS_ANSWER not in PRESERVE_HINTS_VARIANS:
    print(
        f"ERROR: '{PRESERVE_HINTS_ANSWER}' is not a valid answer, "
        f"please select one among [{', '.join(PRESERVE_HINTS_VARIANS)}]."
    )
    sys.exit(1)
else:
    if not PRESERVE_HINTS_VARIANS[PRESERVE_HINTS_ANSWER]:
        for f_name in COMMENTS_STRUCTURE:
            f_path = Path(f_name)
            if not f_path.exists():
                print(f"WARNING: skipping comments removal from file {f_name}")
            else:
                content = f_path.read_text().splitlines(keepends=True)
                result = []
                for line in content:
                    if not re.match(COMMENTS_STRUCTURE[f_name], line):
                        result.append(line)
                f_path.write_text("".join(result))
# <<< Optionally clearing comments
