import re

from pathlib import Path

project_slug_name = "{{ cookiecutter.project_slug }}".replace("-", "_")

live_file_path = Path(".neuro/live.yml")

text = live_file_path.read_text()
text = re.sub("PROJECT_SLUG_WITH_UNDERSCORES_PLACEHOLDER", project_slug_name, text)

live_file_path.write_text(text)
