"""Render a DigestResult as Markdown, HTML or JSON."""

from __future__ import annotations

import html
import json
from datetime import datetime

from .aggregator import DigestResult
from .models import Article


def _fmt_date(art: Article) -> str:
    if not art.published:
        return "date unknown"
    return art.published.strftime("%Y-%m-%d %H:%M UTC")


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #

def _md_article(art: Article) -> str:
    lines = [f"### [{art.title}]({art.link})"]
    meta = f"*{art.source} · {_fmt_date(art)}*"
    if art.matched_keywords:
        tags = ", ".join(k for k in art.matched_keywords if k != "belgium (source)")
        if tags:
            meta += f" · 🇧🇪 _{tags}_"
    lines.append(meta)
    if art.summary:
        lines.append("")
        lines.append(art.summary)
    lines.append("")
    lines.append(f"🔗 Read the full article: <{art.link}>")
    return "\n".join(lines)


def render_markdown(digest: DigestResult) -> str:
    date_str = digest.generated_at.strftime("%A, %d %B %Y")
    out: list[str] = []
    out.append(f"# 🛡️ Cybersecurity News Digest — {date_str}")
    out.append("")
    out.append(
        f"_Generated {digest.generated_at.strftime('%Y-%m-%d %H:%M UTC')} · "
        f"last {digest.since_hours}h · {digest.count} stories from "
        f"{digest.sources_ok}/{digest.sources_total} sources._"
    )
    out.append("")
    out.append(
        "Every item below is summarized from the source's own feed and links "
        "to the original, official article for the full story."
    )
    out.append("")

    out.append("## 🇧🇪 Belgium")
    out.append("")
    if digest.belgium:
        for art in digest.belgium:
            out.append(_md_article(art))
            out.append("\n---\n")
    else:
        out.append("_No Belgium-specific stories in this window._")
        out.append("")

    out.append("## 🌍 World")
    out.append("")
    if digest.world:
        for art in digest.world:
            out.append(_md_article(art))
            out.append("\n---\n")
    else:
        out.append("_No world stories in this window._")
        out.append("")

    if digest.errors:
        out.append("## ⚠️ Sources that could not be reached")
        out.append("")
        for err in digest.errors:
            out.append(f"- {err}")
        out.append("")

    out.append(
        "_This digest aggregates public RSS/Atom feeds from reputable "
        "cybersecurity outlets and official CERT/CSIRT bodies. "
        "Summaries are extractive (taken from the source feed); always read "
        "the linked original for the authoritative account._"
    )
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #

def _html_article(art: Article) -> str:
    title = html.escape(art.title)
    link = html.escape(art.link, quote=True)
    source = html.escape(art.source)
    summary = html.escape(art.summary)
    tags = ""
    if art.matched_keywords:
        kws = ", ".join(
            html.escape(k) for k in art.matched_keywords if k != "belgium (source)"
        )
        if kws:
            tags = f'<span class="tag">🇧🇪 {kws}</span>'
    return f"""
      <article class="card">
        <h3><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
        <div class="meta">{source} · {_fmt_date(art)} {tags}</div>
        <p class="summary">{summary}</p>
        <a class="readmore" href="{link}" target="_blank" rel="noopener noreferrer">Read the full article &rarr;</a>
      </article>"""


def render_html(digest: DigestResult) -> str:
    date_str = digest.generated_at.strftime("%A, %d %B %Y")

    def section(title: str, articles: list[Article], empty: str) -> str:
        body = "\n".join(_html_article(a) for a in articles) if articles else \
            f'<p class="empty">{empty}</p>'
        return f'<section><h2>{title}</h2>{body}</section>'

    be_section = section("🇧🇪 Belgium", digest.belgium,
                         "No Belgium-specific stories in this window.")
    world_section = section("🌍 World", digest.world,
                            "No world stories in this window.")

    errors_html = ""
    if digest.errors:
        items = "".join(f"<li>{html.escape(e)}</li>" for e in digest.errors)
        errors_html = (
            f'<section class="errors"><h2>⚠️ Unreachable sources</h2>'
            f"<ul>{items}</ul></section>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cybersecurity News Digest — {date_str}</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
         margin: 0; background: #0b1220; color: #e6edf3; line-height: 1.55; }}
  header {{ background: linear-gradient(135deg,#0d1b3a,#12294d); padding: 2rem 1.25rem;
           border-bottom: 3px solid #2f81f7; }}
  header h1 {{ margin: 0 0 .25rem; font-size: 1.6rem; }}
  header p {{ margin: 0; color: #9fb3c8; font-size: .9rem; }}
  main {{ max-width: 860px; margin: 0 auto; padding: 1.5rem 1.25rem 3rem; }}
  h2 {{ margin-top: 2.2rem; border-bottom: 1px solid #22304a; padding-bottom: .4rem; }}
  .card {{ background: #111a2e; border: 1px solid #22304a; border-radius: 12px;
          padding: 1rem 1.15rem; margin: 1rem 0; }}
  .card h3 {{ margin: 0 0 .35rem; font-size: 1.12rem; }}
  .card h3 a {{ color: #6cb6ff; text-decoration: none; }}
  .card h3 a:hover {{ text-decoration: underline; }}
  .meta {{ font-size: .8rem; color: #8aa0b6; margin-bottom: .55rem; }}
  .tag {{ display: inline-block; background: #1f2f1f; color: #a7e0a7;
         border: 1px solid #2f5f2f; border-radius: 6px; padding: 0 .4rem;
         margin-left: .4rem; font-size: .72rem; }}
  .summary {{ margin: .3rem 0 .7rem; color: #d7e2ee; }}
  .readmore {{ font-size: .85rem; color: #2f81f7; text-decoration: none; font-weight: 600; }}
  .readmore:hover {{ text-decoration: underline; }}
  .empty {{ color: #7a8ca0; font-style: italic; }}
  .errors ul {{ color: #d0a0a0; font-size: .8rem; }}
  footer {{ max-width: 860px; margin: 0 auto; padding: 1rem 1.25rem 3rem;
           color: #6f8296; font-size: .78rem; }}
  a {{ color: #6cb6ff; }}
</style>
</head>
<body>
<header>
  <h1>🛡️ Cybersecurity News Digest</h1>
  <p>{date_str} · last {digest.since_hours}h · {digest.count} stories from
     {digest.sources_ok}/{digest.sources_total} sources</p>
</header>
<main>
  <p>Every item is summarized from the source's own feed and links to the
     original, official article for the full story.</p>
  {be_section}
  {world_section}
  {errors_html}
</main>
<footer>
  Aggregated from public RSS/Atom feeds of reputable cybersecurity outlets and
  official CERT/CSIRT bodies. Summaries are extractive (taken from the source
  feed); read the linked original for the authoritative account.
</footer>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# JSON
# --------------------------------------------------------------------------- #

def render_json(digest: DigestResult) -> str:
    payload = {
        "generated_at": digest.generated_at.astimezone().isoformat(),
        "since_hours": digest.since_hours,
        "sources_ok": digest.sources_ok,
        "sources_total": digest.sources_total,
        "count": digest.count,
        "belgium": [a.to_dict() for a in digest.belgium],
        "world": [a.to_dict() for a in digest.world],
        "errors": digest.errors,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
