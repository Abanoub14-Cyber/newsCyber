# 🛡️ newsCyber — Daily Cybersecurity News Agent (Belgium & the World)

A small, dependency‑light **agent that gathers real cybersecurity news every
day** — with a special focus on **Belgium 🇧🇪** and full coverage of the
**wider world 🌍**. For every story you get a short **summary** and a **link to
the original, official article** so you can read the full account at the source.

Everything comes from **public RSS/Atom feeds of reputable outlets and official
CERT/CSIRT bodies** (see [the source list](config/feeds.json)). Nothing is
invented: summaries are *extractive* — taken directly from what each source
publishes — and every item links back to the real article. **No fake news.**

> 📄 Want to see what the output looks like first? Open
> [`examples/example-digest.md`](examples/example-digest.md) or
> [`examples/example-digest.html`](examples/example-digest.html)
> *(these are generated from a test fixture — clearly marked example data, not real news)*.

---

## ✨ What it does

- Pulls the latest stories from ~14 trusted cybersecurity feeds (world + Belgium/EU).
- **Detects Belgium‑relevant stories** across *every* feed using a keyword matcher
  (Belgium, Belgian cities, CCB/Safeonweb, CERT.be, major Belgian orgs, …) — so
  Belgian news surfaces even when it appears on an international outlet.
- Summarizes each article (short, faithful, extractive).
- Deduplicates, filters to a time window (default: last 24 h) and ranks by
  relevance + recency.
- Outputs a clean digest to your **terminal**, or as **Markdown / HTML / JSON**.
- Ships a **GitHub Action** that runs the agent **automatically every day**.

---

## 🚀 Quick start

Requires **Python 3.9+**. No compilation, one optional dependency.

```bash
# 1. (optional but recommended) install requests
pip install -r requirements.txt

# 2. Get today's cybersecurity news in your terminal
python main.py
```

That prints a Belgium section and a World section, each story with its source,
time, summary and a link to the full article.

### More ways to run it

```bash
# Widen the window to the last 48 hours
python main.py --since-hours 48

# Write Markdown + HTML + JSON into ./digests/ (also keeps a latest.* copy)
python main.py --format all

# Just the HTML digest, printed to stdout
python main.py --format html --no-write

# Use your own curated feed list
python main.py --config path/to/my-feeds.json
```

Open the generated `digests/latest.html` in any browser for a nicely styled,
mobile‑friendly reading view.

### All options

| Flag | Default | Description |
|------|---------|-------------|
| `--since-hours N` | `24` | Only include stories from the last N hours. |
| `--max-per-source N` | `15` | Cap stories taken from each feed. |
| `--format` | `terminal` | `terminal`, `md`, `html`, `json`, or `all`. |
| `--output-dir DIR` | `digests` | Where md/html/json files are written. |
| `--config FILE` | `config/feeds.json` | Custom feed list. |
| `--no-write` | off | Print to stdout instead of writing files. |
| `--quiet` | off | Suppress progress messages. |

---

## 🤖 Run it automatically every day (the "agent")

A ready‑to‑use workflow lives at
[`.github/workflows/daily-news.yml`](.github/workflows/daily-news.yml). Once this
repository is on GitHub it will, **every day at ~06:15 UTC**:

1. fetch the latest real news,
2. build the digest in Markdown, HTML and JSON, and
3. commit the files to a dedicated **`digests` branch** (so your `main` stays
   clean) and attach them as a downloadable workflow artifact.

You can also trigger it any time from the **Actions → Daily Cybersecurity News
Digest → Run workflow** button. No secrets or API keys are required — it uses the
built‑in `GITHUB_TOKEN`.

**Prefer email or Slack delivery?** The command prints/writes plain files, so you
can pipe `digests/latest.md` into any notifier you like. A couple of easy paths:
add a step that emails `digests/latest.html`, or post the Markdown to a Slack
webhook.

### Run it locally on a schedule instead

Add a cron entry on your own machine:

```cron
# 8:15 every morning: refresh the digest into ~/cyber-digests
15 8 * * *  cd /path/to/newsCyber && /usr/bin/python3 main.py --format all --output-dir ~/cyber-digests
```

---

## 📰 Sources

The default feeds are in [`config/feeds.json`](config/feeds.json) and include:

- **Belgium / EU:** Centre for Cybersecurity Belgium (Safeonweb), CERT.be,
  ENISA (EU Cybersecurity Agency).
- **World:** BleepingComputer, The Hacker News, Krebs on Security, Dark Reading,
  SecurityWeek, The Record, Schneier on Security, Graham Cluley, CISA advisories,
  Microsoft MSRC, Google Project Zero.

Add, remove or replace any of them by editing that file — each entry just needs a
`name`, `url` and `region` (`BE`, `EU` or `WORLD`). The Belgium keyword list at
the bottom of the same file controls how Belgian relevance is detected; extend it
with organisations or topics you care about.

> ℹ️ Feed URLs occasionally change. If a source shows up under
> "unreachable sources" in the digest, update its URL in `config/feeds.json`.

---

## 🧩 How it works

```
config/feeds.json ──▶ fetch.py ──▶ parse (RSS 2.0 / Atom, stdlib XML)
                                     │
                                     ▼
                          summarize.py (clean HTML + extractive summary)
                                     │
                                     ▼
        aggregator.py ── dedupe · filter window · tag Belgium · rank
                                     │
                                     ▼
              render.py ── terminal · Markdown · HTML · JSON
```

- **`cybernews/fetch.py`** — downloads feeds (via `requests`, or `urllib` as a
  fallback) and parses both RSS 2.0 and Atom with the standard‑library XML parser.
- **`cybernews/summarize.py`** — strips HTML and builds a short, faithful summary
  from the source's own text.
- **`cybernews/aggregator.py`** — deduplicates, applies the time window, tags
  Belgium‑relevant stories, and ranks results.
- **`cybernews/render.py`** — produces the terminal / Markdown / HTML / JSON output.
- **`cybernews/cli.py`** + **`main.py`** — the command‑line agent.

---

## ✅ Tests

The pipeline is fully testable offline (no network needed) using a bundled RSS
fixture:

```bash
python tests/test_pipeline.py      # no dependencies
# or
pytest -q tests/
```

CI runs these on every push via
[`.github/workflows/tests.yml`](.github/workflows/tests.yml).

---

## 📝 Notes & honesty

- Summaries are **extractive** (the lead of each article as the source wrote it),
  not AI‑paraphrased, so nothing is fabricated. For the authoritative and complete
  story, always follow the **"Read the full article"** link to the official site.
- This tool only reads **public feeds**; it does not bypass paywalls or scrape.
- Respect each outlet's terms of use when redistributing their content.

## 📄 License

Released under the MIT License — see [`LICENSE`](LICENSE).
