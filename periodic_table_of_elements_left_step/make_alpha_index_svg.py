#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate an alphabetical element index as a standalone SVG panel.

Outputs:
  element_alpha_index.svg  (standalone SVG)

Embed tip:
  - The root <svg> includes a <g id="alpha-index"> node wrapping content.
  - You can copy that group into your poster SVG, or import as an external asset.
"""

from pathlib import Path
from collections import defaultdict
from typing import List, Tuple

# -------- CONFIG --------
OUT_SVG = Path("element_alpha_index.svg")
WIDTH = 1200        # overall SVG width (px)
PADDING = 32        # outer padding (px)
COLS = 3            # number of columns
COL_GAP = 40        # gap between columns (px)
FONT_FAMILY = "Inter, Arial, Helvetica, sans-serif"
FONT_SIZE = 18      # element line font size
HEADER_SIZE = 22    # letter header font size
LINE_H = 26         # line height (px)
HEADER_SPACING = 10 # extra space below letter header (px)
SHOW_SYMBOLS = True  # include chemical symbols inline (after Z)
SHOW_LETTER_HEADERS = True  # show A, B, C... section headers

# Optional intro title for the panel (set to "" to hide)
PANEL_TITLE = "Alphabetical Index of Elements"
TITLE_SIZE = 24
TITLE_GAP = 18  # gap under title

# Data: (Z, Symbol, Name) for Z=1..118 (IUPAC current names)
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

def group_and_sort(elements):
    from collections import defaultdict
    g = defaultdict(list)
    for z, sym, name in elements:
        g[name[0].upper()].append((z, sym, name))
    for k in g:
        g[k].sort(key=lambda t: t[2])
    letters = sorted(g.keys())
    return g, letters

def compute_layout(letters, grouped, cols):
    # compute line counts per section
    sections = []
    for L in letters:
        lines = 1 + len(grouped[L]) if SHOW_LETTER_HEADERS else len(grouped[L])
        sections.append((L, lines))
    # greedy balance into columns
    buckets = [[] for _ in range(cols)]
    heights = [0]*cols
    for L, lines in sections:
        i = min(range(cols), key=lambda c: heights[c])
        buckets[i].append(L)
        heights[i] += lines
    return buckets

def build_svg():
    grouped, letters = group_and_sort(ELEMENTS)
    col_letters = compute_layout(letters, grouped, COLS)

    total_gap = (COLS - 1) * COL_GAP
    inner_width = WIDTH - 2 * PADDING - total_gap
    col_width = inner_width / COLS

    y = PADDING
    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="100">')  # temp height

    parts.append('<defs>')
    parts.append('<style><![CDATA['
                 f'.title {{ font:{TITLE_SIZE}px {FONT_FAMILY}; font-weight:600; fill:#111; }}\n'
                 f'.hdr {{ font:{HEADER_SIZE}px {FONT_FAMILY}; font-weight:600; fill:#111; }}\n'
                 f'.row {{ font:{FONT_SIZE}px {FONT_FAMILY}; fill:#111; }}\n'
                 f'.mono {{ font:{FONT_SIZE}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; fill:#111; }}\n'
                 ']]></style>')
    parts.append('</defs>')

    parts.append('<g id="alpha-index">')

    # Title
    if PANEL_TITLE:
        parts.append(f'<text class="title" x="{PADDING}" y="{y}">{PANEL_TITLE}</text>')
        y += TITLE_SIZE + TITLE_GAP

    col_x0 = [PADDING + i * (col_width + COL_GAP) for i in range(COLS)]
    col_y = [y]*COLS

    for ci, letters_in_col in enumerate(col_letters):
        x0 = col_x0[ci]
        y0 = col_y[ci]
        for L in letters_in_col:
            rows = grouped[L]
            if SHOW_LETTER_HEADERS:
                parts.append(f'<text class="hdr" x="{x0}" y="{y0}">{L}</text>')
                y0 += HEADER_SIZE + HEADER_SPACING
            for z, sym, name in rows:
                x_num = x0
                x_sym = x0 + 70
                x_name = x0 + (110 if SHOW_SYMBOLS else 80)
                parts.append(
                    f'<text class="row" y="{y0}">'
                    f'<tspan class="mono" x="{x_num}">{z:>3}</tspan>'
                    + (f'<tspan class="mono" x="{x_sym}">{sym}</tspan>' if SHOW_SYMBOLS else '')
                    + f'<tspan x="{x_name}">{name}</tspan>'
                    f'</text>'
                )
                y0 += LINE_H
        col_y[ci] = y0

    parts.append('</g>')

    height = max(col_y) + PADDING
    parts[1] = f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}">'
    parts.append('</svg>')
    return "\n".join(parts), (WIDTH, height)

def main():
    svg, size = build_svg()
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT_SVG.resolve()} size={size}")

if __name__ == "__main__":
    main()
