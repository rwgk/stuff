#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alphabetical index panels with mini element cells (color + Z + symbol).

- Main panel: sorted by SYMBOL with letter headers, 3 columns.
- Mismatch panel: only entries where first letter of symbol != first letter of name,
  sorted by NAME, compact 2 columns.
- Mini cell styling mirrors the left-step table: background color by ℓ-block,
  small atomic number at top-left, symbol centered.

Outputs:
  element_alpha_index_by_symbol_cells.svg
  element_name_symbol_mismatches_cells.svg
"""

from pathlib import Path
from typing import List, Tuple
from collections import defaultdict

# ---------- CONFIG (shared) ----------
FONT_FAMILY = "Inter, Arial, Helvetica, sans-serif"

# Colors per ℓ-block (0=s,1=p,2=d,3=f) — match your left-step table
BLOCK_FILLS = {
    3: "#f3e8ff",  # f-block
    2: "#e0f2fe",  # d-block
    1: "#dcfce7",  # p-block
    0: "#fee2e2",  # s-block
}

# Mini cell geometry (keep consistent with left-step table feel)
CELL_W = 44
CELL_H = 28
CELL_RX = 4
CELL_RY = 4
CELL_STROKE = "#222"
CELL_STROKE_W = 0.9

# Text sizes/offsets (align with your table if desired)
NUM_SIZE = 10
SYM_SIZE = 13
ANUM_DX = 4
ANUM_DY = 11
SYM_CENTER_DY = 0.78  # fraction of CELL_H, e.g., 0.78

NAME_FONT = 18
MONO_FONT = 18  # for aligned Z/symbol columns (if needed)

# ---------- CONFIG (main panel) ----------
OUT_MAIN = Path("element_alpha_index_by_symbol_cells.svg")
WIDTH_MAIN = 1200
PADDING_MAIN = 32
COLS_MAIN = 3
COL_GAP_MAIN = 40
HEADER_SIZE = 22
HEADER_SPACING = 10
LINE_GAP = 8  # extra gap below each row

PANEL_TITLE = "Alphabetical Index by Element Symbol"
TITLE_SIZE = 24
TITLE_GAP = 18

# ---------- CONFIG (mismatch panel) ----------
OUT_MIS = Path("element_name_symbol_mismatches_cells.svg")
WIDTH_MIS = 900
PADDING_MIS = 24
COLS_MIS = 2
COL_GAP_MIS = 30
TITLE_MIS = "Element names whose first letter ≠ symbol's first letter"
TITLE_SIZE_MIS = 22
TITLE_GAP_MIS = 14

# ---------- Data ----------
ELEMENTS: List[Tuple[int, str, str]] = [
    (1,"H","Hydrogen"),(2,"He","Helium"),(3,"Li","Lithium"),(4,"Be","Beryllium"),
    (5,"B","Boron"),(6,"C","Carbon"),(7,"N","Nitrogen"),(8,"O","Oxygen"),(9,"F","Fluorine"),(10,"Ne","Neon"),
    (11,"Na","Sodium"),(12,"Mg","Magnesium"),(13,"Al","Aluminium"),(14,"Si","Silicon"),(15,"P","Phosphorus"),(16,"S","Sulfur"),
    (17,"Cl","Chlorine"),(18,"Ar","Argon"),(19,"K","Potassium"),(20,"Ca","Calcium"),
    (21,"Sc","Scandium"),(22,"Ti","Titanium"),(23,"V","Vanadium"),(24,"Cr","Chromium"),(25,"Mn","Manganese"),(26,"Fe","Iron"),
    (27,"Co","Cobalt"),(28,"Ni","Nickel"),(29,"Cu","Copper"),(30,"Zn","Zinc"),
    (31,"Ga","Gallium"),(32,"Ge","Germanium"),(33,"As","Arsenic"),(34,"Se","Selenium"),(35,"Br","Bromine"),(36,"Kr","Krypton"),
    (37,"Rb","Rubidium"),(38,"Sr","Strontium"),(39,"Y","Yttrium"),(40,"Zr","Zirconium"),(41,"Nb","Niobium"),(42,"Mo","Molybdenum"),
    (43,"Tc","Technetium"),(44,"Ru","Ruthenium"),(45,"Rh","Rhodium"),(46,"Pd","Palladium"),(47,"Ag","Silver"),(48,"Cd","Cadmium"),
    (49,"In","Indium"),(50,"Sn","Tin"),(51,"Sb","Antimony"),(52,"Te","Tellurium"),(53,"I","Iodine"),(54,"Xe","Xenon"),
    (55,"Cs","Cesium"),(56,"Ba","Barium"),(57,"La","Lanthanum"),(58,"Ce","Cerium"),(59,"Pr","Praseodymium"),(60,"Nd","Neodymium"),
    (61,"Pm","Promethium"),(62,"Sm","Samarium"),(63,"Eu","Europium"),(64,"Gd","Gadolinium"),(65,"Tb","Terbium"),(66,"Dy","Dysprosium"),
    (67,"Ho","Holmium"),(68,"Er","Erbium"),(69,"Tm","Thulium"),(70,"Yb","Ytterbium"),(71,"Lu","Lutetium"),
    (72,"Hf","Hafnium"),(73,"Ta","Tantalum"),(74,"W","Tungsten"),(75,"Re","Rhenium"),(76,"Os","Osmium"),(77,"Ir","Iridium"),
    (78,"Pt","Platinum"),(79,"Au","Gold"),(80,"Hg","Mercury"),(81,"Tl","Thallium"),(82,"Pb","Lead"),(83,"Bi","Bismuth"),
    (84,"Po","Polonium"),(85,"At","Astatine"),(86,"Rn","Radon"),
    (87,"Fr","Francium"),(88,"Ra","Radium"),(89,"Ac","Actinium"),(90,"Th","Thorium"),(91,"Pa","Protactinium"),(92,"U","Uranium"),
    (93,"Np","Neptunium"),(94,"Pu","Plutonium"),(95,"Am","Americium"),(96,"Cm","Curium"),(97,"Bk","Berkelium"),
    (98,"Cf","Californium"),(99,"Es","Einsteinium"),(100,"Fm","Fermium"),(101,"Md","Mendelevium"),(102,"No","Nobelium"),
    (103,"Lr","Lawrencium"),(104,"Rf","Rutherfordium"),(105,"Db","Dubnium"),(106,"Sg","Seaborgium"),(107,"Bh","Bohrium"),
    (108,"Hs","Hassium"),(109,"Mt","Meitnerium"),(110,"Ds","Darmstadtium"),(111,"Rg","Roentgenium"),(112,"Cn","Copernicium"),
    (113,"Nh","Nihonium"),(114,"Fl","Flerovium"),(115,"Mc","Moscovium"),(116,"Lv","Livermorium"),(117,"Ts","Tennessine"),
    (118,"Og","Oganesson"),
]

# ---------- Compute ℓ-block (last-filled subshell) per Z ----------
SUBSHELLS = [
    (1,0,"1s",2),
    (2,0,"2s",2),
    (2,1,"2p",6),
    (3,0,"3s",2),
    (3,1,"3p",6),
    (4,0,"4s",2),
    (3,2,"3d",10),
    (4,1,"4p",6),
    (5,0,"5s",2),
    (4,2,"4d",10),
    (5,1,"5p",6),
    (6,0,"6s",2),
    (4,3,"4f",14),
    (5,2,"5d",10),
    (6,1,"6p",6),
    (7,0,"7s",2),
    (5,3,"5f",14),
    (6,2,"6d",10),
    (7,1,"7p",6),
]

def l_block_for_Z(z: int) -> int:
    """Return ℓ (0=s,1=p,2=d,3=f) for the last-filled subshell of element Z (ideal Aufbau)."""
    filled = 0
    for n, l_block, label, cap in SUBSHELLS:
        for _ in range(cap):
            filled += 1
            if filled == z:
                return l_block
    return 0

# ---------- Layout helpers ----------
def group_by_symbol_first_letter(data):
    g = defaultdict(list)
    for z, sym, name in data:
        g[sym[0].upper()].append((z, sym, name))
    for k in g:
        g[k].sort(key=lambda t: (t[1].lower(), t[2].lower()))
    letters = sorted(g.keys())
    return g, letters

def greedy_columns(letters, grouped, cols, include_headers=True, header_weight=1):
    sections = []
    for L in letters:
        lines = (header_weight if include_headers else 0) + len(grouped[L])
        sections.append((L, lines))
    buckets = [[] for _ in range(cols)]
    heights = [0]*cols
    for L, lines in sections:
        i = min(range(cols), key=lambda c: heights[c])
        buckets[i].append(L)
        heights[i] += lines
    return buckets

# ---------- Renderers ----------
def svg_header(width, height, extra_css=""):
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">\n'
        '<defs>\n'
        '<style><![CDATA[\n'
        f'.title {{ font:{TITLE_SIZE}px {FONT_FAMILY}; font-weight:600; fill:#111; }}\n'
        f'.title_mis {{ font:{TITLE_SIZE_MIS}px {FONT_FAMILY}; font-weight:600; fill:#111; }}\n'
        f'.hdr {{ font:{HEADER_SIZE}px {FONT_FAMILY}; font-weight:600; fill:#111; }}\n'
        f'.name {{ font:{NAME_FONT}px {FONT_FAMILY}; font-weight:600; fill:#111; }}\n'
        f'.anum {{ font:{NUM_SIZE}px {FONT_FAMILY}; fill:#111; }}\n'
        f'.sym  {{ font:{SYM_SIZE}px {FONT_FAMILY}; font-weight:600; fill:#111; }}\n'
        f'.cell {{ stroke:{CELL_STROKE}; stroke-width:{CELL_STROKE_W}; }}\n'
        f'.sym_mis {{ font:{NAME_FONT}px {FONT_FAMILY}; font-weight:700; fill:#111; }}\n'
        + extra_css +
        '\n]]></style>\n'
        '</defs>\n'
    )

def draw_mini_cell(z, sym, x, y):
    """Return SVG snippets for a mini cell at (x,y)."""
    lblock = l_block_for_Z(z)
    fill = BLOCK_FILLS.get(lblock, "none")
    parts = []
    parts.append(f'<rect class="cell" x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" '
                 f'rx="{CELL_RX}" ry="{CELL_RY}" fill="{fill}" />')
    parts.append(f'<text class="anum" x="{x + ANUM_DX}" y="{y + ANUM_DY}">{z}</text>')
    sym_y = y + CELL_H * SYM_CENTER_DY
    parts.append(f'<text class="sym" x="{x + CELL_W/2}" y="{sym_y}" text-anchor="middle">{sym}</text>')
    return "\n".join(parts)

# ---------- Build main (by symbol) ----------
def build_main():
    grouped, letters = group_by_symbol_first_letter(ELEMENTS)
    buckets = greedy_columns(letters, grouped, COLS_MAIN, include_headers=True, header_weight=1)

    total_gap = (COLS_MAIN - 1) * COL_GAP_MAIN
    inner_w = WIDTH_MAIN - 2*PADDING_MAIN - total_gap
    col_w = inner_w / COLS_MAIN

    # rough vertical metrics
    row_h = max(CELL_H, NAME_FONT) + LINE_GAP

    # temp height; patched later
    parts = [svg_header(WIDTH_MAIN, 100)]
    parts.append('<g id="alpha-index-by-symbol-cells">')

    y = PADDING_MAIN
    if PANEL_TITLE:
        parts.append(f'<text class="title" x="{PADDING_MAIN}" y="{y}">{PANEL_TITLE}</text>')
        y += TITLE_SIZE + TITLE_GAP

    col_x = [PADDING_MAIN + i*(col_w + COL_GAP_MAIN) for i in range(COLS_MAIN)]
    col_y = [y]*COLS_MAIN

    for ci, letters_in_col in enumerate(buckets):
        x0 = col_x[ci]
        y0 = col_y[ci]
        for L in letters_in_col:
            rows = grouped[L]
            parts.append(f'<text class="hdr" x="{x0}" y="{y0}">{L}</text>')
            y0 += HEADER_SIZE + HEADER_SPACING
            for z, sym, name in rows:
                # mini cell on the left; name to the right
                cell_y = y0 - (CELL_H - NUM_SIZE)
                parts.append(draw_mini_cell(z, sym, x0, cell_y))  # slight vertical align
                name_x = x0 + CELL_W + 14
                name_y = cell_y + (CELL_H * 0.50) + 1
                parts.append(f'<text class="name" x="{name_x}" y="{name_y}" dominant-baseline="middle">{name}</text>')
                y0 += row_h
        col_y[ci] = y0

    parts.append('</g>')
    height = max(col_y) + PADDING_MAIN
    parts[0] = svg_header(WIDTH_MAIN, height)
    parts.append('</svg>')
    return "\n".join(parts), (WIDTH_MAIN, height)

# ---------- Build mismatch (name vs symbol first letter) ----------
def build_mismatch():
    mismatches = [(z,sym,name) for (z,sym,name) in ELEMENTS if sym[0].upper() != name[0].upper()]
    mismatches.sort(key=lambda t: t[2].lower())  # by name

    total_gap = (COLS_MIS - 1) * COL_GAP_MIS
    inner_w = WIDTH_MIS - 2*PADDING_MIS - total_gap
    col_w = inner_w / COLS_MIS

    row_h = max(CELL_H, NAME_FONT) + 6

    parts = [svg_header(WIDTH_MIS, 100)]
    parts.append('<g id="alpha-index-mismatches-cells">')

    y = PADDING_MIS
    if TITLE_MIS:
        parts.append(f'<text class="title_mis" x="{PADDING_MIS}" y="{y}">{TITLE_MIS}</text>')
        y += TITLE_SIZE_MIS + TITLE_GAP_MIS

    per_col = (len(mismatches) + COLS_MIS - 1) // COLS_MIS
    columns = [mismatches[i*per_col:(i+1)*per_col] for i in range(COLS_MIS)]

    col_x = [PADDING_MIS + i*(col_w + COL_GAP_MIS) for i in range(COLS_MIS)]
    col_y = [y]*COLS_MIS

    for ci, rows in enumerate(columns):
        x0 = col_x[ci]
        y0 = col_y[ci]
        for z, sym, name in rows:
            cell_y = y0 - (CELL_H - NUM_SIZE)
            parts.append(draw_mini_cell(z, sym, x0, cell_y))
            name_x = x0 + CELL_W + 14
            name_y = cell_y + (CELL_H * 0.50) + 1
            parts.append(f'<text class="name" x="{name_x}" y="{name_y}" dominant-baseline="middle">{name}</text>')
            y0 += row_h
        col_y[ci] = y0

    parts.append('</g>')
    height = max(col_y) + PADDING_MIS
    parts[0] = svg_header(WIDTH_MIS, height)
    parts.append('</svg>')
    return "\n".join(parts), (WIDTH_MIS, height)

def main():
    svg_main, _ = build_main()
    OUT_MAIN.write_text(svg_main, encoding="utf-8")
    svg_mis, _ = build_mismatch()
    OUT_MIS.write_text(svg_mis, encoding="utf-8")
    print(f"Wrote {OUT_MAIN.resolve()} and {OUT_MIS.resolve()}")

if __name__ == "__main__":
    main()
