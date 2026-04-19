"""Dynamic loader — stage folders start with digits (01_scrape), which isn't a
legal Python module name. We load stage files by path via importlib."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load(relpath: str) -> ModuleType:
    """Load a stage file like '01_scrape/google_maps.py' and return the module."""
    full = PROJECT_ROOT / "stages" / relpath
    if not full.exists():
        raise FileNotFoundError(full)
    name = relpath.replace("/", ".").removesuffix(".py")
    name = "cas_stage_" + name.replace(".", "_")
    spec = importlib.util.spec_from_file_location(name, full)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
