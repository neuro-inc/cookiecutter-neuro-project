import importlib
import sys
import typing as t

from shortcuts.internals.abc import Config


def collect_entrypoints(module_name: str) -> t.Dict[str, t.Callable[[Config], None]]:
    """ collect all callable object from module `module_name`
    whose names start with a lowerase english alphabet character
    """
    importlib.import_module(module_name)
    module = sys.modules[module_name]
    result: t.Dict[str, t.Callable] = {}
    for name in dir(module):
        if 'a' <= name[0] <= 'z':
            obj = getattr(module, name)
            if callable(obj):
                result[name] = obj
    return result
