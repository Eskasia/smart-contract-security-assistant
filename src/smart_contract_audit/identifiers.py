from __future__ import annotations

import re

SAFE_PATH_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]+$")


def is_safe_path_segment(value: str) -> bool:
    return bool(SAFE_PATH_SEGMENT.fullmatch(value)) and value not in {".", ".."}


def require_safe_path_segment(value: str, field_name: str) -> str:
    if not is_safe_path_segment(value):
        raise ValueError(f"{field_name} must be a safe relative path segment.")
    return value
