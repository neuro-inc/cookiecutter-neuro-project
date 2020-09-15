import uuid
import re

from pathlib import Path

project_slug_name = "{{ cookiecutter.project_slug }}".replace("_", "-")
flow_id = f"neuro-flow-{uuid.uuid4().hex[:8]}"

live_file_path = Path(".neuro/live.yml")

text = live_file_path.read_text()
text = re.sub("PROJECT_SLUG_WITH_DASHES_PLACEHOLDER", project_slug_name, text)
text = re.sub("FLOW_ID_PLACEHOLDER", flow_id, text)

live_file_path.write_text(text)
