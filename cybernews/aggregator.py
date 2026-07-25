"""Orchestrate the pipeline: fetch every feed, tag, deduplicate, rank."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from .config import load_config
from .fetch import FetchError, fetch_feed
from .models import Article

_WORD_SPLIT = re.compile(r"[^a-z0-9.]+")


@dataclass
class DigestResult:
    generated_at: datetime
    since_hours: int
    belgium: list[Article] = field(default_factory=list)
    world: list[Article] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    sources_ok: int = 0
    sources_total: int = 0

    @property
    def all(self) -> list[Article]:
        return self.belgium + self.world

    @property
    def count(self) -> int:
        return len(self.belgium) + len(self.world)


def _tag_belgium(article: Article, keywords: list[str]) -> None:
    """Mark an article as Belgium-relevant when its text matches keywords."""
    haystack = f" {article.title} {article.raw_summary} ".lower()
    matched = [kw.strip() for kw in keywords if kw.strip() and kw in haystack]
    if article.region == "BE":
        # A dedicated Belgian source is always Belgium-relevant.
        article.is_belgium = True
        if "belgium (source)" not in matched:
            matched.append("belgium (source)")
    else:
        article.is_belgium = bool(matched)
    article.matched_keywords = sorted(set(matched))


def _score(article: Article, now: datetime) -> float:
    """Rank by recency, Belgium relevance and source region."""
    score = 0.0
    if article.published:
        age_hours = max(0.0, (now - article.published).total_seconds() / 3600.0)
        score += max(0.0, 72.0 - age_hours)  # newer = higher, up to 3 days
    if article.is_belgium:
        score += 100.0
        score += 5.0 * len(article.matched_keywords)
    if article.region == "BE":
        score += 40.0
    elif article.region == "EU":
        score += 10.0
    return score


def _dedupe(articles: list[Article]) -> list[Article]:
    seen: set[str] = set()
    out: list[Article] = []
    for art in articles:
        key_link = art.link.split("?")[0].rstrip("/").lower()
        key_title = re.sub(r"\s+", " ", art.title.lower()).strip()
        if key_link in seen or key_title in seen:
            continue
        seen.add(key_link)
        seen.add(key_title)
        out.append(art)
    return out


def build_digest(
    config_path: str | None = None,
    since_hours: int = 24,
    max_per_source: int = 15,
    now: Optional[datetime] = None,
    progress: Optional[Callable[[str], None]] = None,
    fetcher: Callable[..., list[Article]] = fetch_feed,
) -> DigestResult:
    """Run the full aggregation pipeline and return a DigestResult.

    ``fetcher`` is injectable so the pipeline can be tested offline.
    """
    cfg = load_config(config_path)
    feeds = cfg["feeds"]
    keywords = cfg["belgium_keywords"]
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=since_hours)

    result = DigestResult(generated_at=now, since_hours=since_hours,
                          sources_total=len(feeds))
    collected: list[Article] = []

    for feed in feeds:
        name = feed.get("name", feed.get("url", "unknown"))
        region = feed.get("region", "WORLD")
        if progress:
            progress(f"Fetching {name} …")
        try:
            articles = fetcher(feed["url"], source=name, region=region)
            result.sources_ok += 1
        except FetchError as exc:
            result.errors.append(str(exc))
            continue
        except Exception as exc:  # noqa: BLE001 - never let one feed break the run
            result.errors.append(f"{name}: {exc}")
            continue

        # Keep undated items (many feeds omit dates) but respect the window
        # for dated ones. Cap per source to avoid one feed flooding the digest.
        fresh = [
            a for a in articles
            if a.published is None or a.published >= cutoff
        ][:max_per_source]
        collected.extend(fresh)

    collected = _dedupe(collected)

    for art in collected:
        _tag_belgium(art, keywords)
        art.score = _score(art, now)

    belgium = [a for a in collected if a.is_belgium]
    world = [a for a in collected if not a.is_belgium]

    belgium.sort(key=lambda a: a.score, reverse=True)
    world.sort(key=lambda a: a.score, reverse=True)

    result.belgium = belgium
    result.world = world
    return result
