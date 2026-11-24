"""Palette grid, answer mosaic and README table from battery v2. Model-free.

    uv run python scripts/figure.py          # write figures/palette.svg, figures/mosaic.svg and the README table
    uv run python scripts/figure.py --check  # fail if any of them differs from what the data gives

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
MOSAIC = ROOT / "figures/mosaic.svg"
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
    return runs, out, n


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


def mosaic(runs, cnt):
    """One equal tile per saved answer. Run r sits at column r // 10, row r % 10 of its digit's band."""
    theme = wp.Theme(json.loads((ROOT / "vendor/warm-precision-kit/tokens.json").read_text()))
    tw, th, left, top, band = 6, 4, 40, 8, 48
    fills = {c: "#" + "".join(f"{v:02x}" for v in CANONICAL[c]) for c in ROWS}
    other = theme["well"]
    paths = {c: [] for c in [*ROWS, "rest"]}
    drawn = {d: Counter() for d in range(10)}
    for r, run in enumerate(runs):
        col, row = divmod(r, 10)
        for d, answer in zip(run["order"], run["answers"]):
            d = int(d)
            c = bat.parse_name(answer)
            drawn[d][c if c is not None else "unparsed"] += 1
            paths[c if c in COLORS else "rest"].append(f"M{left + col * tw} {top + d * band + row * th}h{tw}v{th}h-{tw}z")
    assert drawn == cnt and all(sum(drawn[d].values()) == len(runs) for d in range(10))
    legend_y = top + 10 * band + 24
    width, height = left + 100 * tw + 8, legend_y + 3 * 32 + 4
    alt = ("Ten horizontal bands, one per digit from 0 to 9. Each band holds all 1,000 sampled answers for that digit, "
           "one equal tile per answer, in run order down each column and then left to right. Basic color words use "
           "stand-in colors; off-palette and unparsed answers are beige. Black tiles fill much of the 0 and 8 bands, "
           "purple much of 7 and 9, and every band mixes many colors.")
    parts = [wp._open(theme, width, height, "mosaic", "Every answer LFM3-1.7B gave, one tile each", alt),
             f'<rect width="{width}" height="{height}" fill="{theme["canvas"]}"/><g shape-rendering="crispEdges">']
    for c, d_ in paths.items():
        parts.append(f'<path fill="{fills.get(c, other)}" d="{"".join(d_)}"/>')
    parts.append("</g>")
    for d in range(10):
        y = top + d * band
        parts.append(wp._text(theme, left - 12, y + 10 * th / 2 + 5.5, str(d), anchor="end", weight=600))
        parts.append(f'<rect x="{left - 0.5}" y="{y - 0.5}" width="{100 * tw + 1}" height="{10 * th + 1}" fill="none" '
                     f'stroke="{theme["context"]}" stroke-width="1"/>')
    keys = [*ROWS, "other or unparsed"]
    for i, c in enumerate(keys):
        row, col = divmod(i, 6) if i < len(ROWS) else (2, 0)
        x, y = left + col * 100, legend_y + row * 32
        parts.append(f'<rect x="{x}" y="{y - 13}" width="16" height="16" rx="2" fill="{fills.get(c, other)}" '
                     f'stroke="{theme["context"]}" stroke-width="1"/>')
        parts.append(wp._text(theme, x + 24, y, c, color="text-secondary"))
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
    runs, cnt, n = counts()
    new_svg, new_mosaic, new_table = svg(cnt, n), mosaic(runs, cnt), table(cnt, n)
    readme = README.read_text()
    assert readme.count(START) == 1 and readme.count(END) == 1
    old_table = readme[readme.index(START):readme.index(END) + len(END)]
    if args.check:
        ok = (SVG.exists() and SVG.read_text() == new_svg and MOSAIC.exists() and MOSAIC.read_text() == new_mosaic
              and old_table == new_table)
        print("figures and README table match the data" if ok else "a figure or the README table is out of date")
        raise SystemExit(0 if ok else 1)
    SVG.parent.mkdir(exist_ok=True)
    SVG.write_text(new_svg)
    MOSAIC.write_text(new_mosaic)
    README.write_text(readme.replace(old_table, new_table))
    print("wrote", SVG.relative_to(ROOT), MOSAIC.relative_to(ROOT), "and the README table")


if __name__ == "__main__":
    main()
