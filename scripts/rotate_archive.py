#!/usr/bin/env python3
"""Rotate briefings older than KEEP_DAYS into archive/YYYY-MM.json.

Keeps briefings/ flat at ~14 files while leaving every past edition
reachable from the dashboard (index.html falls back to the archive on 404).

Usage:  python3 scripts/rotate_archive.py [--keep 14] [--dry-run]
"""
import argparse, json, os, sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEF = os.path.join(ROOT, "briefings")
ARCH = os.path.join(ROOT, "archive")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", type=int, default=14,
                    help="days of briefings to leave in briefings/ (default 14)")
    ap.add_argument("--today", help="override today's date, YYYY-MM-DD")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    today = date.fromisoformat(a.today) if a.today else date.today()
    cutoff = today - timedelta(days=a.keep - 1)

    idx_path = os.path.join(BRIEF, "index.json")
    idx = load(idx_path)
    dates = sorted(set(idx.get("dates", [])))

    live = [d for d in os.listdir(BRIEF) if d.endswith(".json") and d != "index.json"]
    to_move = sorted(d[:-5] for d in live if date.fromisoformat(d[:-5]) < cutoff)

    if not to_move:
        print(f"rotate: nothing older than {cutoff.isoformat()}; {len(live)} live briefings")
    else:
        by_month = {}
        for ds in to_move:
            by_month.setdefault(ds[:7], []).append(ds)

        for month, ds_list in sorted(by_month.items()):
            ap_path = os.path.join(ARCH, month + ".json")
            bundle = load(ap_path) if os.path.exists(ap_path) else {}
            for ds in ds_list:
                bundle[ds] = load(os.path.join(BRIEF, ds + ".json"))
            bundle = {k: bundle[k] for k in sorted(bundle)}
            if a.dry_run:
                print(f"rotate: would write {len(ds_list)} -> archive/{month}.json")
                continue
            save(ap_path, bundle)
            for ds in ds_list:
                os.remove(os.path.join(BRIEF, ds + ".json"))
            print(f"rotate: moved {len(ds_list)} -> archive/{month}.json")

    # index.json keeps EVERY date so prev/next walks full history.
    archived = sorted(
        k for m in (os.listdir(ARCH) if os.path.isdir(ARCH) else [])
        if m.endswith(".json") for k in load(os.path.join(ARCH, m))
    )
    all_dates = sorted(set(dates) | set(archived) |
                       {d[:-5] for d in os.listdir(BRIEF)
                        if d.endswith(".json") and d != "index.json"})
    if not all_dates:
        sys.exit("rotate: no briefings found; refusing to write empty index")
    new_idx = {"latest": max(all_dates), "dates": all_dates, "archived": archived}
    if a.dry_run:
        print("rotate: would write index.json ->", json.dumps(new_idx)[:120])
    else:
        save(idx_path, new_idx)
        print(f"rotate: index.json {len(all_dates)} dates, "
              f"{len(archived)} archived, latest {new_idx['latest']}")


if __name__ == "__main__":
    main()
