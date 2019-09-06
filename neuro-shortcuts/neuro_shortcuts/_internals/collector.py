import sys
import typing as t

from neuro_shortcuts._internals.abc import Config


def collect_entrypoints(module_name: str) -> t.Dict[str, t.Callable[[Config], None]]:
    f_names = dir(module_name)
    print(f_names)
    exit(33)
    return {f_name: getattr(sys.modules[module_name], f_name) for f_name in f_names}
