"""Runtime configuration for the Practical AI Journey FastAPI app."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    root_path: str = ""


def _normalize_root_path(raw: str) -> str:
    value = (raw or "").strip()
    if not value or value == "/":
        return ""
    if not value.startswith("/"):
        value = f"/{value}"
    return value.rstrip("/")


def get_settings() -> Settings:
    return Settings(root_path=_normalize_root_path(os.getenv("PRACTICAL_AI_ROOT_PATH", "")))
