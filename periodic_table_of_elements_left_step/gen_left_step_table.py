#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a fully vectorized periodic table in the Bent & Weinhold
(Madelung-tier, t = n + ℓ) format.

Based on:
  F. Weinhold and H. A. Bent (2019),
  "Periodicity, Symbols, Tables, and Models for Higher-Order Valency
  and Donor–Acceptor Kinships",
  *Foundations of Chemistry*, 21, 213–229.
  https://www.researchgate.net/publication/331412871
"""

# Quick tweaks: edit CONFIG below — cell sizes, colors, fonts, offsets,
# title text/position, and whether to show s/p/d/f block arrows.

from pathlib import Path
from typing import List, Tuple, Dict

# ========== CONFIG ==========
OUT_SVG = Path("left_step_table_madelung_vector_gen.svg")  # change path if desired

CONFIG = {
    # Canvas paddings
    "PAD_L": 120,
    "PAD_T": 100,
    "PAD_R": 20,
    "PAD_B": 30,
    # Cell geometry
    "CELL_W": 32,
    "CELL_H": 32,
    "CELL_RX": 4,  # rounded corner x
    "CELL_RY": 4,  # rounded corner y
    "CELL_STROKE": "#222",
    "CELL_STROKE_W": 0.9,
    # Fonts
    "FONT_FAMILY": "Inter, Arial, Helvetica, sans-serif",
    "NUM_SIZE": 10,
    "SYM_SIZE": 13,
    "NAME_SIZE": 8,  # only used if show_name=True
    "LABEL_SIZE": 14,
    # Content toggles
    "show_name": False,  # set True if you add names (see ELEMENT_NAMES placeholder)
    "show_block_arrows": True,
    # Text colors
    "TEXT_PRIMARY": "#111",
    "TEXT_SUBTLE": "#444",
    "GUIDE_STROKE": "#888",
    # Title
    "TITLE_TEXT": "Periodic Table of Elements — Left-step Bent &amp; Weinhold format — Madelung-tier arrangement (t = n + ℓ)",
    "TITLE_Y": 36,  # absolute SVG coordinate
    # Colors per ℓ-block (background fill for cells) — tweak freely
    # l: 0=s, 1=p, 2=d, 3=f
    "BLOCK_FILLS": {
        3: "#f3e8ff",  # f-block
        2: "#e0f2fe",  # d-block
        1: "#dcfce7",  # p-block
        0: "#fee2e2",  # s-block
    },
    "BLOCK_HEADER_TEXT": {
        3: "f (ℓ=3)",
        2: "d (ℓ=2)",
        1: "p (ℓ=1)",
        0: "s (ℓ=0)",
    },
    # Relative offsets within each cell (fine-tune positioning)
    "OFFSETS": {
        "anum_dx": 4,  # atomic number x offset from cell left
        "anum_dy": 11,  # atomic number y offset from cell top
        "sym_center_dy": 0.78,  # multiplier of CELL_H (e.g., 0.78 → lower half)
        "name_center_dy": 0.86,  # used if show_name=True
    },
    # Block header label offsets
    "BLOCK_HDR_DY": 34,  # distance above the grid to place block labels
    "BLOCK_RULE_DY": 27,  # position for faint line under block label
    # Row label text
    "ROW_LABEL_PREFIX": "t = ",
    # Arrow styling (used if show_block_arrows=True)
    "ARROW_Y_OFFSET": 24,  # distance below grid bottom where arrows are drawn
    "ARROW_STROKE": "#444",
    "ARROW_STROKE_W": 1.2,
    "ARROW_HEAD_SIZE": 6,  # marker size (px)
}

# Optional: element names (only used if CONFIG['show_name'] = True).
# To use names, fill this dict: ELEMENT_NAMES[Z] = "Hydrogen", etc.
# For brevity it's left empty here; you can paste a mapping later.
ELEMENT_NAMES: Dict[int, str] = {}

# Symbols Z=1..118 (index 0 unused)
SYMBOLS: List[str] = [
    None,
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
]

# Subshell filling (ideal Aufbau) up to 7p
# entries: (n, l, label, capacity)
SUBSHELLS: List[Tuple[int, int, str, int]] = [
    (1, 0, "1s", 2),
    (2, 0, "2s", 2),
    (2, 1, "2p", 6),
    (3, 0, "3s", 2),
    (3, 1, "3p", 6),
    (4, 0, "4s", 2),
    (3, 2, "3d", 10),
    (4, 1, "4p", 6),
    (5, 0, "5s", 2),
    (4, 2, "4d", 10),
    (5, 1, "5p", 6),
    (6, 0, "6s", 2),
    (4, 3, "4f", 14),
    (5, 2, "5d", 10),
    (6, 1, "6p", 6),
    (7, 0, "7s", 2),
    (5, 3, "5f", 14),
    (6, 2, "6d", 10),
    (7, 1, "7p", 6),
]

# ℓ-block definitions left→right (f, d, p, s) for left-step
# dict key "l" == azimuthal quantum number ℓ (0=s,1=p,2=d,3=f)
BLOCK_DEFS = [
    {"l": 3, "width": 14},
    {"l": 2, "width": 10},
    {"l": 1, "width": 6},
    {"l": 0, "width": 2},
]


def compute_layout():
    """Compute positions for Z=1..118 in left-step layout by last-filled subshell.
    Returns:
        placements: dict[Z] -> dict with keys:
            n, l, subshell, e, t, col_in_block, col (overall), row (t-index)
        t_min, t_max, total_cols
        x_start: dict[l] -> starting column for that block
    """
    Z_MAX = 118
    placements = {}
    # compute block start columns
    x_start = {}
    total_cols = 0
    for blk in BLOCK_DEFS:
        x_start[blk["l"]] = total_cols
        total_cols += blk["width"]

    Z = 0
    for n, l_block, label, cap in SUBSHELLS:
        for e in range(1, cap + 1):
            Z += 1
            if Z > Z_MAX:
                break
            placements[Z] = {
                "n": n,
                "l": l_block,
                "subshell": label,
                "e": e,
                "t": n + l_block,
                "col_in_block": e - 1,
            }
        if Z > Z_MAX:
            break

    t_vals = sorted({info["t"] for info in placements.values()})
    t_min, t_max = min(t_vals), max(t_vals)

    # convert to overall col/row
    for Z, info in placements.items():
        l_block = info["l"]
        col = x_start[l_block] + info["col_in_block"]
        row = info["t"] - t_min
        info["col"] = col
        info["row"] = row

    return placements, t_min, t_max, total_cols, x_start


def svg_header(w, h, cfg):
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
    )
    lines.append("  <defs>")
    lines.append('    <style type="text/css"><![CDATA[')
    lines.append(
        f"      .cell {{ fill: none; stroke: {cfg['CELL_STROKE']}; stroke-width: {cfg['CELL_STROKE_W']}; }}"
    )
    lines.append(
        f"      .anum {{ font: {cfg['NUM_SIZE']}px {cfg['FONT_FAMILY']}; fill: {cfg['TEXT_PRIMARY']}; }}"
    )
    lines.append(
        f"      .sym  {{ font: {cfg['SYM_SIZE']}px {cfg['FONT_FAMILY']}; font-weight: 600; fill: {cfg['TEXT_PRIMARY']}; }}"
    )
    lines.append(
        f"      .name {{ font: {cfg['NAME_SIZE']}px {cfg['FONT_FAMILY']}; fill: {cfg['TEXT_SUBTLE']}; }}"
    )
    lines.append(
        f"      .blocklbl {{ font: {cfg['LABEL_SIZE']}px {cfg['FONT_FAMILY']}; font-weight: 600; fill: {cfg['TEXT_PRIMARY']}; }}"
    )
    lines.append(
        f"      .rowlbl {{ font: {cfg['LABEL_SIZE']}px {cfg['FONT_FAMILY']}; font-weight: 600; fill: {cfg['TEXT_PRIMARY']}; }}"
    )
    lines.append(
        f"      .guide {{ stroke: {cfg['GUIDE_STROKE']}; stroke-dasharray: 2 3; }}"
    )
    lines.append(
        f"      .arrowlbl {{ font: {cfg['LABEL_SIZE']}px {cfg['FONT_FAMILY']}; font-weight: 600; fill: {cfg['TEXT_PRIMARY']}; }}"
    )
    lines.append(
        f"      .arrowline {{ stroke: {cfg['ARROW_STROKE']}; stroke-width: {cfg['ARROW_STROKE_W']}; "
        f"fill: none; marker-start: url(#arrow); marker-end: url(#arrow); }}"
    )
    lines.append("    ]]></style>")
    lines.append("")
    lines.append(
        '    <marker id="arrow" viewBox="0 0 10 10" '
        f'markerWidth="{cfg["ARROW_HEAD_SIZE"]}" markerHeight="{cfg["ARROW_HEAD_SIZE"]}" '
        'refX="10" refY="5" orient="auto-start-reverse" markerUnits="strokeWidth">'
    )
    lines.append(
        f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{cfg["ARROW_STROKE"]}"/>'
    )
    lines.append("    </marker>")
    lines.append("  </defs>")
    return "\n".join(lines) + "\n"


def svg_footer():
    return "</svg>\n"


def build_svg():
    cfg = CONFIG
    placements, t_min, t_max, total_cols, x_start = compute_layout()

    # Dimensions
    cols = total_cols
    rows = t_max - t_min + 1
    W = cfg["PAD_L"] + cols * cfg["CELL_W"] + cfg["PAD_R"]
    H = (
        cfg["PAD_T"]
        + rows * cfg["CELL_H"]
        + cfg["PAD_B"]
        + (cfg["ARROW_Y_OFFSET"] if cfg["show_block_arrows"] else 0)
    )

    parts = [svg_header(W, H, cfg)]
    parts.append(f"<title>{cfg['TITLE_TEXT']}</title>")

    # Title
    parts.append(
        f'<text class="blocklbl" x="{W / 2}" y="{cfg["TITLE_Y"]}" text-anchor="middle">{cfg["TITLE_TEXT"]}</text>'
    )

    # Block labels + faint rules
    # Left→right order: f, d, p, s
    for blk in BLOCK_DEFS:
        l_block = blk["l"]
        width = blk["width"] * cfg["CELL_W"]
        x0 = cfg["PAD_L"] + x_start[l_block] * cfg["CELL_W"]
        cx = x0 + width / 2
        y_lbl = cfg["PAD_T"] - cfg["BLOCK_HDR_DY"]
        y_rule = cfg["PAD_T"] - cfg["BLOCK_RULE_DY"]
        label = CONFIG["BLOCK_HEADER_TEXT"][l_block]
        parts.append(
            f'<text class="blocklbl" x="{cx}" y="{y_lbl}" text-anchor="middle">{label}</text>'
        )
        parts.append(
            f'<line class="guide" x1="{x0}" y1="{y_rule}" x2="{x0 + width}" y2="{y_rule}" />'
        )

    # Row labels (t = n + ℓ) and optional faint row guides
    for t in range(t_min, t_max + 1):
        row_y = cfg["PAD_T"] + (t - t_min) * cfg["CELL_H"]
        parts.append(
            f'<text class="rowlbl" x="{cfg["PAD_L"] - 12}" y="{row_y + cfg["CELL_H"] * 0.66}" text-anchor="end">{cfg["ROW_LABEL_PREFIX"]}{t}</text>'
        )
    # optional row guide lines
    parts.append('<g class="guide">')
    for t in range(t_min, t_max + 1):
        row_y = cfg["PAD_T"] + (t - t_min) * cfg["CELL_H"]
        parts.append(
            f'<line x1="{cfg["PAD_L"]}" y1="{row_y}" x2="{cfg["PAD_L"] + cols * cfg["CELL_W"]}" y2="{row_y}" />'
        )
    parts.append("</g>")

    # Cells + text
    for Z, info in placements.items():
        l_block = info["l"]
        col = info["col"]
        row = info["row"]
        x = cfg["PAD_L"] + col * cfg["CELL_W"]
        y = cfg["PAD_T"] + row * cfg["CELL_H"]

        # background fill (per block color)
        fill = cfg["BLOCK_FILLS"].get(l_block, "none")
        parts.append(
            f'<rect class="cell" x="{x}" y="{y}" width="{cfg["CELL_W"]}" height="{cfg["CELL_H"]}" '
            f'rx="{cfg["CELL_RX"]}" ry="{cfg["CELL_RY"]}" style="fill:{fill};stroke:{cfg["CELL_STROKE"]};stroke-width:{cfg["CELL_STROKE_W"]};" />'
        )

        # atomic number (top-left inside cell)
        parts.append(
            f'<text class="anum" x="{x + cfg["OFFSETS"]["anum_dx"]}" y="{y + cfg["OFFSETS"]["anum_dy"]}">{Z}</text>'
        )

        # symbol (centered horizontally; vertical placement via multiplier of CELL_H)
        sym_y = y + cfg["CELL_H"] * cfg["OFFSETS"]["sym_center_dy"]
        parts.append(
            f'<text class="sym" x="{x + cfg["CELL_W"] / 2}" y="{sym_y}" text-anchor="middle">{SYMBOLS[Z]}</text>'
        )

        # optional element name
        if cfg["show_name"]:
            name = ELEMENT_NAMES.get(Z, "")
            if name:
                name_y = y + cfg["CELL_H"] * cfg["OFFSETS"]["name_center_dy"]
                parts.append(
                    f'<text class="name" x="{x + cfg["CELL_W"] / 2}" y="{name_y}" text-anchor="middle">{name}</text>'
                )

    # Block arrows underneath (double-headed), with labels centered
    if cfg["show_block_arrows"]:
        baseline_y = cfg["PAD_T"] + rows * cfg["CELL_H"] + cfg["ARROW_Y_OFFSET"]
        for blk in BLOCK_DEFS:
            l_block = blk["l"]
            width = blk["width"] * cfg["CELL_W"]
            x0 = cfg["PAD_L"] + x_start[l_block] * cfg["CELL_W"]
            x1 = x0 + width
            cx = (x0 + x1) / 2
            # Draw arrow line with markers
            parts.append(
                f'<line class="arrowline" x1="{x0}" y1="{baseline_y}" x2="{x1}" y2="{baseline_y}" />'
            )
            # Label (s/p/d/f)
            label = {0: "s", 1: "p", 2: "d", 3: "f"}[l_block]
            parts.append(
                f'<text class="arrowlbl" x="{cx}" y="{baseline_y - 6}" text-anchor="middle">{label}</text>'
            )

    parts.append(svg_footer())
    return "\n".join(parts), (W, H)


def main():
    svg, size = build_svg()
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT_SVG.resolve()} size={size}")


if __name__ == "__main__":
    main()
