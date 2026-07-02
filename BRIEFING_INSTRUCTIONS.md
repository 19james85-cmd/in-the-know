# Daily Briefing Runbook — In the Know: Cybersecurity

You are generating today's cybersecurity daily briefing for this repository's
dashboard. Follow every step exactly. The dashboard renders whatever you commit,
so accuracy matters more than volume.

## Step 1 — Date

Compute today's date in **America/Los_Angeles** as `YYYY-MM-DD`. This is the
briefing date used everywhere below.

## Step 2 — Gather candidates

```
python3 scripts/fetch_feeds.py --hours 24 --out /tmp/candidates.json
```

- If the script exits **non-zero** (every feed failed): **STOP. Commit nothing.**
  The dashboard gracefully shows the previous day.
- Read `/tmp/candidates.json`. Individual failed feeds listed in `feeds[]` are
  normal (Cyber Defense Magazine is usually blocked); work with what succeeded.
- If fewer than 10 items total, re-run with `--hours 36`.

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
  an accurate body paragraph.
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
3. For each, append `{"t","c","d","e"}`:
   - `c` from exactly: Vulnerability, Threat/Actor, Malware, Network,
     Regulatory, Cryptography, General
   - `d`: 1–2 plain-English sentences for an absolute beginner
   - `e`: one concrete, realistic example sentence
4. Keep the array sorted by `t` (case-insensitive). **Never modify or delete
   existing entries.**

## Step 8 — Commit and push

```
git add briefings/ glossary.json
git commit -m "Daily briefing YYYY-MM-DD"
git push origin main
```

Only ever commit `briefings/*` and `glossary.json`. Never commit
`candidates.json` or changes to any other file.
