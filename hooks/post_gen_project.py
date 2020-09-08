import uuid
import re

from pathlib import Path

project_kebab = "{{ cookiecutter.project_slug }}".replace("_", "-")
project_id = f"{project_kebab}-{uuid.uuid4().hex[:8]}"

live_file_path = Path(".neuro/live.yml")

text = live_file_path.read_text()
text = re.sub(r"project:project-kebab-name-placeholder", f"project:{project_kebab}", text)
text = re.sub(r"project-id:project-uuid-placeholder", f"project-id:{project_id}", text)

live_file_path.write_text(text)
