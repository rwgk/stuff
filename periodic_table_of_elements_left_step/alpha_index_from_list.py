#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alpha_index_from_list.svg
-------------------------
Build a single SVG panel sized for ~2500x1000, flowing a one-column list
into newspaper-style columns.

INPUT
  alpha_one_column.txt
    • Lines are either section headers ("A".."Z", "Special"), one intentional
      blank spacer line, or element rows like:
        89 Ac Actinium

OUTPUT
  alpha_index_from_list.svg

STYLE
  • Headers: bold, larger
  • Element rows: mini cell (ℓ-block color, Z top-left, centered symbol) + name
  • Colors and geometry aligned with your left-step style, all inline (no CSS)
"""

from pathlib import Path
import re
from typing import List, Tuple

# ---------------- CONFIG ----------------
IN_TXT  = Path("alpha_one_column.txt")
OUT_SVG = Path("alpha_index_from_list.svg")

# Target panel size (2500 x 1000)
WIDTH, HEIGHT = 2500, 1360

# Try these column counts and pick whichever packs best
CANDIDATE_COLS = [8]

# Margins and gaps
PADDING_X = 40
PADDING_Y = 40
COL_GAP   = 40

# Mini cell geometry (match your left-step look)
CELL_W, CELL_H = 60, 36
CELL_RX, CELL_RY = 6, 6
CELL_STROKE = "#222"
CELL_STROKE_W = 1.0

# Typography
FONT_FAMILY = "Inter, Arial, Helvetica, sans-serif"
NAME_SIZE   = 22
NUM_SIZE    = 12
SYM_SIZE    = 16
HEADER_SIZE = 26
HEADER_WEIGHT = 700

# Offsets
ANUM_DX, ANUM_DY = 5, 13
SYM_CENTER_DY = 0.78  # fraction of CELL_H for symbol vertical placement
ROW_GAP   = 10        # space between element rows
HDR_GAP   = 10        # space under header lines

# ℓ-block colors (0=s, 1=p, 2=d, 3=f)
BLOCK_FILLS = {
    3: "#f3e8ff",  # f-block
    2: "#e0f2fe",  # d-block
    1: "#dcfce7",  # p-block
    0: "#fee2e2",  # s-block
}

# Ideal Aufbau subshell sequence to compute last-filled ℓ
# Entries: (n, ℓ, capacity)
SUBSHELLS = [
    (1,0,2),
    (2,0,2), (2,1,6),
    (3,0,2), (3,1,6),
    (4,0,2), (3,2,10), (4,1,6),
    (5,0,2), (4,2,10), (5,1,6),
    (6,0,2), (4,3,14), (5,2,10), (6,1,6),
    (7,0,2), (5,3,14), (6,2,10), (7,1,6),
]

# ---------------- Helpers ----------------

def ell_for_Z(Z: int) -> int:
    filled = 0
    for _n, ell, cap in SUBSHELLS:
        for _ in range(cap):
            filled += 1
            if filled == Z:
                return ell
    return 0

def parse_lines(lines: List[str]):
    """Return a list of items:
       ('header', text)     — section headers A..Z, 'Special'
       ('spacer', '')       — intentional blank spacer line
       ('elem', Z, sym, name) for rows like '89 Ac Actinium'
    """
    items = []
    for raw in lines:
        s = raw.strip()
        if not s:
            items.append(("spacer", ""))
            continue
        if s == "Special" or (len(s) == 1 and s.isalpha() and s.isupper()):
            items.append(("header", s))
            continue
        m = re.match(r'^\s*(\d+)\s+([A-Za-z]{1,3})\s+(.+?)\s*$', s)
        if not m:
            # Unknown line; treat as header to avoid losing it
            items.append(("header", s))
            continue
        Z = int(m.group(1))
        sym = m.group(2)
        name = m.group(3)
        items.append(("elem", Z, sym, name))
    return items

def measure_heights(items: List[tuple]) -> List[int]:
    """Compute per-item heights used for packing into columns."""
    row_h = max(CELL_H, NAME_SIZE) + ROW_GAP
    heights = []
    for kind, *rest in items:
        if kind == "header":
            heights.append(HEADER_SIZE + HDR_GAP)
        elif kind == "spacer":
            heights.append(ROW_GAP)  # treat spacer as a small gap
        else:
            heights.append(row_h)
    return heights

def pack_columns(items: List[tuple], heights: List[int], cols: int):
    """Greedy pack items into 'cols' columns, top->bottom, left->right,
       without exceeding available column height (except the first item)."""
    usable_h = HEIGHT - 2 * PADDING_Y
    slices = []
    start = 0
    for c in range(cols):
        y = 0
        i = start
        while i < len(items):
            h = heights[i]
            # If adding this item exceeds the column height and we still have columns, wrap
            if y > 0 and (y + h) > usable_h and c < cols - 1:
                break
            y += h
            i += 1
        slices.append((start, i))
        start = i
        if start >= len(items):
            # fill remaining slice entries as empty
            for _ in range(c + 1, cols):
                slices.append((start, start))
            break
    return slices

def choose_best_cols(items: List[tuple], heights: List[int]):
    """Try candidate column counts; prefer no overflow, then minimal leftover."""
    usable_h = HEIGHT - 2 * PADDING_Y
    best = None
    for cols in CANDIDATE_COLS:
        slices = pack_columns(items, heights, cols)
        last_start, last_end = slices[-1]
        used_last = sum(heights[last_start:last_end])
        leftover = max(0, usable_h - used_last)
        overflow = 0 if last_end == len(items) else sum(heights[last_end:])
        score = (overflow, leftover)
        if best is None or score < best[0]:
            best = (score, cols, slices)
    return best[1], best[2]

def col_positions(cols: int):
    inner_w = WIDTH - 2 * PADDING_X - (cols - 1) * COL_GAP
    cw = inner_w / cols
    xs = [PADDING_X + i * (cw + COL_GAP) for i in range(cols)]
    return xs, cw

# ---------------- SVG primitives ----------------

def draw_cell(Z: int, sym: str, x: float, y: float) -> str:
    """Mini element cell: colored rect, Z top-left, symbol centered."""
    ell = ell_for_Z(Z)
    fill = BLOCK_FILLS.get(ell, "none")
    sym_y = y + CELL_H * SYM_CENTER_DY
    return (
        f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" '
        f'rx="{CELL_RX}" ry="{CELL_RY}" '
        f'style="fill:{fill};stroke:{CELL_STROKE};stroke-width:{CELL_STROKE_W};" />\n'
        f'<text x="{x + ANUM_DX}" y="{y + ANUM_DY}" '
        f'style="font:{NUM_SIZE}px {FONT_FAMILY};fill:#111;">{Z}</text>\n'
        f'<text x="{x + CELL_W/2}" y="{sym_y}" text-anchor="middle" '
        f'style="font:{SYM_SIZE}px {FONT_FAMILY};font-weight:600;fill:#111;">{sym}</text>'
    )

def name_text(name: str, x: float, y_mid: float) -> str:
    return (
        f'<text x="{x}" y="{y_mid}" dominant-baseline="middle" '
        f'style="font:{NAME_SIZE}px {FONT_FAMILY};font-weight:600;fill:#111;">{name}</text>'
    )

def header_text(text, x, y_top):
    return (
        f'<text x="{x}" y="{y_top}" dominant-baseline="hanging" '
        f'style="font:{HEADER_SIZE}px {FONT_FAMILY};font-weight:{HEADER_WEIGHT};fill:#111;">{text}</text>'
    )

# ---------------- Build SVG ----------------

def build_svg(items: List[tuple]) -> str:
    heights = measure_heights(items)
    cols, slices = choose_best_cols(items, heights)
    xs, cw = col_positions(cols)

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}">')
    out.append('<g id="alpha-index-from-list">')

    for c, (i0, i1) in enumerate(slices):
        x0 = xs[c]
        y = PADDING_Y
        for idx in range(i0, i1):
            kind, *rest = items[idx]
            if kind == "header":
                out.append(header_text(rest[0], x0, y - 16))
                y += HEADER_SIZE + HDR_GAP
            elif kind == "spacer":
                y += ROW_GAP
            else:
                Z, sym, name = rest
                # Draw cell slightly above baseline so Z top-left sits nicely
                cell_y = y - (CELL_H - NUM_SIZE)
                out.append(draw_cell(Z, sym, x0, cell_y))
                # Name centered vertically to the cell
                name_x = x0 + CELL_W + 16
                name_y = cell_y + CELL_H * 0.5
                out.append(name_text(name, name_x, name_y))
                y += max(CELL_H, NAME_SIZE) + ROW_GAP

    out.append('</g>')
    out.append('</svg>')
    return "\n".join(out)

def main():
    lines = IN_TXT.read_text(encoding="utf-8").splitlines()
    items = parse_lines(lines)
    svg = build_svg(items)
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT_SVG.resolve()}")

if __name__ == "__main__":
    main()
