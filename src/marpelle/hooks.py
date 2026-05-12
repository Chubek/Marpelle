from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from .errors import MarpelleError

Hook = Callable[[dict[str, Any]], dict[str, Any]]


def load_hooks(module_name: str = "marpelle_hooks") -> dict[str, Hook]:
    module = importlib.import_module(module_name)
    hooks = getattr(module, "HOOKS", None)
    if not isinstance(hooks, dict):
        raise MarpelleError(f"{module_name}.HOOKS must be a dict")
    for name, handler in hooks.items():
        if not isinstance(name, str) or not callable(handler):
            raise MarpelleError("HOOKS must map command names to callables")
    return hooks
