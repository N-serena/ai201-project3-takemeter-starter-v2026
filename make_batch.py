#!/usr/bin/env python3
"""
Carve a batch of unlabelled posts out of the pool.

    python make_batch.py --n 20 --note cold --out cold_batch.csv
    python make_batch.py --n 60 --note "pre-labelled, checked" --out batch_02.csv

Writes `id,text,label,note` with `label` left empty for you to fill in.

The draw is random but seeded, so the same command gives the same batch. That
matters for the first 20: picking posts yourself means picking the ones you
already know how to label, and the point of the cold batch is to find out what
the feed's real distribution is and which boundaries are genuinely hard.

Anything already labelled is excluded. Pass `--exclude` for batches that are
out being worked on, so two batches never contain the same post.
"""

import argparse
import csv
import random
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass

FIELDS = ["id", "text", "label", "note"]


def read(path):
    if not path or not Path(path).exists():
        return []
    with Path(path).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def normalise(text):
    return re.sub(r"[^a-z0-9 ]", "", (text or "").lower()).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--pool", default="pool.csv", type=Path)
    ap.add_argument("--labels", default="labels.csv", type=Path,
                    help="already-labelled posts, excluded from the draw")
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="other batch files to exclude")
    ap.add_argument("--note", default="cold", help="goes in the note column")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="cold_batch.csv", type=Path)
    args = ap.parse_args()

    pool = read(args.pool)
    if not pool:
        sys.exit(f"No posts in {args.pool}. Run collect_hn.py first.")

    taken_ids, taken_text = set(), set()
    for source in [args.labels, *args.exclude]:
        for row in read(source):
            if row.get("id"):
                taken_ids.add(row["id"])
            taken_text.add(normalise(row.get("text")))

    available = [
        r for r in pool
        if r["id"] not in taken_ids and normalise(r["text"]) not in taken_text
    ]
    if len(available) < args.n:
        sys.exit(f"Only {len(available)} unlabelled posts available, asked for {args.n}.")

    batch = random.Random(args.seed).sample(available, args.n)

    with args.out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for row in batch:
            writer.writerow({"id": row["id"], "text": row["text"],
                             "label": "", "note": args.note})

    print(f"wrote {args.out} - {args.n} posts, label column empty")
    print(f"  drawn from {len(available)} unlabelled of {len(pool)} in the pool")
    print(f"  seed {args.seed}, note {args.note!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
