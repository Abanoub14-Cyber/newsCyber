"""Fetch feeds over HTTP and parse RSS 2.0 / Atom into Article objects.

Uses the standard library XML parser plus ``requests`` (falling back to
``urllib`` if requests is not installed) so the project has no hard third-party
parsing dependency and runs anywhere.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from xml.etree import ElementTree as ET

from .models import Article
from .summarize import clean_html, summarize

USER_AGENT = (
    "Mozilla/5.0 (compatible; cybernews-aggregator/1.0; "
    "+https://github.com/Abanoub14-Cyber/newsCyber)"
)

# XML namespaces we may encounter.
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


class FetchError(Exception):
    """Raised when a feed cannot be retrieved."""


def fetch_url(url: str, timeout: int = 20, retries: int = 2) -> bytes:
    """Download a URL and return the raw bytes, retrying on transient errors."""
    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            return _http_get(url, timeout)
        except Exception as exc:  # noqa: BLE001 - we re-raise as FetchError below
            last_err = exc
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise FetchError(f"Could not fetch {url}: {last_err}")


def _http_get(url: str, timeout: int) -> bytes:
    try:
        import requests  # type: ignore

        resp = requests.get(
            url, timeout=timeout, headers={"User-Agent": USER_AGENT}
        )
        resp.raise_for_status()
        return resp.content
    except ImportError:
        import urllib.request

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
            return r.read()


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #

def _localname(tag: str) -> str:
    """Return the tag name without its XML namespace."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _text(el: Optional[ET.Element]) -> str:
    return (el.text or "").strip() if el is not None else ""


def _parse_date(value: str) -> Optional[datetime]:
    """Parse an RSS (RFC 822) or Atom (ISO 8601) date string into aware UTC."""
    if not value:
        return None
    value = value.strip()
    # RSS: "Wed, 02 Oct 2024 13:00:00 GMT"
    try:
        dt = parsedate_to_datetime(value)
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    # Atom: "2024-10-02T13:00:00Z" or with offset.
    try:
        iso = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _find_child(item: ET.Element, names: set[str]) -> Optional[ET.Element]:
    for child in item:
        if _localname(child.tag) in names:
            return child
    return None


def _extract_link(item: ET.Element) -> str:
    """Get the article URL from either an RSS <link>text</link> or an Atom
    <link href="..."/> (preferring rel="alternate")."""
    fallback = ""
    for child in item:
        if _localname(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        if href:
            rel = child.attrib.get("rel", "alternate")
            if rel == "alternate":
                return href.strip()
            fallback = fallback or href.strip()
        elif child.text and child.text.strip():
            return child.text.strip()
    return fallback


def parse_feed(content: bytes, source: str, region: str = "WORLD") -> list[Article]:
    """Parse feed bytes (RSS 2.0 or Atom) into a list of Article objects."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise FetchError(f"Malformed XML for {source}: {exc}") from exc

    # RSS items live under channel/item; Atom entries are direct children.
    items = [el for el in root.iter() if _localname(el.tag) == "item"]
    if not items:
        items = [el for el in root.iter() if _localname(el.tag) == "entry"]

    articles: list[Article] = []
    for item in items:
        title = _text(_find_child(item, {"title"}))
        link = _extract_link(item)
        if not title or not link:
            continue

        # Description: prefer full content, fall back to summary/description.
        body_el = _find_child(item, {"encoded", "content", "description", "summary"})
        raw = _text(body_el)
        raw_clean = clean_html(raw)

        date_el = _find_child(item, {"pubDate", "published", "updated", "date"})
        published = _parse_date(_text(date_el))

        articles.append(
            Article(
                title=clean_html(title),
                link=link,
                source=source,
                region=region,
                published=published,
                summary=summarize(raw),
                raw_summary=raw_clean,
            )
        )
    return articles


def fetch_feed(url: str, source: str, region: str = "WORLD",
               timeout: int = 20) -> list[Article]:
    """Fetch and parse a single feed. Raises FetchError on failure."""
    content = fetch_url(url, timeout=timeout)
    return parse_feed(content, source=source, region=region)
