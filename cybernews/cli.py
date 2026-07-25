"""Command-line interface: the daily cybersecurity news agent."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import timezone

from .aggregator import build_digest
from .render import render_html, render_json, render_markdown


def _print(msg: str) -> None:
    print(msg, file=sys.stderr)


def _terminal_digest(digest) -> str:
    """A compact, readable digest for the terminal."""
    lines = []
    date_str = digest.generated_at.strftime("%A, %d %B %Y")
    lines.append(f"\n🛡️  CYBERSECURITY NEWS — {date_str}")
    lines.append(f"    last {digest.since_hours}h · {digest.count} stories · "
                 f"{digest.sources_ok}/{digest.sources_total} sources reachable")

    for header, arts in (("🇧🇪 BELGIUM", digest.belgium), ("🌍 WORLD", digest.world)):
        lines.append(f"\n{'='*70}\n{header}\n{'='*70}")
        if not arts:
            lines.append("  (nothing in this window)")
            continue
        for i, art in enumerate(arts, 1):
            when = art.published.strftime("%Y-%m-%d %H:%M UTC") if art.published else "date unknown"
            lines.append(f"\n{i}. {art.title}")
            lines.append(f"   {art.source} · {when}")
            if art.summary:
                lines.append(f"   {art.summary}")
            lines.append(f"   🔗 {art.link}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cybernews",
        description="Daily cybersecurity news agent — Belgium & the world. "
                    "Real stories from reputable feeds, each with a summary and "
                    "a link to the official article.",
    )
    p.add_argument("--since-hours", type=int, default=24,
                   help="Only include stories from the last N hours (default: 24).")
    p.add_argument("--max-per-source", type=int, default=15,
                   help="Cap the number of stories taken from each feed (default: 15).")
    p.add_argument("--config", default=None,
                   help="Path to a custom feeds.json.")
    p.add_argument("--format", default="terminal",
                   choices=["terminal", "md", "html", "json", "all"],
                   help="Output format (default: terminal).")
    p.add_argument("--output-dir", default="digests",
                   help="Directory for md/html/json output (default: ./digests).")
    p.add_argument("--no-write", action="store_true",
                   help="Print to stdout only; do not write files.")
    p.add_argument("--quiet", action="store_true",
                   help="Suppress progress messages.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    progress = None if args.quiet else _print
    if not args.quiet:
        _print("Gathering cybersecurity news …")

    digest = build_digest(
        config_path=args.config,
        since_hours=args.since_hours,
        max_per_source=args.max_per_source,
        progress=progress,
    )

    if not args.quiet:
        _print(f"Collected {digest.count} stories "
               f"({len(digest.belgium)} Belgium / {len(digest.world)} world).")
        for err in digest.errors:
            _print(f"  ⚠️  {err}")

    date_slug = digest.generated_at.astimezone(timezone.utc).strftime("%Y-%m-%d")
    renderers = {
        "md": ("md", render_markdown),
        "html": ("html", render_html),
        "json": ("json", render_json),
    }

    if args.format == "terminal":
        print(_terminal_digest(digest))
        return 0

    formats = ["md", "html", "json"] if args.format == "all" else [args.format]

    for fmt in formats:
        ext, renderer = renderers[fmt]
        content = renderer(digest)
        if args.no_write:
            print(content)
            continue
        os.makedirs(args.output_dir, exist_ok=True)
        path = os.path.join(args.output_dir, f"{date_slug}.{ext}")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        # Also refresh a "latest" convenience copy.
        latest = os.path.join(args.output_dir, f"latest.{ext}")
        with open(latest, "w", encoding="utf-8") as fh:
            fh.write(content)
        _print(f"Wrote {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
