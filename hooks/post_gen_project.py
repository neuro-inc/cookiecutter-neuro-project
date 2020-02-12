import uuid
import re
import sys

from pathlib import Path

project_id = f"neuro-project-{uuid.uuid4().hex[:8]}"

makefile_path = Path("Makefile")

text = makefile_path.read_text()
text = re.sub(r"PROJECT_ID=placeholder", f"PROJECT_ID={project_id}", text)

if sys.platform in ["win32", "cygwin"]:
    # This is a workaround of the problem on Windows where some paths storing
    # in env vars and starting with a single slash '/' are for some reason
    # resolved to a local path 'C:\Users\...
    # So on Windows, some paths should start with one explicit slash.
    # Note, this does not apply to '--volume'
    text = text.replace("$(PROJECT_PATH_ENV)", "/$(PROJECT_PATH_ENV)")

makefile_path.write_text(text)
