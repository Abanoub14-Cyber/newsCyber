"""Lightweight, offline text cleaning and extractive summarization.

Summaries are built *only* from the text the source itself publishes in its
feed (the description / content). Nothing is invented or paraphrased by a
model, so the digest stays factual and always points back to the official
article for the full story.
"""

from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
# Split on sentence-ending punctuation followed by whitespace + a capital/quote/digit.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'À-ſ])")


def clean_html(text: str) -> str:
    """Strip HTML tags and collapse whitespace from a feed description."""
    if not text:
        return ""
    # Drop script/style blocks entirely before removing the rest of the tags.
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def split_sentences(text: str) -> list[str]:
    if not text:
        return []
    parts = _SENTENCE_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def summarize(text: str, max_sentences: int = 2, max_chars: int = 320) -> str:
    """Return a short extractive summary: the first sentences of the text.

    The lead of a news item almost always carries the who/what/where, so the
    first one or two sentences make a faithful, non-editorialized summary.
    """
    clean = clean_html(text)
    if not clean:
        return ""

    sentences = split_sentences(clean)
    if not sentences:
        chosen = clean
    else:
        chosen = " ".join(sentences[:max_sentences]).strip()

    if len(chosen) > max_chars:
        cut = chosen[: max_chars - 1]
        # Avoid cutting in the middle of a word.
        if " " in cut:
            cut = cut[: cut.rfind(" ")]
        chosen = cut.rstrip(" ,;:.") + "…"  # ellipsis
    return chosen
