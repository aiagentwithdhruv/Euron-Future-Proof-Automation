"""Bootstrap: make shared/* from the Agentic Workflow engine importable.

Every tool/module inside D2C_Ecommerce_Suite imports this once to wire up
`shared.logger`, `shared.env_loader`, `shared.sanitize`, etc.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGINE_ROOT = PROJECT_ROOT.parent / "Agentic Workflow for Students"

if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def project_root() -> Path:
    return PROJECT_ROOT


def tmp_dir() -> Path:
    p = PROJECT_ROOT / ".tmp"
    p.mkdir(parents=True, exist_ok=True)
    return p


def runs_dir() -> Path:
    p = PROJECT_ROOT / "runs"
    p.mkdir(parents=True, exist_ok=True)
    return p
