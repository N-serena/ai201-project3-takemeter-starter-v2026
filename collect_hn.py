#!/usr/bin/env python3
"""
Collect Hacker News comments into a pool to label.

    python collect_hn.py                      # broad sweep of the recent feed
    python collect_hn.py --query "benchmark" --append
    python collect_hn.py --report             # what's in the pool already

Writes `pool.csv`: unlabelled posts with an id, so labelling is a separate
step from collecting and the corpus is reproducible.

Three filters, each of which shows up in the dataset write-up:

**25 to 95 words.** A profile of 300 raw comments put the median at 30 words,
with 23% under 15 and 12% over 95. The short ones carry no stance to learn and
the long ones are truncated at MAX_LENGTH=128 anyway, so the band is the part
of the feed worth labelling.

**At most 3 comments per story.** Forty comments off one thread teaches the
model that thread's vocabulary, and near-identical arguments landing in
different splits is leakage by another name.

**Whitespace collapsed to single spaces.** Every word is kept; paragraph breaks
are not. It makes the CSV editable in a spreadsheet, and at 128 tokens the
model cannot tell the difference.

The `source` column records which sweep a post came from. A broad sweep gives
the feed's natural label distribution; a `--query` sweep deliberately skews it
to top up a thin label. Those are different things and the README has to say
which posts came from which.
"""

import argparse
import csv
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass

RECENT = "https://hn.algolia.com/api/v1/search_by_date"
RELEVANT = "https://hn.algolia.com/api/v1/search"

FIELDS = ["id", "text", "words", "story", "source"]

TAG = re.compile(r"<[^>]+>")
PARA = re.compile(r"</p>\s*<p>|<p>")


def clean(raw):
    """HN comment HTML to one line of plain text."""
    text = PARA.sub(" ", raw or "")
    text = TAG.sub("", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


#   The API serves at most 1000 hits per query — nbPages comes back as 10 and
#   page 10 onward is empty. One sweep of the recent feed therefore tops out
#   around 160 posts once the per-story cap has taken its share. The way past
#   it is time windows: each window is a separate query with its own 1000-hit
#   budget, so the sweep stays broad instead of being skewed toward a topic.
MAX_PAGES = 10


def fetch_page(base, page, query=None, numeric_filters=None):
    params = {"tags": "comment", "hitsPerPage": "100", "page": str(page)}
    if query:
        params["query"] = query
    if numeric_filters:
        params["numericFilters"] = numeric_filters
    url = f"{base}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "ai201-takemeter-coursework"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def sweep_once(base, query, numeric_filters, pages, min_words, max_words, label):
    rows = []
    for page in range(min(pages, MAX_PAGES)):
        try:
            data = fetch_page(base, page, query, numeric_filters)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] page {page} failed ({exc}) — stopping this sweep")
            break
        hits = data.get("hits", [])
        if not hits:
            break
        for hit in hits:
            text = clean(hit.get("comment_text"))
            words = len(text.split())
            if not (min_words <= words <= max_words):
                continue
            rows.append({
                "id": hit.get("objectID"),
                "text": text,
                "words": words,
                "story": (hit.get("story_title") or "").strip(),
                "source": label,
            })
        time.sleep(0.3)  # the API is free; don't hammer it
    return rows


def sweep(pages, query, min_words, max_words, windows, window_hours):
    """Fetch, clean and filter across one or more time windows."""
    base = RELEVANT if query else RECENT
    label = query if query else "broad"
    now = int(time.time())
    span = window_hours * 3600

    rows = []
    for w in range(windows):
        end, start = now - w * span, now - (w + 1) * span
        filters = None if windows == 1 else f"created_at_i>={start},created_at_i<{end}"
        got = sweep_once(base, query, filters, pages, min_words, max_words, label)
        if windows > 1:
            print(f"  window {w + 1}/{windows}: {len(got)} in band")
        rows.extend(got)
    return rows


def load(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def save(path, rows):
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def normalise(text):
    """For duplicate detection: case and punctuation shouldn't hide a repeat."""
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def merge(existing, incoming, per_story):
    """Add incoming rows, skipping duplicates and over-represented stories."""
    seen_ids = {r["id"] for r in existing}
    seen_text = {normalise(r["text"]) for r in existing}
    per = Counter(r["story"] for r in existing)

    kept, dup, capped = [], 0, 0
    for row in incoming:
        if row["id"] in seen_ids or normalise(row["text"]) in seen_text:
            dup += 1
            continue
        if row["story"] and per[row["story"]] >= per_story:
            capped += 1
            continue
        seen_ids.add(row["id"])
        seen_text.add(normalise(row["text"]))
        per[row["story"]] += 1
        kept.append(row)
    return kept, dup, capped


def report(rows):
    if not rows:
        print("pool.csv is empty or missing. Run a sweep first.")
        return
    words = sorted(int(r["words"]) for r in rows)
    stories = Counter(r["story"] for r in rows)
    print(f"{len(rows)} posts in the pool")
    print(f"  words      median {words[len(words) // 2]}, range {words[0]}-{words[-1]}")
    print(f"  stories    {len(stories)} distinct, at most {max(stories.values())} per story")
    print("  by sweep")
    for source, n in Counter(r["source"] for r in rows).most_common():
        print(f"    {source:<28} {n}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", type=int, default=MAX_PAGES,
                    help=f"100 comments per page; the API caps a query at {MAX_PAGES}")
    ap.add_argument("--windows", type=int, default=1,
                    help="split the sweep into this many time windows, each with its own 1000-hit budget")
    ap.add_argument("--window-hours", type=int, default=24)
    ap.add_argument("--query", help="topic sweep instead of the recent feed")
    ap.add_argument("--per-story", type=int, default=3)
    ap.add_argument("--min-words", type=int, default=25)
    ap.add_argument("--max-words", type=int, default=95)
    ap.add_argument("--out", default="pool.csv", type=Path)
    ap.add_argument("--append", action="store_true", help="add to the pool instead of replacing it")
    ap.add_argument("--report", action="store_true", help="describe the pool and exit")
    args = ap.parse_args()

    if args.report:
        report(load(args.out))
        return 0

    existing = load(args.out) if args.append else []
    incoming = sweep(args.pages, args.query, args.min_words, args.max_words,
                     args.windows, args.window_hours)
    kept, dup, capped = merge(existing, incoming, args.per_story)

    save(args.out, existing + kept)

    print(f"fetched {len(incoming)} in the {args.min_words}-{args.max_words} word band")
    print(f"  kept       {len(kept)}")
    print(f"  duplicate  {dup}")
    print(f"  over the {args.per_story}-per-story cap: {capped}")
    print()
    report(existing + kept)
    return 0


if __name__ == "__main__":
    sys.exit(main())
