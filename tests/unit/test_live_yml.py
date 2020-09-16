from typing import Any, Dict, List
from neuro_flow import ConfigDir

def test_validate_live_yml() -> None:
    config_path = find_live_config(config_dir)
