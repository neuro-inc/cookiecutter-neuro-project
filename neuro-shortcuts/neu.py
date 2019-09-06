import pathlib

from shortcuts.config import create_config
from shortcuts.internals.loaders import collect_entrypoints
from argparse import  ArgumentParser
API_MODULE_NAME = "shortcuts.api"


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(description='TODO root')
    parser.add_argument('action', metavar='ACTION', type=str,
                       help='TODO action')
    return parser

def get_project_name() -> str:
    """ We assume that the parent directory is named same as the project
    """
    current_dir = pathlib.Path(__file__).resolve()
    return str(current_dir.parent)


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    action_name = args.action

    module_name = API_MODULE_NAME
    entrypoints = collect_entrypoints(module_name)
    action = entrypoints.get(action_name)
    if not action:
        print(f"ERROR: Cannot find action '{action_name}' in module '{module_name}'")
        print(f"Available actions: {', '.join(entrypoints.keys())}")
        exit(1)

    project_name = get_project_name()
    cfg = create_config(project_name)

    try:
        action(cfg)
    except (TypeError, AttributeError) as e:
        print(f"ERROR: Could not execute action '{action_name}': {e}")

