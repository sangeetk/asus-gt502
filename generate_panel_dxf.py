#!/usr/bin/env python3
"""
Generate laser-cut DXF for a custom ASUS ROG GT502 front panel (3 mm aluminium)
with cutouts for Waveshare touchscreens mounted from behind with 3M VHB tape.

Screen data taken from the Waveshare dimension drawings:

  11 inch   glass 253.67 x 165.22 | active 236.47 x 148.02 | bezel 8.60 all round
  6.25 inch glass 159.18 x  74.70 | active 144.18 x  66.60 | bezel 7.50 L/R, 4.05 T/B

"Inset" below = how far the cutout edge sits inside the glass edge. That strip of
glass is what the panel overlaps, i.e. the width available for the VHB tape.
Inset must never exceed the bezel width, or the cutout would clip active pixels.

Output is DXF R12, millimetres, closed POLYLINEs with bulge arcs -> every contour
is a single closed loop, which is what a laser CAM wants.
"""

import math

BULGE_90 = math.tan(math.radians(90) / 4)  # 0.4142135624, CCW quarter arc


def signed_area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1]
                     - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def ccw(pts):
    return pts if signed_area(pts) > 0 else pts[::-1]


# ------------------------------------------------------------ stencil lettering
# Squared monoline caps. Every glyph is ONE closed simple polygon, so each cuts
# as a single hole. Glyphs are drawn on a design grid DH tall with DS-wide
# strokes, then scaled uniformly to the wanted CAP_H.
#
# A, P and R have enclosed counters. In a cut-through panel a counter is an
# island with nothing holding it - it would drop out of the sheet and leave a
# blob instead of a letter. So each carries a BRIDGE: a gap in the crossbar (A)
# or the middle bar (P, R) that ties the counter back to the surrounding metal.
# The bridge is held at a fixed width in mm rather than being scaled with the
# type, so shrinking the text never thins the tab below what will survive
# handling. Those gaps are structural, not decorative - do not close them up.
DH = 22.0            # design cap height
DS = 4.0             # design stroke width

CAP_H = 14.0         # actual cap height, mm
BRIDGE = 2.5         # actual bridge width, mm - NOT scaled with CAP_H
TRACKING_D = 5.0     # letter gap, design units
SPACE_D = 6.0        # word space, design units

BRIDGED = ("A", "P", "R")

WIDTHS = {"A": 18.0, "C": 16.0, "E": 14.0, "H": 16.0, "I": 4.0, "N": 16.0,
          "P": 16.0, "R": 16.0, "T": 16.0, "U": 16.0, " ": SPACE_D}


def _glyph_A(g):
    w, h, s = WIDTHS["A"], DH, DS
    yb, yt = 7.0, 7.0 + s                      # crossbar band
    gl, gr = w / 2 - g / 2, w / 2 + g / 2      # bridge gap in the crossbar
    return [(0, 0), (s, 0), (s, yb), (gl, yb), (gl, yt), (s, yt), (s, h - s),
            (w - s, h - s), (w - s, yt), (gr, yt), (gr, yb), (w - s, yb),
            (w - s, 0), (w, 0), (w, h), (0, h)]


def _glyph_P(g):
    w, h, s = WIDTHS["P"], DH, DS
    bowl = 7.0
    yb, yt = h - 2 * s - bowl, h - s - bowl    # middle-bar band
    gl, gr = w / 2 - g / 2, w / 2 + g / 2
    return [(0, 0), (s, 0), (s, yb), (gl, yb), (gl, yt), (s, yt), (s, h - s),
            (w - s, h - s), (w - s, yt), (gr, yt), (gr, yb), (w, yb),
            (w, h), (0, h)]


def _glyph_R(g):
    """Bowl bridged through the middle bar, plus a splayed diagonal leg.

    The leg is what separates R from A here - without it both reduce to two
    verticals joined by a gapped mid bar and the two letters read alike.
    """
    w, h, s = WIDTHS["R"], DH, DS
    bowl = 7.0
    yb, yt = h - 2 * s - bowl, h - s - bowl    # middle-bar band
    gl, gr = w / 2 - g / 2, w / 2 + g / 2
    lx = w / 2                                 # where the leg leaves the mid bar
    return [(0, 0), (s, 0), (s, yb), (gl, yb), (gl, yt), (s, yt), (s, h - s),
            (w - s, h - s), (w - s, yt), (gr, yt), (gr, yb), (lx, yb),
            (w - s, 0), (w, 0), (w - s, yb), (w, yb), (w, h), (0, h)]


def _glyph_C(g=0):
    w, h, s = WIDTHS["C"], DH, DS
    return [(0, 0), (w, 0), (w, s), (s, s), (s, h - s), (w, h - s), (w, h), (0, h)]


def _glyph_U(g=0):
    w, h, s = WIDTHS["U"], DH, DS
    return [(0, 0), (w, 0), (w, h), (w - s, h), (w - s, s), (s, s), (s, h), (0, h)]


def _glyph_N(g=0):
    """Vertical stems plus a parallel-sided diagonal."""
    w, h, s = WIDTHS["N"], DH, DS
    v = 8.0                                    # vertical offset of the diagonal
    return [(0, 0), (0, h), (s, h), (w - s, v), (w - s, h), (w, h), (w, 0),
            (w - s, 0), (s, h - v), (s, 0)]


def _glyph_T(g=0):
    w, h, s = WIDTHS["T"], DH, DS
    xl, xr = (w - s) / 2, (w + s) / 2
    return [(xl, 0), (xr, 0), (xr, h - s), (w, h - s), (w, h), (0, h),
            (0, h - s), (xl, h - s)]


def _glyph_E(g=0):
    w, h, s = WIDTHS["E"], DH, DS
    yb, yt = h / 2 - s / 2, h / 2 + s / 2      # middle bar
    return [(0, 0), (w, 0), (w, s), (s, s), (s, yb), (w, yb), (w, yt), (s, yt),
            (s, h - s), (w, h - s), (w, h), (0, h)]


def _glyph_H(g=0):
    w, h, s = WIDTHS["H"], DH, DS
    yb, yt = h / 2 - s / 2, h / 2 + s / 2
    return [(0, 0), (s, 0), (s, yb), (w - s, yb), (w - s, 0), (w, 0), (w, h),
            (w - s, h), (w - s, yt), (s, yt), (s, h), (0, h)]


def _glyph_I(g=0):
    return [(0, 0), (WIDTHS["I"], 0), (WIDTHS["I"], DH), (0, DH)]


GLYPHS = {"A": _glyph_A, "C": _glyph_C, "E": _glyph_E, "H": _glyph_H,
          "I": _glyph_I, "N": _glyph_N, "P": _glyph_P, "R": _glyph_R,
          "T": _glyph_T, "U": _glyph_U}


def text_polys(word, cx, baseline, cap_h=None):
    """Glyph polygons for `word`, scaled to cap_h, centred on cx, on baseline.

    Returns (polygons, overall width in mm).
    """
    cap_h = CAP_H if cap_h is None else cap_h
    sc = cap_h / DH
    g = BRIDGE / sc                  # bridge kept at a fixed width in mm
    missing = [c for c in word if c != " " and c not in GLYPHS]
    assert not missing, f"no glyph for {missing}"

    adv = [WIDTHS[c] for c in word]
    total_d = sum(adv) + TRACKING_D * (len(word) - 1)
    x0 = cx - total_d * sc / 2

    polys, xd = [], 0.0
    for ch, w in zip(word, adv):
        if ch != " ":
            polys.append([(x0 + (xd + px) * sc, baseline + py * sc)
                          for px, py in GLYPHS[ch](g)])
        xd += w + TRACKING_D
    return polys, total_d * sc

# ------------------------------------------------------------ back border layer
# A second 3 mm layer bonded to the BACK of the panel purely as a stiffener.
# Four strips around the edge. The screens bond to the panel's own cutouts, so
# every strip must stay clear of the screen GLASS footprint by BORDER_CLEAR -
# a strip under the glass would sit the screen on a 3 mm step and tilt it.
#
# Requested widths. Each is capped at what the back face actually leaves free,
# so a later nudge of the windows narrows a strip (and says so) instead of
# quietly fouling a screen.
BORDER_REQ = {"left": 12.0, "right": 12.0, "top": 20.0, "bottom": 22.0}
BORDER_CLEAR = 1.0       # minimum air between a strip and the screen glass
BORDER_NEST_GAP = 10.0   # spacing between pieces in the cutting layout

# ---------------------------------------------------------------- screen specs
SCREEN_11 = dict(name="11in", glass=(165.22, 253.67), active=(148.02, 236.47),
                 bezel=(8.60, 8.60))   # (horizontal, vertical) as mounted PORTRAIT
SCREEN_625 = dict(name="6.25in", glass=(159.18, 74.70), active=(144.18, 66.60),
                  bezel=(7.50, 4.05))  # as mounted LANDSCAPE


# ------------------------------------------------------------------ DXF writer
class Dxf:
    def __init__(self):
        self.ents = []
        self.layers = {}

    def layer(self, name, color):
        self.layers[name] = color

    def rounded_rect(self, layer, x0, y0, w, h, r):
        """Closed CCW polyline, lower-left corner at (x0, y0)."""
        b = BULGE_90
        verts = [
            (x0 + r,     y0,         0),
            (x0 + w - r, y0,         b),
            (x0 + w,     y0 + r,     0),
            (x0 + w,     y0 + h - r, b),
            (x0 + w - r, y0 + h,     0),
            (x0 + r,     y0 + h,     b),
            (x0,         y0 + h - r, 0),
            (x0,         y0 + r,     b),
        ]
        out = ["0", "POLYLINE", "8", layer, "66", "1", "70", "1",
               "10", "0.0", "20", "0.0", "30", "0.0"]
        for x, y, bg in verts:
            out += ["0", "VERTEX", "8", layer,
                    "10", f"{x:.4f}", "20", f"{y:.4f}", "30", "0.0",
                    "42", f"{bg:.10f}"]
        out += ["0", "SEQEND", "8", layer]
        self.ents += out

    def polygon(self, layer, pts):
        """Closed polyline through pts, straight segments, forced CCW."""
        pts = ccw(pts)
        out = ["0", "POLYLINE", "8", layer, "66", "1", "70", "1",
               "10", "0.0", "20", "0.0", "30", "0.0"]
        for x, y in pts:
            out += ["0", "VERTEX", "8", layer,
                    "10", f"{x:.4f}", "20", f"{y:.4f}", "30", "0.0"]
        out += ["0", "SEQEND", "8", layer]
        self.ents += out

    def circle(self, layer, cx, cy, dia):
        self.ents += ["0", "CIRCLE", "8", layer,
                      "10", f"{cx:.4f}", "20", f"{cy:.4f}", "30", "0.0",
                      "40", f"{dia / 2:.4f}"]

    def dumps(self, extmax):
        h = ["0", "SECTION", "2", "HEADER",
             "9", "$ACADVER", "1", "AC1009",
             "9", "$INSUNITS", "70", "4",        # 4 = millimetres
             "9", "$MEASUREMENT", "70", "1",     # 1 = metric
             "9", "$LUNITS", "70", "2",
             "9", "$EXTMIN", "10", "0.0", "20", "0.0", "30", "0.0",
             "9", "$EXTMAX", "10", f"{extmax[0]:.4f}", "20", f"{extmax[1]:.4f}",
             "30", "0.0",
             "0", "ENDSEC"]

        t = ["0", "SECTION", "2", "TABLES",
             "0", "TABLE", "2", "LTYPE", "70", "1",
             "0", "LTYPE", "2", "CONTINUOUS", "70", "0",
             "3", "Solid line", "72", "65", "73", "0", "40", "0.0",
             "0", "ENDTAB",
             "0", "TABLE", "2", "LAYER", "70", str(len(self.layers))]
        for name, color in self.layers.items():
            t += ["0", "LAYER", "2", name, "70", "0", "62", str(color),
                  "6", "CONTINUOUS"]
        t += ["0", "ENDTAB", "0", "ENDSEC"]

        e = ["0", "SECTION", "2", "ENTITIES"] + self.ents + ["0", "ENDSEC"]
        return "\r\n".join(h + t + e + ["0", "EOF"]) + "\r\n"


# ------------------------------------------------------------------ SVG preview
def svg(path, pw, ph, cutouts, refs, title, letters=(), holes=(),
        parts=(), ghosts=(), canvas=None):
    pad = 20
    cw, chh = canvas or (pw, ph)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{cw+2*pad}" '
         f'height="{chh+2*pad}" viewBox="0 0 {cw+2*pad} {chh+2*pad}">',
         f'<rect width="100%" height="100%" fill="#f4f4f5"/>',
         f'<g transform="translate({pad},{pad}) scale(1,-1) translate(0,{-chh})">',
         f'<rect x="0" y="0" width="{pw}" height="{ph}" rx="3" '
         f'fill="#c8ccd0" stroke="#3f3f46" stroke-width="0.8"/>']
    for x, y, w, h, r in cutouts:
        s.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
                 f'rx="{r}" fill="#f4f4f5" stroke="#dc2626" stroke-width="0.8"/>')
    for poly in letters:
        pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in poly)
        s.append(f'<polygon points="{pts}" fill="#f4f4f5" stroke="#dc2626" '
                 f'stroke-width="0.8"/>')
    for hx, hy, hd in holes:
        s.append(f'<circle cx="{hx:.3f}" cy="{hy:.3f}" r="{hd/2:.3f}" '
                 f'fill="#f4f4f5" stroke="#dc2626" stroke-width="0.8"/>')
    for x, y, w, h in ghosts:      # where the strips end up, behind the panel
        s.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
                 f'fill="#9aa0a6" fill-opacity="0.35" stroke="#5f6368" '
                 f'stroke-width="0.5" stroke-dasharray="4 2"/>')
    for x, y, w, h, phs in parts:  # the same strips, nested for cutting
        s.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
                 f'fill="#c8ccd0" stroke="#3f3f46" stroke-width="0.8"/>')
        for hx, hy in phs:
            s.append(f'<circle cx="{x+hx:.3f}" cy="{y+hy:.3f}" r="{HOLE_DIA/2:.3f}" '
                     f'fill="#f4f4f5" stroke="#dc2626" stroke-width="0.8"/>')
    for x, y, w, h, colour, dash in refs:
        s.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
                 f'fill="none" stroke="{colour}" stroke-width="0.6" '
                 f'stroke-dasharray="{dash}"/>')
    s += ['</g>',
          f'<text x="{pad}" y="{chh+2*pad-6}" font-family="sans-serif" '
          f'font-size="9" fill="#3f3f46">{title}</text>',
          '</svg>']
    with open(path, "w") as f:
        f.write("\n".join(s))


def svg_1to1(path, pw, ph, cutouts, refs, notes, letters=(), holes=()):
    """True-scale SVG: 1 user unit = 1 mm, page is exactly pw x ph mm.

    Print at 100% / "actual size" (no fit-to-page) and the scale bar must
    measure 100 mm. Then lay the real screens on it to check the fit.
    Anything falling outside the panel is clipped by the page, which is the
    point: if a cutout runs off the edge, the print shows it.
    """
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{pw}mm" height="{ph}mm" '
         f'viewBox="0 0 {pw} {ph}">',
         '<rect width="100%" height="100%" fill="#ffffff"/>',
         f'<g transform="scale(1,-1) translate(0,{-ph})">',
         f'<rect x="0.15" y="0.15" width="{pw-0.3}" height="{ph-0.3}" '
         f'rx="{PANEL_CORNER_R}" fill="none" stroke="#000000" stroke-width="0.3"/>']
    for x, y, w, h, r in cutouts:
        s.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
                 f'rx="{r}" fill="none" stroke="#dc2626" stroke-width="0.5"/>')
    for poly in letters:
        pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in poly)
        s.append(f'<polygon points="{pts}" fill="none" stroke="#dc2626" '
                 f'stroke-width="0.5"/>')
    for hx, hy, hd in holes:
        s.append(f'<circle cx="{hx:.3f}" cy="{hy:.3f}" r="{hd/2:.3f}" '
                 f'fill="none" stroke="#dc2626" stroke-width="0.5"/>')
    for x, y, w, h, colour, dash in refs:
        s.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
                 f'fill="none" stroke="{colour}" stroke-width="0.3" '
                 f'stroke-dasharray="{dash}"/>')
    # 100 mm scale bar, bottom-left inside the panel
    bx, by = 8.0, 6.0
    s += [f'<line x1="{bx}" y1="{by}" x2="{bx+100}" y2="{by}" '
          f'stroke="#000" stroke-width="0.4"/>',
          f'<line x1="{bx}" y1="{by-1.5}" x2="{bx}" y2="{by+1.5}" '
          f'stroke="#000" stroke-width="0.4"/>',
          f'<line x1="{bx+100}" y1="{by-1.5}" x2="{bx+100}" y2="{by+1.5}" '
          f'stroke="#000" stroke-width="0.4"/>',
          '</g>']
    s.append(f'<text x="{bx}" y="{ph-by+3.2}" font-family="sans-serif" '
             f'font-size="3">100 mm - measure this after printing</text>')
    for i, line in enumerate(notes):
        s.append(f'<text x="8" y="{12 + i*4}" font-family="sans-serif" '
                 f'font-size="3" fill="#3f3f46">{line}</text>')
    s.append('</svg>')
    with open(path, "w") as f:
        f.write("\n".join(s))


# --------------------------------------------------------------------- builders
def cutout_from(screen, insets):
    """insets = (left, right, bottom, top) -> (w, h) of the cutout."""
    l, rr, b, t = insets
    gw, gh = screen["glass"]
    bh, bv = screen["bezel"]
    for v, lim, side in ((l, bh, "left"), (rr, bh, "right"),
                         (b, bv, "bottom"), (t, bv, "top")):
        assert v <= lim + 1e-9, f"{screen['name']} {side} inset {v} > bezel {lim}"
    return gw - l - rr, gh - b - t


PANEL_W = 194.0
PANEL_CORNER_R = 3.0
CUT_R = 2.0

PANEL_H = 384.0     # measured outer height of the GT502 front panel
CUT_GAP = 12.0      # vertical gap between the two cutouts

# Mounting holes: 4 off, one pair inset from the top edge and a mirrored pair
# inset from the bottom edge, same inset from the sides.
# NOTE: diameter is an assumption - M3 clearance. Change HOLE_DIA if the
# fastener is anything else; positions are as specified and are not guesses.
HOLE_DIA = 3.2

# One entry per hole, all measured to the hole CENTRE, each as the distance
# from a NAMED edge so the numbers read the same way they were specified:
#   (("left"|"right", dist), ("top"|"bottom", dist))
# These are measured off the cut sheet and are deliberately not a symmetric
# pattern - keep them as independent values, do not "tidy" them into a formula.
MOUNT_HOLES = [
    (("left",  63.0), ("top",    13.0)),   # top left
    (("right", 60.0), ("top",    13.0)),   # top right
    (("left",  30.0), ("bottom", 16.0)),   # bottom left
    (("right", 30.0), ("bottom", 16.0)),   # bottom right
]
HOLE_NAMES = ("top left", "top right", "bottom left", "bottom right")


def hole_xy(spec, ph):
    (xe, xd), (ye, yd) = spec
    return (xd if xe == "left" else PANEL_W - xd,
            yd if ye == "bottom" else ph - yd)
# Fit corrections measured off the first laser-cut sheet. The 4 mounting holes
# locate the panel to the case, so they are the datum and do NOT move - only the
# two windows shift. Positive DX is right, positive DY is up.
WIN_DX = 3.0        # both windows: 3 right
WIN_11_DY = -3.0    # lower / 11in window: 3 down
WIN_625_DY = 3.0    # upper / 6.25in window: 3 up

WORD = None         # set to a string to also emit a variant with text cut
                    # into the top band, e.g. "URANTIA TECH". Glyphs and the
                    # stencil bridging above stay ready for when it is wanted.
GLASS_BOTTOM = 18.0     # metal left below the 11in glass once screens are pushed down

# How far each cutout edge sits inside the screen's glass edge, i.e. the width
# of bezel the aluminium overlaps = the width available for the VHB tape.
# Must stay <= the bezel on that edge, or the cutout would clip active pixels.
INS_11 = (6.0, 6.0, 6.0, 6.0)     # left, right, bottom, top  (bezel 8.60 all round)
INS_625 = (6.0, 6.0, 3.0, 3.0)    # left, right, bottom, top  (bezel 7.50 / 4.05)


def build_both(out_dxf, out_svg, out_print, panel_h=None, cut_gap=5.0,
               glass_bottom=None, word=None):
    """Both screens, 6.25in landscape on top, 11in portrait below.

    panel_h      measured outer height of the panel. None -> smallest height
                 that still leaves 8 mm of aluminium past the glass top/bottom.
    glass_bottom mm of aluminium below the 11in glass. None -> centre the pair.
                 Set it to push the screens down and open a band at the top.
    word         text to cut into that top band, or None for no text.
    """
    ins11, ins625 = INS_11, INS_625
    cw11, ch11 = cutout_from(SCREEN_11, ins11)
    cw62, ch62 = cutout_from(SCREEN_625, ins625)

    nominal_stack = ch11 + cut_gap + ch62
    glass_span = nominal_stack + ins625[3] + ins11[2]
    ph_min = glass_span + 16.0                      # >= 8 mm of panel past glass
    ph = math.ceil(ph_min) if panel_h is None else float(panel_h)

    # Nominal layout: pair centred (or sat on glass_bottom), windows centred
    # on the width.
    margin = ((ph - nominal_stack) / 2 if glass_bottom is None
              else glass_bottom + ins11[2])
    y11 = margin + WIN_11_DY
    y62 = margin + ch11 + cut_gap + WIN_625_DY
    x11 = (PANEL_W - cw11) / 2 + WIN_DX
    x62 = (PANEL_W - cw62) / 2 + WIN_DX

    # Everything below is measured off the SHIFTED positions, so the reported
    # gap and clearances describe the part that actually gets cut.
    act_gap = y62 - (y11 + ch11)                    # metal between the windows
    glass_gap = act_gap - ins11[3] - ins625[2]      # air between the two glasses
    assert glass_gap > 0, "screens would physically collide behind the panel"

    glass_bot_11 = y11 - ins11[2]
    glass_top = y62 + ch62 + ins625[3]
    band = ph - glass_top
    overflow = max(0.0, -glass_bot_11, glass_top - ph)

    # Windows must stay inside the sheet, and so must the glass behind them.
    assert glass_bot_11 > 0, "11in glass hangs off the bottom of the sheet"
    assert glass_top < ph, "6.25in glass hangs off the top of the sheet"
    for gx, cw, ins in ((x11, cw11, ins11), (x62, cw62, ins625)):
        assert gx - ins[0] > 0 and gx + cw + ins[1] < PANEL_W, \
            "glass hangs off the side of the sheet"

    cut_gap = act_gap

    d = Dxf()
    d.layer("PANEL_OUTLINE", 7)
    d.layer("CUTOUT", 1)
    d.rounded_rect("PANEL_OUTLINE", 0, 0, PANEL_W, ph, PANEL_CORNER_R)
    d.rounded_rect("CUTOUT", x11, y11, cw11, ch11, CUT_R)
    d.rounded_rect("CUTOUT", x62, y62, cw62, ch62, CUT_R)

    hr = HOLE_DIA / 2
    holes = [hole_xy(spec, ph) for spec in MOUNT_HOLES]
    for hx, hyc in holes:
        d.circle("CUTOUT", hx, hyc, HOLE_DIA)
    # Every hole must clear both windows and stay inside the sheet edges.
    for hx, hyc in holes:
        where = f"hole at ({hx:.2f}, {hyc:.2f})"
        assert hr < hx < PANEL_W - hr, f"{where} breaks a side edge"
        assert hr < hyc < ph - hr, f"{where} breaks the top/bottom edge"
        for wx, wy, ww, wh, name in ((x11, y11, cw11, ch11, "lower window"),
                                     (x62, y62, cw62, ch62, "upper window")):
            clear = (hx + hr <= wx or hx - hr >= wx + ww
                     or hyc + hr <= wy or hyc - hr >= wy + wh)
            assert clear, f"{where} runs into the {name}"

    letters, text_w, baseline = [], 0.0, None
    if word:
        # Centre the lettering vertically in the free band.
        baseline = glass_top + (band - CAP_H) / 2
        assert baseline > glass_top, f"no room for text: band is only {band:.2f} mm"
        assert baseline + CAP_H < ph, "text runs off the top of the panel"
        letters, text_w = text_polys(word, PANEL_W / 2, baseline)
        for poly in letters:
            d.polygon("CUTOUT", poly)

    bd = plan_border(PANEL_W, ph,
                     (x11 - ins11[0], y11 - ins11[2]) + SCREEN_11["glass"],
                     (x62 - ins625[0], y62 - ins625[2]) + SCREEN_625["glass"],
                     holes)
    d.layer("BORDER_STRIP", 3)
    for name, nx, ny, nw, nh in bd["nested"]:
        d.rounded_rect("BORDER_STRIP", nx, ny, nw, nh, 0.001)
        for hxo, hyo in bd["strip_holes"][name]:
            d.circle("CUTOUT", nx + hxo, ny + hyo, HOLE_DIA)

    with open(out_dxf, "w") as f:
        f.write(d.dumps(bd["sheet"]))

    g11w, g11h = SCREEN_11["glass"]
    a11w, a11h = SCREEN_11["active"]
    g62w, g62h = SCREEN_625["glass"]
    a62w, a62h = SCREEN_625["active"]
    refs = [
        (x11 - ins11[0], y11 - ins11[2], g11w, g11h, "#2563eb", "3 2"),
        (x62 - ins625[0], y62 - ins625[2], g62w, g62h, "#2563eb", "3 2"),
        ((PANEL_W - a11w) / 2, y11 - ins11[2] + SCREEN_11["bezel"][1],
         a11w, a11h, "#16a34a", "1 1"),
        ((PANEL_W - a62w) / 2, y62 - ins625[2] + SCREEN_625["bezel"][1],
         a62w, a62h, "#16a34a", "1 1"),
    ]
    cutouts = [(x11, y11, cw11, ch11, CUT_R), (x62, y62, cw62, ch62, CUT_R)]
    svg_holes = [(hx, hyc, HOLE_DIA) for hx, hyc in holes]
    svg(out_svg, PANEL_W, ph, cutouts, refs,
        f"{PANEL_W:.0f} x {ph:.0f} - 6.25in landscape top, 11in portrait below. "
        f"cutouts {cw62:.2f}x{ch62:.2f} and {cw11:.2f}x{ch11:.2f}, "
        f"gap {cut_gap:.1f} (glass gap {glass_gap:.1f})"
        + (f", text \"{word}\" {CAP_H:.0f} mm caps" if word else "")
        + f". Plus {len(bd['nested'])} back stiffener strips nested at right/top "
          "(grey dashed = where they bond behind the panel).",
        letters=letters, holes=svg_holes,
        parts=[(nx, ny, nw, nh, bd["strip_holes"][n])
               for n, nx, ny, nw, nh in bd["nested"]],
        ghosts=[(sx, sy, sw, sh) for _, sx, sy, sw, sh in bd["placed"]],
        canvas=bd["sheet"])

    svg_1to1(out_print, PANEL_W, ph, cutouts, refs, [
        f"GT502 front panel, 3 mm aluminium - {PANEL_W:.0f} x {ph:.0f} mm",
        "PRINT AT 100% / ACTUAL SIZE. Do not fit to page.",
        f"6.25in cutout {cw62:.2f} x {ch62:.2f}   11in cutout {cw11:.2f} x {ch11:.2f}",
        f"cutout gap {cut_gap:.1f} mm     glass-to-glass gap {glass_gap:.1f} mm",
        "red = cut line   blue dashed = screen glass outline   green = active area",
    ] + ([f'text "{word}": {CAP_H:.1f} mm caps, {DS*CAP_H/DH:.2f} mm stroke, '
          f'{text_w:.2f} mm wide, baseline Y {baseline:.2f}'] if word else []),
        letters=letters, holes=svg_holes)
    return dict(panel=(PANEL_W, ph), c11=(cw11, ch11), c62=(cw62, ch62),
                gap=cut_gap, glass_gap=glass_gap, margin=margin,
                overflow=overflow, glass_span=glass_span,
                y11=y11, y62=y62, x11=x11, x62=x62,
                band=band, glass_top=glass_top, word=word, holes=holes,
                border=bd,
                g11rect=(x11 - ins11[0], y11 - ins11[2], g11w, g11h),
                g62rect=(x62 - ins625[0], y62 - ins625[2], g62w, g62h),
                text_w=text_w, baseline=baseline, n_letters=len(letters),
                bridged=", ".join(c for c in BRIDGED if word and c in word))



def plan_border(pw, ph, g11rect, g62rect, holes):
    """Work out the four back stiffener strips. Pure geometry - writes nothing.

    The strips are nested into the MAIN dxf so the whole build comes off one
    sheet as one cutting job. Returns both their assembled positions (for the
    clearance check) and their nested positions (what actually gets cut).
    """
    gx1, gy1, gw1, gh1 = g11rect               # 11in glass footprint
    gx2, gy2, gw2, gh2 = g62rect               # 6.25in glass footprint

    # Free back-face margin on each edge = distance from the sheet edge to the
    # nearest glass, taking whichever screen comes closer.
    avail = {
        "left":   min(gx1, gx2),
        "right":  min(pw - (gx1 + gw1), pw - (gx2 + gw2)),
        "bottom": gy1,
        "top":    ph - (gy2 + gh2),
    }
    width, capped = {}, {}
    for edge, req in BORDER_REQ.items():
        room = avail[edge] - BORDER_CLEAR
        width[edge] = min(req, math.floor(room))
        if width[edge] < req:
            capped[edge] = (req, width[edge], avail[edge])

    # Verticals run the full height between the panel's corner radii, so their
    # square ends stop exactly on the arc tangents and nothing juts past the
    # rounded corner. Horizontals butt between them.
    vy, vh = PANEL_CORNER_R, ph - 2 * PANEL_CORNER_R
    hx = width["left"]
    hw = pw - width["left"] - width["right"]

    placed = [
        ("left strip",   0.0,                  vy,               width["left"],  vh),
        ("right strip",  pw - width["right"],   vy,               width["right"], vh),
        ("top strip",    hx,   ph - width["top"],                 hw, width["top"]),
        ("bottom strip", hx,   0.0,                               hw, width["bottom"]),
    ]

    # Which holes land in which strip, as offsets inside that strip.
    strip_holes = {}
    for name, sx, sy, sw, sh in placed:
        hits = [(x - sx, y - sy) for x, y in holes
                if sx <= x <= sx + sw and sy <= y <= sy + sh]
        strip_holes[name] = hits

    # No strip may touch either glass footprint.
    for name, sx, sy, sw, sh in placed:
        for gx, gy, gw, gh in (g11rect, g62rect):
            clear = (sx + sw <= gx or sx >= gx + gw
                     or sy + sh <= gy or sy >= gy + gh)
            assert clear, f"{name} overlaps a screen glass footprint"
    # Every hole must end up in exactly one strip, or a screw has nothing to pass through.
    assert sum(len(v) for v in strip_holes.values()) == len(holes), \
        "a mounting hole falls outside every strip"

    # ---- nest the pieces onto the same sheet as the panel ----
    # Verticals go in a column to the right of the panel, horizontals above it.
    # Nothing may overlap the panel or another piece.
    nested = []
    cx = pw + BORDER_NEST_GAP
    for name, _, _, sw, sh in placed[:2]:                 # the two verticals
        nested.append((name, cx, 0.0, sw, sh))
        cx += sw + BORDER_NEST_GAP
    cy = ph + BORDER_NEST_GAP
    for name, _, _, sw, sh in placed[2:]:                 # the two horizontals
        nested.append((name, 0.0, cy, sw, sh))
        cy += sh + BORDER_NEST_GAP

    sheet = (max([cx - BORDER_NEST_GAP] + [x + w for _, x, _, w, _ in nested]),
             max([cy - BORDER_NEST_GAP] + [y + h for _, _, y, _, h in nested]))

    boxes = [("panel", 0.0, 0.0, pw, ph)] + [(n, x, y, w, h) for n, x, y, w, h in nested]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            _, ax, ay, aw, ah = boxes[i]
            _, bx, by, bw, bh = boxes[j]
            apart = (ax + aw <= bx or bx + bw <= ax
                     or ay + ah <= by or by + bh <= ay)
            assert apart, f"nested {boxes[i][0]} overlaps {boxes[j][0]}"

    return dict(width=width, capped=capped, avail=avail, placed=placed,
                strip_holes=strip_holes, nested=nested, sheet=sheet)

SPEC = """CUSTOM FRONT PANEL - CUTTING SPECIFICATION
ASUS ROG GT502, aluminium front panel with two touchscreen cutouts
==================================================================

DXF FILE   : {dxf}
MATERIAL   : Aluminium sheet, 3.0 mm thickness
QUANTITY   : 1 off of everything on the sheet - the panel plus the 4 back
             stiffener strips nested beside it. ONE cutting job.
PROCESS    : Laser cut (fibre) or waterjet
UNITS      : Millimetres. DXF is AC1009 / R12 ASCII, $INSUNITS = 4 (mm).
GEOMETRY   : Panel outer profile + internal cutouts, plus 4 separate
             rectangular strips nested to the right of and above the panel.
             The strips are separate parts, NOT features of the panel.
TOLERANCE  : +/- 0.15 mm on all cutout sizes and positions.
KERF       : Geometry is NOMINAL. Please apply your own kerf compensation so
             the finished part matches the drawing: outer profile cut on the
             outside of the line, windows cut on the inside of the line.
FINISH     : Deburr both faces. The window edges must be flat and burr-free -
             a touchscreen is bonded to the BACK face around each opening
             with 3M VHB tape, so the back face must be clean and flat.
             No anodising / powder coat unless quoted separately.

DIMENSIONS (origin = lower-left corner of the sheet, X right, Y up)
------------------------------------------------------------------
Sheet outline        {pw:.2f} W x {ph:.2f} H, corner radius {pr:.1f}

Window 1 - upper, small (6.25 inch screen, landscape)
   size              {c62w:.2f} W x {c62h:.2f} H, corner radius {cr:.1f}
   lower-left at     X {x62:.2f} , Y {y62:.2f}

Window 2 - lower, large (11 inch screen, portrait)
   size              {c11w:.2f} W x {c11h:.2f} H, corner radius {cr:.1f}
   lower-left at     X {x11:.2f} , Y {y11:.2f}

Vertical gap between the two windows   {gap:.2f}
Both windows sit {wdx:.2f} to the RIGHT of the sheet centreline, so the
left and right margins are NOT equal. Please work to the X/Y
coordinates above rather than centring anything.

Mounting holes - {hn} off, diameter {hdia:.2f} THROUGH
{holelist}
   All hole positions are to the CENTRE. They are NOT a symmetric pattern -
   please work to the coordinates as given.
Aluminium remaining below lower window {y11:.2f}
Aluminium remaining above upper window {above:.2f}

NOTES
------------------------------------------------------------------
- The {hn} mounting holes above are the only fixings in this drawing. No
  clip or latch features are included. Please cut only what is in the DXF.
- Do not scale the drawing. All dimensions are final.

BACK STIFFENER STRIPS - 4 pieces, same 3 mm aluminium
------------------------------------------------------------------
Nested to the right of and above the panel on the same sheet. They are
separate parts that bond flat to the BACK of the panel; they are not
visible in the finished build. Total sheet extent {sheetw:.2f} x {sheeth:.2f}.

{striplist}

Strip hole positions are offsets from that strip's own lower-left corner
and match the panel holes, so one screw passes through both layers.
Deburr both faces - these bond flat against the panel.
"""


TEXT_NOTE = """
LETTERING
------------------------------------------------------------------
The word "{word}" is cut right through the sheet as {n} separate closed
contours, {caps:.0f} mm cap height, {stroke:.2f} mm stroke, {tw:.2f} mm overall width,
centred on the sheet width, baseline at Y {baseline:.2f}.

IMPORTANT - {bridged} are STENCIL letters. Each has a {bridge:.1f} mm gap in one
bar that ties the middle of the letter back to the surrounding sheet. Please cut them exactly as drawn. Do not "correct" the gaps or
substitute a normal font: without those gaps the centres of those
letters are loose islands and will fall out of the panel.
"""


def write_spec(path, dxf_name, b, extra_windows=0, word=None):
    pw, ph = b["panel"]
    text = SPEC.format(
        dxf=dxf_name, pw=pw, ph=ph, pr=PANEL_CORNER_R, cr=CUT_R,
        contours=5 + extra_windows,
        c62w=b["c62"][0], c62h=b["c62"][1], x62=b["x62"], y62=b["y62"],
        c11w=b["c11"][0], c11h=b["c11"][1], x11=b["x11"], y11=b["y11"],
        gap=b["gap"], above=ph - b["y62"] - b["c62"][1],
        hdia=HOLE_DIA, hn=len(b["holes"]), wdx=WIN_DX,
        sheetw=b["border"]["sheet"][0], sheeth=b["border"]["sheet"][1],
        striplist="\n".join(
            f"   {name:<14s} {nw:>7.2f} W x {nh:>7.2f} H"
            f"   nested at X {nx:.2f}, Y {ny:.2f}"
            + ("".join(f"\n                  hole at X {hx:.2f}, Y {hy:.2f}"
                       for hx, hy in b["border"]["strip_holes"][name])
               or "\n                  no holes")
            for name, nx, ny, nw, nh in b["border"]["nested"]),
        holelist="\n".join(
            f"   {name:<13s} X {hx:>7.2f} , Y {hy:>7.2f}"
            f"   ({xd:.2f} from {xe}, {yd:.2f} from {ye})"
            for name, (hx, hy), ((xe, xd), (ye, yd))
            in zip(HOLE_NAMES, b["holes"], MOUNT_HOLES)))
    if word:
        text += TEXT_NOTE.format(word=word, n=b["n_letters"], caps=CAP_H,
                                 stroke=DS * CAP_H / DH, tw=b["text_w"],
                                 baseline=b["baseline"], bridge=BRIDGE,
                                 bridged=b["bridged"])
    with open(path, "w") as f:
        f.write(text)


def report(tag, b):
    ph = b["panel"][1]
    print(f"\n=== {tag} ===")
    print(f"panel            {b['panel'][0]:.2f} W x {ph:.2f} H")
    print(f"6.25in cutout    {b['c62'][0]:.2f} x {b['c62'][1]:.2f}"
          f"   at ({b['x62']:.2f}, {b['y62']:.2f})")
    print(f"11in   cutout    {b['c11'][0]:.2f} x {b['c11'][1]:.2f}"
          f"   at ({b['x11']:.2f}, {b['y11']:.2f})")
    print(f"cutout gap       {b['gap']:.2f}   glass-to-glass {b['glass_gap']:.2f}")
    print(f"glass span       {b['glass_span']:.2f} of {ph:.2f} available")
    print(f"metal below 11in glass  {b['y11'] - INS_11[2]:.2f}")
    print(f"free band above glass   {b['band']:.2f}")
    if b["word"]:
        print(f'text "{b["word"]}"      {b["n_letters"]} glyphs, '
              f'{b["text_w"]:.2f} mm wide, baseline Y {b["baseline"]:.2f}, '
              f'top Y {b["baseline"] + CAP_H:.2f}')
        print(f"   metal above text     {ph - b['baseline'] - CAP_H:.2f}")
        print(f"   metal text to glass  {b['baseline'] - b['glass_top']:.2f}")
    if b["overflow"]:
        print(f"*** CUTOUTS OVERRUN THE PANEL BY {b['overflow']:.2f} mm ***")


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    p = lambda n: os.path.join(here, n)

    base = f"GT502_front_panel_{PANEL_W:.0f}x{PANEL_H:.0f}_both_screens"
    b = build_both(p(base + ".dxf"), p(base + ".svg"),
                   p(base + "_PRINT_1to1.svg"),
                   panel_h=PANEL_H, cut_gap=CUT_GAP)
    report("plain", b)
    if not b["overflow"]:
        write_spec(p("CUTTING_SPEC.txt"), base + ".dxf", b)

    bd = b["border"]
    print("\n=== back stiffener strips (nested on the same sheet) ===")
    for edge in ("left", "right", "top", "bottom"):
        w = bd["width"][edge]
        note = ""
        if edge in bd["capped"]:
            req, got, av = bd["capped"][edge]
            note = f"  <-- REDUCED from {req:.0f} (only {av:.2f} free)"
        print(f"  {edge:<7s} width {w:6.2f}   free {bd['avail'][edge]:6.2f}{note}")
    print()
    for (name, sx, sy, sw, sh), (_, nx, ny, _, _) in zip(bd["placed"], bd["nested"]):
        print(f"  {name:<14s} {sw:7.2f} x {sh:7.2f}"
              f"   bonds at ({sx:.2f}, {sy:.2f})"
              f"   nested at ({nx:.2f}, {ny:.2f})"
              f"   holes: {len(bd['strip_holes'][name])}")
    print(f"  sheet extent needed  {bd['sheet'][0]:.2f} x {bd['sheet'][1]:.2f}")

    if not WORD:
        print()
        raise SystemExit

    # Same panel with the text cut into the top. Screens drop so that only
    # GLASS_BOTTOM mm of metal is left below the 11in glass, which opens up
    # the band at the top for the lettering.
    slug = WORD.replace(" ", "_")
    stem = base + "_" + slug
    t = build_both(p(stem + ".dxf"), p(stem + ".svg"),
                   p(stem + "_PRINT_1to1.svg"),
                   panel_h=PANEL_H, cut_gap=CUT_GAP,
                   glass_bottom=GLASS_BOTTOM, word=WORD)
    report(f'with "{WORD}"', t)
    if not t["overflow"]:
        write_spec(p(f"CUTTING_SPEC_{slug}.txt"), stem + ".dxf", t,
                   extra_windows=t["n_letters"], word=WORD)
    print()
