#!/usr/bin/env python3
"""Entry point for the cybersecurity news agent.

Examples
--------
    python main.py                      # print today's digest to the terminal
    python main.py --format all         # also write Markdown, HTML and JSON
    python main.py --since-hours 48     # widen the time window
"""

from cybernews.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
