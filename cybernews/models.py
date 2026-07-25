"""Data models used across the aggregator."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Article:
    """A single news article gathered from a feed."""

    title: str
    link: str
    source: str
    region: str = "WORLD"          # BE, EU or WORLD (the feed's declared region)
    published: Optional[datetime] = None
    summary: str = ""              # cleaned, short human-readable summary
    raw_summary: str = ""          # cleaned full description from the feed
    is_belgium: bool = False       # True when the story is relevant to Belgium
    matched_keywords: list = field(default_factory=list)
    score: float = 0.0             # ranking score (higher = shown first)

    def published_iso(self) -> str:
        if not self.published:
            return ""
        return self.published.astimezone(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["published"] = self.published_iso()
        return data
