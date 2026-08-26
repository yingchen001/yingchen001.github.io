#!/usr/bin/env python3
"""Add abbr={...} (and award={Oral}) to each entry in _bibliography/papers.bib.

The venue abbreviation is derived from the existing journal=/booktitle= string
so the badge in _layouts/bib.html can key into _data/venues.yml. A trailing
", Oral" is stripped from the venue string and re-expressed as award={Oral}.

Idempotent: entries that already have abbr= are left alone.
"""
import re
import sys

BIB = "_bibliography/papers.bib"

# Ordered: first match wins, so the more specific patterns come first.
RULES = [
    (r"arXiv preprint", "arXiv"),
    (r"Pattern Analysis and Machine Intelligence|TPAMI", "TPAMI"),
    (r"Transactions on Image Processing|\(TIP\)", "TIP"),
    (r"Transactions on Multimedia", "TMM"),
    (r"Winter Conference on Applications of Computer Vision|WACV", "WACV"),
    (r"Neural Information Processing Systems|NeurIPS", "NeurIPS"),
    (r"Learning Representations|ICLR", "ICLR"),
    (r"AAAI", "AAAI"),
    (r"ACM International Conference on Multimedia|ACM MM", "ACM MM"),
    (r"ECCV|European Conference", "ECCV"),
    (r"[Cc]onference on [Cc]omputer [Vv]ision and [Pp]attern [Rr]ecognition|CVPR", "CVPR"),
    (r"[Ii]nternational [Cc]onference on [Cc]omputer [Vv]ision|ICCV", "ICCV"),
]

text = open(BIB).read()
entries = re.split(r"\n(?=@)", text)
out, stats = [], {}

for blk in entries:
    key_m = re.match(r"@\w+\{([^,]+),", blk)
    if not key_m:
        out.append(blk)
        continue
    key = key_m.group(1)

    if re.search(r"^\s*abbr\s*=", blk, re.M):
        out.append(blk)
        continue

    venue_m = re.search(r"^\s*(journal|booktitle|school)\s*=\s*\{(.*)\},?\s*$", blk, re.M)
    if not venue_m:
        print(f"  !! no venue field: {key}", file=sys.stderr)
        out.append(blk)
        continue
    venue = venue_m.group(2)

    abbr = next((a for pat, a in RULES if re.search(pat, venue)), None)
    if not abbr:
        print(f"  !! unmatched venue for {key}: {venue[:70]}", file=sys.stderr)
        out.append(blk)
        continue

    inject = [f"  abbr={{{abbr}}}"]

    # ", Oral" belongs in a separate award badge, not in the venue string.
    if re.search(r",\s*Oral\s*$", venue):
        cleaned = re.sub(r",\s*Oral\s*$", "", venue)
        blk = blk.replace("{" + venue + "}", "{" + cleaned + "}", 1)
        inject.append("  award={Oral}")

    # Insert right after the @type{key, line so the fields stay grouped.
    blk = re.sub(r"(@\w+\{[^,]+,\n)", r"\1" + ",\n".join(inject) + ",\n", blk, count=1)
    out.append(blk)
    stats[abbr] = stats.get(abbr, 0) + 1

open(BIB, "w").write("\n".join(out))
print(f"tagged {sum(stats.values())} entries:",
      ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
