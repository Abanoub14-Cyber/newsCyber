"""Offline tests for the aggregator pipeline (no network required)."""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cybernews.aggregator import build_digest  # noqa: E402
from cybernews.fetch import parse_feed  # noqa: E402
from cybernews.render import render_html, render_json, render_markdown  # noqa: E402
from cybernews.summarize import clean_html, summarize  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_rss.xml")


def _load_fixture() -> bytes:
    with open(FIXTURE, "rb") as fh:
        return fh.read()


def test_clean_html_strips_tags():
    assert clean_html("<p>Hello <b>world</b> &amp; more</p>") == "Hello world & more"


def test_summarize_limits_sentences():
    text = "First sentence. Second sentence. Third sentence."
    out = summarize(text, max_sentences=2)
    assert out == "First sentence. Second sentence."


def test_parse_feed_extracts_articles():
    articles = parse_feed(_load_fixture(), source="Sample", region="WORLD")
    assert len(articles) == 3
    titles = [a.title for a in articles]
    assert "Weekly threat roundup" in titles
    # Dates parsed for the first two, None for the undated one.
    assert articles[0].published is not None
    assert articles[2].published is None
    # Query strings stripped/retained on link but link present.
    assert articles[1].link.startswith("https://example.com/vpn-zeroday")


def _fake_fetcher(url, source, region="WORLD"):
    return parse_feed(_load_fixture(), source=source, region=region)


def test_build_digest_tags_belgium(tmp_path):
    # Point at a tiny config with one WORLD feed so we exercise keyword tagging.
    import json
    cfg = tmp_path / "feeds.json"
    cfg.write_text(json.dumps({
        "feeds": [{"name": "Sample", "url": "http://x", "region": "WORLD"}],
        "belgium_keywords": ["belgium", "antwerp",
                             "centre for cybersecurity belgium"],
    }))

    now = datetime(2025, 7, 23, 12, 0, tzinfo=timezone.utc)
    digest = build_digest(
        config_path=str(cfg),
        since_hours=48,
        now=now,
        fetcher=_fake_fetcher,
    )
    assert digest.sources_ok == 1
    # The Antwerp story must be classified as Belgium-relevant.
    be_titles = [a.title for a in digest.belgium]
    assert any("Antwerp" in t for t in be_titles)
    # The VPN story is world-only.
    world_titles = [a.title for a in digest.world]
    assert any("VPN" in t for t in world_titles)


def test_renderers_produce_output(tmp_path):
    import json
    cfg = tmp_path / "feeds.json"
    cfg.write_text(json.dumps({
        "feeds": [{"name": "Sample", "url": "http://x", "region": "BE"}],
        "belgium_keywords": ["belgium"],
    }))
    now = datetime(2025, 7, 23, 12, 0, tzinfo=timezone.utc)
    digest = build_digest(config_path=str(cfg), since_hours=48, now=now,
                          fetcher=_fake_fetcher)

    md = render_markdown(digest)
    assert "Cybersecurity News Digest" in md
    assert "Read the full article" in md

    html_out = render_html(digest)
    assert "<html" in html_out and "Read the full article" in html_out

    data = json.loads(render_json(digest))
    assert data["count"] == 3
    assert "belgium" in data and "world" in data


if __name__ == "__main__":
    # Allow running without pytest.
    import traceback
    passed = failed = 0
    ns = dict(globals())
    for name, fn in ns.items():
        if name.startswith("test_") and callable(fn):
            try:
                import inspect
                if "tmp_path" in inspect.signature(fn).parameters:
                    import tempfile, pathlib
                    with tempfile.TemporaryDirectory() as d:
                        fn(pathlib.Path(d))
                else:
                    fn()
                passed += 1
                print(f"PASS {name}")
            except Exception:
                failed += 1
                print(f"FAIL {name}")
                traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(1 if failed else 0)
