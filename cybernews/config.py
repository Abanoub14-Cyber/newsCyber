"""Loading of the feeds configuration."""

from __future__ import annotations

import json
import os
from typing import Any

_DEFAULT_CONFIG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "feeds.json",
)


def load_config(path: str | None = None) -> dict[str, Any]:
    """Load the feeds configuration JSON.

    Returns a dict with keys ``feeds`` (list) and ``belgium_keywords`` (list).
    """
    path = path or _DEFAULT_CONFIG
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    feeds = [f for f in data.get("feeds", []) if not str(f.get("name", "")).startswith("_")]
    return {
        "feeds": feeds,
        "belgium_keywords": [k.lower() for k in data.get("belgium_keywords", [])],
    }
