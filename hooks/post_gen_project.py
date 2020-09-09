import uuid
import re

from pathlib import Path

project_slug_name = "{{ cookiecutter.project_slug }}".replace("_", "-")
project_id = f"{project_slug_name}-{uuid.uuid4().hex[:8]}"

live_file_path = Path(".neuro/live.yml")

text = live_file_path.read_text()
text = re.sub(r"project:project-slug-name-placeholder", f"project:{project_slug_name}", text)
text = re.sub(r"project-id:project-uuid-placeholder", f"project-id:{project_id}", text)

live_file_path.write_text(text)
