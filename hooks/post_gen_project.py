import uuid
import re

from pathlib import Path

project_id = f"neuro-project-{uuid.uuid4().hex[:8]}"

makefile_path = Path("Makefile")

text = makefile_path.read_text()
text = re.sub(r"PROJECT_ID=placeholder", f"PROJECT_ID={project_id}", text)

makefile_path.write_text(text)
