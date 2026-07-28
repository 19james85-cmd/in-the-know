#!/usr/bin/env python3
"""Emit glossary-index.json: term + category only.

The dashboard downloads this on every page load to auto-link terms in story
bodies. The full glossary.json (with definitions and examples) is fetched
lazily, only when a reader clicks a term or opens the Glossary tab -- so page
weight stays flat no matter how many terms the glossary grows to.

Usage:  python3 scripts/build_glossary_index.py
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "glossary.json")
OUT = os.path.join(ROOT, "glossary-index.json")

with open(SRC, encoding="utf-8") as f:
    gl = json.load(f)

seen, dupes = set(), []
for e in gl:
    k = e["t"].lower()
    if k in seen:
        dupes.append(e["t"])
    seen.add(k)
if dupes:
    sys.exit(f"duplicate terms in glossary.json: {dupes}")

light = sorted(({"t": e["t"], "c": e["c"]} for e in gl),
               key=lambda e: e["t"].lower())
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(light, f, ensure_ascii=False, separators=(",", ":"))
    f.write("\n")

print(f"glossary-index.json: {len(light)} terms, "
      f"{os.path.getsize(OUT)/1024:.1f}K (full: {os.path.getsize(SRC)/1024:.1f}K)")
