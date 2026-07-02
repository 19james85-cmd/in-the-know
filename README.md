# In the Know — Cybersecurity Daily Briefing

A self-updating daily cybersecurity briefing dashboard. Every morning a
scheduled Claude agent gathers the last 24 hours of news from ten curated
sources (via `scripts/fetch_feeds.py`), writes a structured briefing to
`briefings/YYYY-MM-DD.json` following `BRIEFING_INSTRUCTIONS.md`, grows
`glossary.json` with new beginner-friendly terms, and pushes to this repo.
GitHub Pages serves the result.

## Reading it

Open the GitHub Pages URL (bookmark it / add to your phone's home screen).
The dashboard loads today's briefing automatically; use the `‹ ›` buttons in
the header to browse previous days.

## Local preview

`fetch()` of the JSON files doesn't work from `file://`, so serve the folder:

```
# Windows
py -m http.server 8000
# macOS
python3 -m http.server 8000
```

then open http://localhost:8000

## Layout

```
index.html                 the dashboard (all styling + rendering)
glossary.json              beginner glossary; auto-grows nightly
briefings/index.json       {"latest": "...", "dates": [...]}
briefings/YYYY-MM-DD.json  one briefing per day, kept forever
scripts/fetch_feeds.py     stdlib-only RSS fetcher (10 sources)
BRIEFING_INSTRUCTIONS.md   the nightly agent's runbook
legacy/                    earlier hand-operated versions of the dashboard
```

## Manually generating a briefing

If a morning run ever fails, run the runbook by hand in a Claude Code session
from the repo root: *"Read BRIEFING_INSTRUCTIONS.md and follow it exactly."*
