#!/usr/bin/env python3
"""Fetch recent items from the In the Know source RSS feeds.

Stdlib only — no installs needed. Produces a candidates JSON file that the
nightly briefing agent selects stories from.

Usage:
    python3 scripts/fetch_feeds.py [--hours 24] [--out candidates.json]

Exit codes: 0 if at least one feed succeeded, 1 if every feed failed.
"""
import argparse
import gzip
import io
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

# Source names must match the SRC list in index.html so source badges line up.
FEEDS = [
    ("CISA", "https://www.cisa.gov/cybersecurity-advisories/all.xml"),
    ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
    ("Cybersecurity Dive", "https://www.cybersecuritydive.com/feeds/news/"),
    ("SecurityWeek", "https://feeds.feedburner.com/securityweek"),
    ("Dark Reading", "https://www.darkreading.com/rss.xml"),
    ("CyberScoop", "https://cyberscoop.com/feed/"),
    ("Cyber Defense Magazine", "https://www.cyberdefensemagazine.com/feed/"),
    ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
    ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
    # csrc.nist.gov has no working RSS; NIST's cybersecurity topic feed stands in.
    ("NIST (CSRC)", "https://www.nist.gov/news-events/cybersecurity/rss.xml"),
]

# Several feeds (BleepingComputer especially) reject non-browser user agents.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
TIMEOUT = 20
MAX_PER_FEED = 15
SUMMARY_CHARS = 500

ATOM = "{http://www.w3.org/2005/Atom}"


def http_get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        "Accept-Encoding": "gzip",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip" or data[:2] == b"\x1f\x8b":
                data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
            return data
    except urllib.error.HTTPError as err:
        if err.code != 403:
            raise
        # Some CDNs (e.g. Akamai on cisa.gov) 403 Python's TLS fingerprint but
        # accept curl's. curl ships with Windows 10+ and every Linux image.
        return curl_get(url, err)


def curl_get(url, original_err):
    try:
        proc = subprocess.run(
            ["curl", "-s", "-f", "--compressed", "--max-time", str(TIMEOUT),
             "-A", UA, url],
            capture_output=True, timeout=TIMEOUT + 5, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        raise original_err
    if proc.returncode != 0 or not proc.stdout:
        raise original_err
    return proc.stdout


def strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&#8217;|&rsquo;", "'", text)
    text = re.sub(r"&#\d+;|&\w+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:SUMMARY_CHARS]


def parse_date(s):
    """Parse RFC 822 (RSS) or ISO 8601 (Atom) dates to aware UTC datetimes."""
    if not s:
        return None
    s = s.strip()
    try:
        dt = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def first_text(el, *tags):
    for tag in tags:
        node = el.find(tag)
        if node is not None and node.text:
            return node.text
    return None


def parse_feed(xml_bytes):
    """Yield (title, url, published_dt, summary) from RSS 2.0 or Atom."""
    root = ET.fromstring(xml_bytes)
    if root.tag.endswith("feed"):  # Atom
        for entry in root.iter(ATOM + "entry"):
            title = first_text(entry, ATOM + "title")
            link = None
            for l in entry.findall(ATOM + "link"):
                if l.get("rel") in (None, "alternate"):
                    link = l.get("href")
                    break
            published = first_text(entry, ATOM + "published", ATOM + "updated")
            summary = first_text(entry, ATOM + "summary", ATOM + "content")
            yield title, link, parse_date(published), strip_html(summary)
    else:  # RSS 2.0 (root <rss> or <rdf>)
        for item in root.iter("item"):
            title = first_text(item, "title")
            link = first_text(item, "link")
            published = first_text(item, "pubDate",
                                   "{http://purl.org/dc/elements/1.1/}date")
            summary = first_text(item, "description")
            yield title, link, parse_date(published), strip_html(summary)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--out", default="candidates.json")
    args = ap.parse_args()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    feed_status, items = [], []

    for source, url in FEEDS:
        try:
            entries = []
            for title, link, published, summary in parse_feed(http_get(url)):
                if not title or not link:
                    continue
                if published is None or published < cutoff:
                    continue
                entries.append({
                    "source": source,
                    "title": strip_html(title),
                    "url": link.strip(),
                    "published": published.isoformat(),
                    "summary": summary,
                })
            entries.sort(key=lambda e: e["published"], reverse=True)
            entries = entries[:MAX_PER_FEED]
            items.extend(entries)
            feed_status.append({"source": source, "ok": True,
                                "count": len(entries), "error": None})
        except Exception as exc:  # noqa: BLE001 — any single feed may fail
            feed_status.append({"source": source, "ok": False,
                                "count": 0, "error": f"{type(exc).__name__}: {exc}"})

    items.sort(key=lambda e: e["published"], reverse=True)
    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "window_hours": args.hours,
        "feeds": feed_status,
        "items": items,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    ok = [f for f in feed_status if f["ok"]]
    print(f"{len(ok)}/{len(FEEDS)} feeds OK, {len(items)} items "
          f"in last {args.hours}h -> {args.out}", file=sys.stderr)
    for f in feed_status:
        mark = "ok " if f["ok"] else "ERR"
        detail = f["count"] if f["ok"] else f["error"]
        print(f"  [{mark}] {f['source']}: {detail}", file=sys.stderr)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
