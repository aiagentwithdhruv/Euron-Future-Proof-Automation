"""Central config for D2C_Ecommerce_Suite — loads .env once, exposes typed getters."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from tools._bootstrap import project_root

from shared.env_loader import load_env  # noqa: E402
from shared.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

_loaded = False


def ensure_env() -> None:
    global _loaded
    if _loaded:
        return
    load_env(env_path=str(project_root() / ".env"))
    _loaded = True


def env(key: str, default: Optional[str] = None) -> Optional[str]:
    ensure_env()
    val = os.environ.get(key)
    return val if val not in (None, "") else default


def env_int(key: str, default: int) -> int:
    raw = env(key)
    try:
        return int(raw) if raw is not None else default
    except ValueError:
        logger.warning(f"env {key}={raw!r} not an int; using default {default}")
        return default


@dataclass(frozen=True)
class ModuleConfig:
    abandoned_cart_delay_min: int
    abandoned_cart_step2_hrs: int
    abandoned_cart_step3_days: int
    low_stock_threshold: int
    review_request_delay_days: int
    discount_code_recovery: str


def module_config() -> ModuleConfig:
    return ModuleConfig(
        abandoned_cart_delay_min=env_int("ABANDONED_CART_DELAY_MIN", 60),
        abandoned_cart_step2_hrs=env_int("ABANDONED_CART_STEP2_HRS", 24),
        abandoned_cart_step3_days=env_int("ABANDONED_CART_STEP3_DAYS", 3),
        low_stock_threshold=env_int("LOW_STOCK_THRESHOLD", 10),
        review_request_delay_days=env_int("REVIEW_REQUEST_DELAY_DAYS", 7),
        discount_code_recovery=env("DISCOUNT_CODE_RECOVERY", "COMEBACK10"),
    )
