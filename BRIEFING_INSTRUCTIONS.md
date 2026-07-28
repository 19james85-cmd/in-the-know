# Daily Briefing Runbook — In the Know: Cybersecurity

You are generating today's cybersecurity daily briefing for this repository's
dashboard. Follow every step exactly. The dashboard renders whatever you commit,
so accuracy matters more than volume.

## Step 1 — Date

Compute today's date in **America/Los_Angeles** as `YYYY-MM-DD`. This is the
briefing date used everywhere below.

## Step 2 — Get candidates

The **fetch-feeds GitHub Actions workflow** commits fresh candidates to
`data/candidates.json` shortly before this routine runs (~12:40 UTC daily).
This environment's outbound network is usually restricted, so prefer the
committed file over fetching yourself.

1. Read `data/candidates.json` and check its `generated` timestamp.
2. If it is **less than 12 hours old**, use it.
3. If it is missing or stale, try
   `python3 scripts/fetch_feeds.py --hours 24 --out /tmp/candidates.json`
   and use that output instead. If the script exits non-zero AND the
   committed candidates are stale or missing: **STOP. Commit nothing.**
   The dashboard gracefully shows the previous day.
4. Individual failed feeds listed in `feeds[]` are normal (Cyber Defense
   Magazine is usually blocked); work with what succeeded.

## Step 3 — Select stories

From the candidate items only:

- **1 lead story** — the single most consequential item. Active exploitation,
  CISA KEV additions, and emergency directives outrank everything else.
- **3–4 CVE/exploit stories**
- **3 threat actor / ransomware stories**
- **3 regulatory / compliance stories**
- **3 industry trend stories**
- **5 quick hits** (one-sentence items; may overlap with stories above)

Rules:
- **Never invent URLs, CVE numbers, CVSS scores, or facts.** Every claim must
  come from a candidate item or a page you actually fetched.
- Use WebFetch on the top story URLs when the RSS summary is too thin to write
  an accurate body paragraph. If outbound network access is restricted (fetches
  fail), write accurate, appropriately-hedged bodies from the RSS titles and
  summaries alone — do not pad with invented specifics.
- If a category is thin that day, include fewer real items rather than padding
  with stale or fabricated content.
- `source` must be exactly one of: CISA, The Hacker News, Cybersecurity Dive,
  SecurityWeek, Dark Reading, CyberScoop, Cyber Defense Magazine,
  BleepingComputer, Krebs on Security, NIST (CSRC).

## Step 4 — Write the briefing JSON

Exact schema (same shape the dashboard has always used):

```json
{
  "leadStory": {"headline":"","source":"","sourceUrl":"","url":"","tags":[{"label":"","type":"d|w|a|g"}],"body":"","beginnerTip":""},
  "cves": [3-4 objects, same shape as leadStory],
  "threatActors": [3 objects],
  "regulatory": [3 objects],
  "trends": [3 objects],
  "quickHits": [{"color":"danger|warn|accent|ok","source":"","sourceUrl":"","text":""}],
  "analystFooter": ""
}
```

- Tag types — `d`: danger/red (critical CVSS 8+, actively exploited, emergency
  directives). `w`: warn/amber (medium severity, no patch available). `a`:
  accent/blue (informational, frameworks, legislation, standard trends). `g`:
  ok/green (positive developments).
- `url` = the actual article link; `sourceUrl` = the outlet's homepage.
- `body`: 2–4 sentences, plain text. Naturally use glossary terms (CVE, KEV,
  Ransomware, …) where accurate — the dashboard auto-links them.
- `beginnerTip`: 1–3 sentences for an absolute beginner; may use `<strong>`
  around one key term. No other HTML.
- `analystFooter`: one sentence of practical, prioritized guidance for the day.

## Step 5 — Validate

```
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert all(k in d for k in ['leadStory','cves','threatActors','regulatory','trends','quickHits','analystFooter']), 'missing keys'; print('valid')" briefings/YYYY-MM-DD.json
```

## Step 6 — Write files

1. Save the briefing as `briefings/YYYY-MM-DD.json` (today's date). If it
   already exists, overwrite it — reruns are idempotent.
2. Update `briefings/index.json`:
   - Insert today's date into `dates` if absent; keep `dates` sorted ascending.
   - Set `latest` to the maximum date in `dates`.

## Step 7 — Grow the glossary

1. Read `glossary.json` (array of `{"t","c","d","e"}` = term, category,
   definition, example).
2. Find up to **3** beginner-relevant cybersecurity terms that appear in
   today's stories but are **not** already present (case-insensitive compare
   against `t`).
3. Keep `t` **short and matchable** — the dashboard auto-links glossary terms
   by whole-string match against story bodies. "Path Traversal" links;
   "Path traversal (../ sequences)" never will.
4. For each, append `{"t","c","d","e"}`:
   - `c` from exactly: Vulnerability, Threat/Actor, Malware, Network,
     Regulatory, Cryptography, General
   - `d`: 1–2 plain-English sentences for an absolute beginner
   - `e`: one concrete, realistic example sentence
5. Keep the array sorted by `t` (case-insensitive). **Never modify or delete
   existing entries.**
6. Rebuild the lightweight index the dashboard loads on every page view:

   ```
   python3 scripts/build_glossary_index.py
   ```

   This writes `glossary-index.json` (term + category only, ~4K). The full
   `glossary.json` with definitions is fetched lazily, only when a reader
   clicks a term or opens the Glossary tab — so page weight stays flat as the
   glossary grows. The script also fails loudly on duplicate terms, which is
   your check that step 2 didn't re-add something.

## Step 8 — Rotate the archive

`briefings/` holds a rolling **14 days**. Anything older moves into a
month bundle so the directory stays flat:

```
python3 scripts/rotate_archive.py
```

This moves stale briefings into `archive/YYYY-MM.json`, then rewrites
`briefings/index.json` with `latest`, the full `dates` list, and `archived`.
Nothing is lost — `dates` still contains **every** date ever published, and the
dashboard falls back to `archive/YYYY-MM.json` when a briefing isn't in
`briefings/`. Prev/next still walks the whole history.

Run this **after** writing today's briefing and **before** committing. It is
idempotent; re-running it is safe. Use `--dry-run` to preview.

## Step 9 — Commit and push

```
git add briefings/ archive/ glossary.json glossary-index.json
git commit -m "Daily briefing YYYY-MM-DD"
git push origin main
```

Only ever commit those four paths. Never commit `data/candidates.json`,
`index.html`, or the token file.
