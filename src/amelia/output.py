"""JSON serialization for Amelia data models."""

import json
from dataclasses import asdict, is_dataclass


def to_json(obj) -> dict | list:
    """Convert a dataclass or list of dataclasses to JSON-serializable dicts."""
    if isinstance(obj, list):
        return [to_json(item) for item in obj]
    if is_dataclass(obj):
        return asdict(obj)
    return obj


def to_json_str(obj, indent: int = 2) -> str:
    """Convert to JSON string."""
    return json.dumps(to_json(obj), indent=indent)
