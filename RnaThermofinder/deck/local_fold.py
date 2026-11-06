"""Local replacement for the RNAfold webserver: fold with the ViennaRNA Python bindings and draw the
structure the way the webserver does, with no internet connection and no browser.

What the webserver runs by default is ``RNAfold -p -d2 --noLP`` with the Turner 2004 parameters at 37 C.
The same model is used here (``md.dangles = 2``, ``md.noLP = 1``, ViennaRNA's default parameter set), so the
MFE, the structure and the base-pair probabilities are the same numbers the webserver reports.

The drawing reproduces the webserver's "MFE secondary structure" picture:
  * naview layout (the RNAplot default the webserver uses; coordinates are identical),
  * backbone as a line, base pairs as thinner lines, one circle per nucleotide,
  * every nucleotide colored by its probability of being in the state the MFE structure shows
    (paired with its MFE partner, or unpaired), on the webserver's 40-step blue (0) -> red (1) scale.

Two files are written per fold: a vector SVG (letters as <text>, opens in Illustrator/Inkscape/browsers)
and a high-resolution PNG for the slide.
"""
from __future__ import annotations

from pathlib import Path

import RNA

DEFAULT_RADIUS = 8.0         # nucleotide circle radius in layout units (the webserver uses r = 8)
PNG_MAX_INCHES = 9.0         # longest side of the drawing, before the legend
PNG_DPI = 300


def vienna_version() -> str:
    return getattr(RNA, "__version__", "?")


def model_description() -> str:
    return f"ViennaRNA {vienna_version()} RNAfold -p -d2 --noLP (Turner 2004), local"


# ---------------------------------------------------------------- folding

def _model(temp: float):
    md = RNA.md()
    md.temperature = float(temp)
    md.dangles = 2
    md.noLP = 1
    md.noGU = 0
    return md


def fold(seq: str, temp) -> dict:
    """MFE structure and energy, plus the per-nucleotide probability the drawing is colored by.

    For a nucleotide paired with j in the MFE structure the value is P(i.j); for an unpaired nucleotide it is
    P(i unpaired) = 1 - sum_j P(i.j). This is what the webserver's 'Base-pair probabilities' coloring shows.
    """
    seq = seq.upper().replace("T", "U")
    fc = RNA.fold_compound(seq, _model(temp))
    structure, mfe = fc.mfe()
    fc.exp_params_rescale(mfe)       # avoids overflow in the partition function of longer sequences
    _, ensemble = fc.pf()
    bpp = fc.bpp()                   # 1-based upper-triangular matrix
    n = len(seq)
    paired_sum = [0.0] * (n + 1)
    for i in range(1, n + 1):
        row = bpp[i]
        for j in range(i + 1, n + 1):
            p = row[j]
            if p:
                paired_sum[i] += p
                paired_sum[j] += p
    pt = RNA.ptable(structure)
    prob = []
    for i in range(1, n + 1):
        j = pt[i]
        if j > 0:
            a, b = (i, j) if i < j else (j, i)
            prob.append(float(bpp[a][b]))
        else:
            prob.append(max(0.0, 1.0 - paired_sum[i]))
    return {"seq": seq, "structure": structure, "mfe": f"{mfe:.2f}", "mfe_value": float(mfe),
            "ensemble_energy": f"{ensemble:.2f}", "temp": f"{float(temp):g}", "prob": prob,
            "engine": model_description()}


# ---------------------------------------------------------------- colors and layout

# The webserver's 40-step base-pair-probability scale, low (blue) to high (red), copied from its SVG legend.
SCALE = ["#0050dc", "#0064dc", "#0078dc", "#008cdc", "#00a0dc", "#00b4dc", "#00c8dc", "#00dcdc", "#00dcc8",
         "#00dcb4", "#00dca0", "#00dc8c", "#00dc78", "#00dc64", "#00dc50", "#00dc3c", "#00dc28", "#00dc14",
         "#00dc00", "#14dc00", "#28dc00", "#3cdc00", "#50dc00", "#64dc00", "#78dc00", "#8cdc00", "#a0dc00",
         "#b4dc00", "#c8dc00", "#dcdc00", "#dcc800", "#dcb400", "#dca000", "#dc8c00", "#dc7800", "#dc6400",
         "#dc5000", "#dc3c00", "#dc2800", "#dc1400"]



def prob_color(p: float) -> str:
    return SCALE[min(39, max(0, int(round(p * 39))))]


def layout(structure: str):
    """naview coordinates (RNAplot's default, as on the webserver) in SVG orientation (y down).

    The webserver drawing is naview with the y axis negated; doing the same gives its exact picture
    (checked: identical coordinates up to a translation)."""
    n = len(structure)
    if "(" not in structure:
        co = RNA.simple_xy_coordinates(structure)   # naview needs at least one pair
    else:
        co = RNA.naview_xy_coordinates(structure)
    return [(float(co[i].X), -float(co[i].Y)) for i in range(n)]


def _pairs(structure):
    stack, out = [], []
    for i, c in enumerate(structure):
        if c == "(":
            stack.append(i)
        elif c == ")":
            out.append((stack.pop(), i))
    return out


def five_prime_label_pos(xy, r):
    """Just outside the first nucleotide, pointing away from the second one (so it never sits on a circle)."""
    (x0, y0) = xy[0]
    (x1, y1) = xy[1] if len(xy) > 1 else (x0, y0 + 1)
    dx, dy = x0 - x1, y0 - y1
    norm = (dx * dx + dy * dy) ** 0.5 or 1.0
    return x0 + dx / norm * (r + 7), y0 + dy / norm * (r + 7)


def _bounds(xy, pad):
    xs, ys = [p[0] for p in xy], [p[1] for p in xy]
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


# ---------------------------------------------------------------- drawing

def write_svg(result: dict, path, title: str = "") -> None:
    """Static SVG (no script): circles already colored, letters as text, a probability legend."""
    seq, structure, prob = result["seq"], result["structure"], result["prob"]
    xy = layout(structure)
    r = DEFAULT_RADIUS
    x0, y0, x1, y1 = _bounds(xy + [five_prime_label_pos(xy, r)], r + 4)
    w, h = max(x1 - x0, 130), y1 - y0
    legend_h = 46
    W, H = w, h + legend_h
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}" height="{H:.1f}" '
           f'viewBox="0 0 {W:.2f} {H:.2f}" font-family="Arial,Helvetica">',
           f'<title>{title or "MFE secondary structure"} | {result["engine"]} | {result["temp"]} C | '
           f'MFE {result["mfe"]} kcal/mol</title>',
           f'<rect x="0" y="0" width="{W:.2f}" height="{H:.2f}" fill="white"/>',
           f'<g transform="translate({-x0:.3f} {-y0:.3f})">']
    out.append('<polyline id="outline" style="stroke: black; fill: none; stroke-width: 1.5" points="'
               + " ".join(f"{x:.3f},{y:.3f}" for x, y in xy) + '"/>')
    out.append('<g id="pairs" style="stroke: black; stroke-width: 1">')
    for i, j in _pairs(structure):
        out.append(f'<line id="{i},{j}" x1="{xy[i][0]:.3f}" y1="{xy[i][1]:.3f}" x2="{xy[j][0]:.3f}" y2="{xy[j][1]:.3f}"/>')
    out.append("</g>")
    out.append('<g id="nucleotides">')
    for i, (x, y) in enumerate(xy):
        out.append(f'<circle id="c{i}" cx="{x:.3f}" cy="{y:.3f}" r="{r}" fill="{prob_color(prob[i])}" '
                   f'stroke="black" stroke-width="0.4"/>')
    out.append("</g>")
    out.append('<g id="letters" font-size="11px" font-weight="bold" text-anchor="middle" dominant-baseline="central">')
    for i, (x, y) in enumerate(xy):
        out.append(f'<text id="t{i}" x="{x:.3f}" y="{y:.3f}" fill="black">{seq[i]}</text>')
    out.append("</g>")
    fx, fy = five_prime_label_pos(xy, r)
    out.append(f'<text x="{fx:.3f}" y="{fy:.3f}" font-size="10px" font-weight="bold" fill="dimgray" '
               'text-anchor="middle" dominant-baseline="central">5\'</text>')
    out.append("</g>")
    # legend
    lx, ly, cw = 8, h + 14, 3
    out.append(f'<g id="legend" transform="translate({lx} {ly})">')
    out.append('<text x="0" y="-3" font-size="10px" fill="dimgray">base-pair probability</text>')
    for k, c in enumerate(SCALE):
        out.append(f'<rect x="{k * cw}" y="2" width="{cw}" height="10" fill="{c}"/>')
    out.append(f'<text x="0" y="25" font-size="10px" fill="dimgray">0</text>'
               f'<text x="{40 * cw}" y="25" font-size="10px" fill="dimgray" text-anchor="end">1</text>')
    out.append("</g></svg>")
    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")


def write_png(result: dict, path) -> None:
    """High-resolution PNG of the same drawing (matplotlib, Agg backend, no display needed)."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.collections import LineCollection
    from matplotlib.figure import Figure
    from matplotlib.patches import Circle, Rectangle

    seq, structure, prob = result["seq"], result["structure"], result["prob"]
    xy = layout(structure)
    r = DEFAULT_RADIUS
    x0, y0, x1, y1 = _bounds(xy + [five_prime_label_pos(xy, r)], r + 4)
    x1 = max(x1, x0 + 130)                        # room for the legend under narrow drawings
    w, h = x1 - x0, y1 - y0
    legend_units = 40.0                           # same scale as the nucleotides, like the webserver legend
    inch_per_unit = PNG_MAX_INCHES / max(w, h + legend_units)
    pt = inch_per_unit * 72                       # points per layout unit
    fig = Figure(figsize=(w * inch_per_unit, (h + legend_units) * inch_per_unit), dpi=PNG_DPI)
    FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1 + legend_units, y0)            # y down, like the SVG
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.plot([p[0] for p in xy], [p[1] for p in xy], color="black", lw=1.5 * pt, zorder=1,
            solid_capstyle="round")
    segs = [[xy[i], xy[j]] for i, j in _pairs(structure)]
    if segs:
        ax.add_collection(LineCollection(segs, colors="black", linewidths=1.0 * pt, zorder=1))
    for i, (x, y) in enumerate(xy):
        ax.add_patch(Circle((x, y), r, facecolor=prob_color(prob[i]), edgecolor="black",
                            linewidth=0.4 * pt, zorder=2))
        ax.text(x, y, seq[i], ha="center", va="center_baseline", fontsize=11 * pt,
                fontweight="bold", family="DejaVu Sans", zorder=3)
    fx, fy = five_prime_label_pos(xy, r)
    ax.text(fx, fy, "5'", ha="center", va="center", fontsize=10 * pt, fontweight="bold", color="dimgray", zorder=3)

    # legend: 40 color steps, 0 -> 1
    cw = 3.0
    lx, ly = x0 + 6, y1 + 14
    ax.text(lx, ly - 2, "base-pair probability", fontsize=9 * pt, color="dimgray", va="bottom")
    for k, c in enumerate(SCALE):
        ax.add_patch(Rectangle((lx + k * cw, ly), cw, 9, facecolor=c, edgecolor="none"))
    ax.text(lx, ly + 11, "0", fontsize=9 * pt, color="dimgray", va="top")
    ax.text(lx + 40 * cw, ly + 11, "1", fontsize=9 * pt, color="dimgray", va="top", ha="right")

    tmp = Path(path).with_name(Path(path).stem + ".partial.png")
    fig.savefig(tmp, dpi=PNG_DPI, facecolor="white")
    tmp.replace(path)


def drawn_letters(svg_text: str) -> str:
    import re
    return "".join(re.findall(r'<text id="t\d+"[^>]*>([ACGUT])</text>', svg_text))
