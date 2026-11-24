"""Palette figure and README table from battery v2. Model-free.

    uv run python scripts/figure.py          # write figures/palette.svg and the README table
    uv run python scripts/figure.py --check  # fail if either differs from what the data gives

Counts are re-derived from the raw answers in data/battery_v2/battery_instruct.json and must equal
data/battery_v2/analysis.json. Styling comes from the Warm Precision kit (vendor/warm-precision-kit).
The swatch colors stand in for the color words; here color is the subject, so the kit's one-accent rule
is set aside for the swatches only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor/warm-precision-kit"))
import figures as wp  # noqa: E402
from lfm3lab.synesthesia import COLORS  # noqa: E402
from lfm3lab.synesthesia_stimuli import CANONICAL  # noqa: E402

_spec = importlib.util.spec_from_file_location("battery_v1", ROOT / "scripts/battery_v1.py")
bat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bat)

DATA = ROOT / "data/battery_v2"
SVG = ROOT / "figures/palette.svg"
README = ROOT / "README.md"
START, END = "<!-- palette-table:start -->", "<!-- palette-table:end -->"
ROWS = ["black", "gray", "white", "brown", "red", "orange", "yellow", "green", "blue", "purple", "pink"]
FULL = 0.30                     # share that fills a cell
CELL, LABEL_W, TOP = 48, 76, 40


def counts():
    runs = json.loads((DATA / "battery_instruct.json").read_text())["runs"]["name|sample"]
    analysis = json.loads((DATA / "analysis.json").read_text())
    A, _ = bat.to_digit_rows(runs, bat.parse_name)
    n = len(runs)
    out = {}
    for d in range(10):
        c = Counter(a if a is not None else "unparsed" for a in A[:, d])
        assert dict(c) == analysis["per_digit"][str(d)]["sampled_counts"], d
        out[d] = c
    assert n == analysis["n_runs"] == 1000
    return out, n


def svg(cnt, n):
    theme = wp.Theme(json.loads((ROOT / "vendor/warm-precision-kit/tokens.json").read_text()))
    assert sorted(ROWS) == sorted(COLORS)
    top = max(cnt[d][c] / n for d in range(10) for c in ROWS)
    assert top < FULL, top
    width, height = LABEL_W + 10 * CELL + 8, TOP + len(ROWS) * CELL + 8
    alt = ("Grid of ten digits by eleven basic color words. Square area is the share of 1,000 sampled answers "
           "naming that color for that digit; a full square is 30%. Black is large for 0 and 8 and small elsewhere. "
           "Purple is largest for 9 and 7. White and blue are near-equal for 1; yellow leads for 2 and 4.")
    parts = [wp._open(theme, width, height, "palette", "Colors LFM3-1.7B names for each digit", alt),
             f'<rect width="{width}" height="{height}" fill="{theme["canvas"]}"/>']
    for d in range(10):
        parts.append(wp._text(theme, LABEL_W + d * CELL + CELL / 2, TOP - 14, str(d), anchor="middle", weight=600))
    inner = CELL - 6
    for r, c in enumerate(ROWS):
        y = TOP + r * CELL
        parts.append(wp._text(theme, LABEL_W - 12, y + CELL / 2 + 5.5, c, anchor="end", color="text-secondary"))
        rgb = "#" + "".join(f"{v:02x}" for v in CANONICAL[c])
        for d in range(10):
            x = LABEL_W + d * CELL
            parts.append(f'<rect x="{x + 3}" y="{y + 3}" width="{inner}" height="{inner}" fill="{theme["structure"]}" '
                         f'fill-opacity="{theme.track_opacity}"/>')
            share = cnt[d][c] / n
            if share:
                s = inner * math.sqrt(share / FULL)
                parts.append(f'<rect x="{x + CELL / 2 - s / 2:.2f}" y="{y + CELL / 2 - s / 2:.2f}" width="{s:.2f}" '
                             f'height="{s:.2f}" fill="{rgb}" stroke="{theme["structure"]}" stroke-width="1"/>')
    return "".join(parts) + "</svg>\n"


def table(cnt, n):
    lines = ["| Digit | Most named | Second |", "| ---: | --- | --- |"]
    for d in range(10):
        (a, ka), (b, kb) = [(c, k) for c, k in cnt[d].most_common() if c in COLORS][:2]
        lines.append(f"| {d} | {a} {wp.fmt(100 * ka / n, decimals=1, kind='percent')} "
                     f"| {b} {wp.fmt(100 * kb / n, decimals=1, kind='percent')} |")
    return "\n".join([START, *lines, END])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    cnt, n = counts()
    new_svg, new_table = svg(cnt, n), table(cnt, n)
    readme = README.read_text()
    assert readme.count(START) == 1 and readme.count(END) == 1
    old_table = readme[readme.index(START):readme.index(END) + len(END)]
    if args.check:
        ok = SVG.exists() and SVG.read_text() == new_svg and old_table == new_table
        print("figure and README table match the data" if ok else "figure or README table is out of date")
        raise SystemExit(0 if ok else 1)
    SVG.parent.mkdir(exist_ok=True)
    SVG.write_text(new_svg)
    README.write_text(readme.replace(old_table, new_table))
    print("wrote", SVG.relative_to(ROOT), "and the README table")


if __name__ == "__main__":
    main()
