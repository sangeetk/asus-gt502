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

try:
    from name_outlines import NAMES, NAME_FONT, NAME_ASCENDER_MM
except ImportError:          # names are optional; panel still generates without
    NAMES, NAME_FONT, NAME_ASCENDER_MM = {}, None, None

try:
    from hunabku_outline import HUNAB_KU
except ImportError:          # so is the keyring
    HUNAB_KU = None

try:
    from ginger_outline import GINGER
except ImportError:          # and so is the lettering
    GINGER = None


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
BORDER_REQ = {"left": 17.0, "right": 11.0, "top": 24.5, "bottom": 21.5}

# Minimum air between a strip and the screen glass, per edge.
# BOTH side edges are run tight on purpose, to take the side strips as wide as
# the sheet allows: 17 left (17.39 free) and 11 right (11.39 free), leaving only
# ~0.39 either side. The 11in screen must therefore be bonded centred in its
# window to within about 0.39 mm - drift either way and a side strip will not
# sit flat. Bond that screen first, measure both gaps, then fit the strips.
# The bottom strip is run to 21.5 so its top edge all but meets the 11in glass
# bottom edge (21.815) and locates it. It must never exceed that figure: a strip
# under the glass sits the screen on a 3 mm step and tilts the display.
BORDER_CLEAR = {"left": 0.35, "right": 0.35, "top": 0.3, "bottom": 0.3}
BORDER_NEST_GAP = 4.0    # spacing between nested pieces
BORDER_WIN_MARGIN = 5.0  # margin from the 11in window edge to the nested pieces

# A 7th piece: a bar in the gap between the two screens. It gives the 6.25in
# glass a bottom edge to sit down onto, which it otherwise lacks - nothing else
# locates that screen vertically. Width is taken from the actual glass-to-glass
# gap less MID_CLEAR each side, so it can never touch either screen.
BORDER_MID_BAR = True
BORDER_MID_CLEAR = 0.25

# Decorative name pieces, cut from the slug inside the 6.25in window - that
# material is scrap too, so they also cost no extra sheet. Outlines live in
# name_outlines.py; each is one connected piece.
NAME_PIECES = ("Mayan", "Amishi")
NAME_MARGIN = 5.0        # clearance from the 6.25in window edge
NAME_GAP = 4.0           # vertical gap between the two names
BORDER_SIDE_PIECES = 2   # split each long side strip into this many pieces

# Hunab Ku keyring, cut from the leftover slug ABOVE the shorter nested strips
# inside the 11in window. Outline lives in hunabku_outline.py.
#
# Size is not a taste decision. The symbol's own line work is what it is, so
# every feature in it scales with the disc: at MEDAL_ART_DIA the narrowest
# metal and the narrowest slot are HUNAB_KU["min_metal"/"min_slot"] * dia/100,
# and below about 0.9 mm a fibre laser stops making a clean job of 3 mm
# aluminium. That pushes the disc AS LARGE as the free space allows rather than
# to any keyring-ish size - hence 52 mm, which is what fits.
MEDALLION = True
MEDAL_ART_DIA = 52.0      # the traced symbol's own disc
MEDAL_RIM_EXTRA = 1.0     # widen the outer rim past the artwork, see below
MEDAL_LUG_R = 4.0         # keyring lug radius
MEDAL_LUG_STANDOFF = 2.6  # lug centre this far OUTSIDE the disc edge
MEDAL_LUG_FILLET = 1.5    # fillet where the lug meets the disc
MEDAL_RING_HOLE = 3.5     # keyring hole diameter
MEDAL_MIN_FEATURE = 0.85  # refuse to draw it smaller than this, mm
MEDAL_GAP = 4.0           # clearance to the nested strips

# The "ginger" lettering, cut from what is left of the same slug, beside the
# keyring. Traced from artwork rather than set from a font - outline and size
# both live in ginger_outline.py, so there is no size constant here: the weld
# tab holding the i-dot on is a fixed 2.5 mm and must not scale with the word.
# Re-run trace_ginger.py to change the size.
GINGER_CUT = True
GINGER_GAP = 4.0          # clearance to the strips and the keyring
GINGER_MIN_NECK = 1.0     # refuse to cut it thinner than this

# The strips are nested INSIDE the 11in window - that slug is scrap anyway, so
# they cost no extra sheet and the sheet stays the size of the panel. Pieces are
# turned long-side-vertical to fit the window, which is why some carry a
# rotation: their holes rotate with them.

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

    def rect_corners(self, layer, x0, y0, w, h, radii):
        """Closed CCW polyline, per-corner radii as (bl, br, tr, tl).

        A zero radius emits a sharp corner. Lets a piece carry the panel's
        corner radius on just the corner that sits at the panel corner, so it
        can run the panel's full length instead of stopping at the arc tangent.
        """
        b, (r_bl, r_br, r_tr, r_tl) = BULGE_90, radii
        v = []
        v.append((x0 + r_bl, y0, 0.0) if r_bl else (x0, y0, 0.0))
        if r_br:
            v += [(x0 + w - r_br, y0, b), (x0 + w, y0 + r_br, 0.0)]
        else:
            v.append((x0 + w, y0, 0.0))
        if r_tr:
            v += [(x0 + w, y0 + h - r_tr, b), (x0 + w - r_tr, y0 + h, 0.0)]
        else:
            v.append((x0 + w, y0 + h, 0.0))
        if r_tl:
            v += [(x0 + r_tl, y0 + h, b), (x0, y0 + h - r_tl, 0.0)]
        else:
            v.append((x0, y0 + h, 0.0))
        if r_bl:
            v.append((x0, y0 + r_bl, b))

        out = ["0", "POLYLINE", "8", layer, "66", "1", "70", "1",
               "10", "0.0", "20", "0.0", "30", "0.0"]
        for x, y, bg in v:
            out += ["0", "VERTEX", "8", layer,
                    "10", f"{x:.4f}", "20", f"{y:.4f}", "30", "0.0",
                    "42", f"{bg:.10f}"]
        out += ["0", "SEQEND", "8", layer]
        self.ents += out

    def profile(self, layer, verts, ox=0.0, oy=0.0):
        """Closed polyline from a [(x, y, bulge)] profile, offset to (ox, oy)."""
        out = ["0", "POLYLINE", "8", layer, "66", "1", "70", "1",
               "10", "0.0", "20", "0.0", "30", "0.0"]
        for x, y, bg in verts:
            out += ["0", "VERTEX", "8", layer,
                    "10", f"{ox + x:.4f}", "20", f"{oy + y:.4f}", "30", "0.0",
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



def svg_corner_path(x0, y0, w, h, radii):
    """SVG path `d` for a rectangle with per-corner radii (bl, br, tr, tl).

    Traversed so that every arc sweeps in the increasing-angle direction, hence
    sweep-flag 1 throughout. A zero radius degenerates to a sharp corner.
    """
    r_bl, r_br, r_tr, r_tl = radii
    d = [f"M {x0 + r_bl:.3f},{y0:.3f}"]
    if r_br:
        d.append(f"L {x0 + w - r_br:.3f},{y0:.3f}")
        d.append(f"A {r_br:.3f},{r_br:.3f} 0 0 1 {x0 + w:.3f},{y0 + r_br:.3f}")
    else:
        d.append(f"L {x0 + w:.3f},{y0:.3f}")
    if r_tr:
        d.append(f"L {x0 + w:.3f},{y0 + h - r_tr:.3f}")
        d.append(f"A {r_tr:.3f},{r_tr:.3f} 0 0 1 {x0 + w - r_tr:.3f},{y0 + h:.3f}")
    else:
        d.append(f"L {x0 + w:.3f},{y0 + h:.3f}")
    if r_tl:
        d.append(f"L {x0 + r_tl:.3f},{y0 + h:.3f}")
        d.append(f"A {r_tl:.3f},{r_tl:.3f} 0 0 1 {x0:.3f},{y0 + h - r_tl:.3f}")
    else:
        d.append(f"L {x0:.3f},{y0 + h:.3f}")
    if r_bl:
        d.append(f"L {x0:.3f},{y0 + r_bl:.3f}")
        d.append(f"A {r_bl:.3f},{r_bl:.3f} 0 0 1 {x0 + r_bl:.3f},{y0:.3f}")
    else:
        d.append(f"L {x0:.3f},{y0:.3f}")
    return " ".join(d) + " Z"


def prof_rect(w, h, radii):
    """Vertex list [(x, y, bulge)] for a rectangle with per-corner radii."""
    b, (r_bl, r_br, r_tr, r_tl) = BULGE_90, radii
    v = [(r_bl, 0.0, 0.0) if r_bl else (0.0, 0.0, 0.0)]
    v += [(w - r_br, 0.0, b), (w, r_br, 0.0)] if r_br else [(w, 0.0, 0.0)]
    v += [(w, h - r_tr, b), (w - r_tr, h, 0.0)] if r_tr else [(w, h, 0.0)]
    v += [(r_tl, h, b), (0.0, h - r_tl, 0.0)] if r_tl else [(0.0, h, 0.0)]
    if r_bl:
        v.append((0.0, r_bl, b))
    return v


def prof_step(w_lo, w_hi, h, y_step, r_top, mirror):
    """Vertex list for a side rail that steps wider above y_step.

    Narrow (w_lo) alongside the tall screen, wide (w_hi) above it. r_top rounds
    the outer top corner. mirror=True builds the right-hand piece, whose outer
    edge is at x = w_hi. Coordinates are relative to the bounding box.
    """
    b = BULGE_90
    if not mirror:                      # outer edge at x = 0
        v = [(0.0, 0.0, 0.0), (w_lo, 0.0, 0.0), (w_lo, y_step, 0.0),
             (w_hi, y_step, 0.0), (w_hi, h, 0.0)]
        v += [(r_top, h, b), (0.0, h - r_top, 0.0)] if r_top else [(0.0, h, 0.0)]
        return v
    o = w_hi                            # outer edge at x = w_hi
    v = [(o, 0.0, 0.0)]
    v += [(o, h - r_top, b), (o - r_top, h, 0.0)] if r_top else [(o, h, 0.0)]
    v += [(0.0, h, 0.0), (0.0, y_step, 0.0),
          (o - w_lo, y_step, 0.0), (o - w_lo, 0.0, 0.0)]
    return v


def rot90(verts, h):
    """Rotate a profile 90 deg CCW. Bulges are unchanged by rotation."""
    return [(h - y, x, bg) for x, y, bg in verts]


def svg_path_verts(verts, ox=0.0, oy=0.0):
    """SVG path `d` from a [(x, y, bulge)] profile, offset to (ox, oy)."""
    pts = [(ox + x, oy + y, bg) for x, y, bg in verts]
    d = [f"M {pts[0][0]:.3f},{pts[0][1]:.3f}"]
    for i, (x, y, bg) in enumerate(pts):
        nx, ny, _ = pts[(i + 1) % len(pts)]
        if abs(bg) < 1e-9:
            d.append(f"L {nx:.3f},{ny:.3f}")
        else:
            th = 4 * math.atan(bg)
            chord = math.hypot(nx - x, ny - y)
            r = abs(chord / (2 * math.sin(th / 2)))
            large = 1 if abs(th) > math.pi else 0
            sweep = 1 if bg > 0 else 0
            d.append(f"A {r:.3f},{r:.3f} 0 {large} {sweep} {nx:.3f},{ny:.3f}")
    return " ".join(d) + " Z"

# ------------------------------------------------------------------ SVG preview
def svg(path, pw, ph, cutouts, refs, title, letters=(), holes=(),
        parts=(), ghosts=(), names=(), medal=None, canvas=None):
    pad = 20
    cw, chh = canvas or (pw, ph)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{cw+2*pad}" '
         f'height="{chh+2*pad}" viewBox="0 0 {cw+2*pad} {chh+2*pad}">',
         f'<rect width="100%" height="100%" fill="#f4f4f5"/>',
         f'<g transform="translate({pad},{pad}) scale(1,-1) translate(0,{-chh})">',
         f'<rect x="0" y="0" width="{pw}" height="{ph}" rx="3" '
         f'fill="#c8ccd0" stroke="#dc2626" stroke-width="0.8"/>']
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
    for x, y, vs in ghosts:        # where the strips end up, behind the panel
        s.append(f'<path d="{svg_path_verts(vs, x, y)}" '
                 f'fill="#9aa0a6" fill-opacity="0.35" stroke="#5f6368" '
                 f'stroke-width="0.5" stroke-dasharray="4 2"/>')
    for nx, ny, rings in names:    # name pieces, cut from the 6.25in slug
        d = " ".join(
            "M " + " L ".join(f"{nx+rx:.3f},{ny+ry:.3f}" for rx, ry in ring) + " Z"
            for ring in rings)
        s.append(f'<path d="{d}" fill="#c8ccd0" fill-rule="evenodd" '
                 f'stroke="#dc2626" stroke-width="0.5"/>')
    if medal:                      # keyring, cut from the 11in slug
        mx, my, mrings, (mhx, mhy), mhd = medal
        dd = " ".join(
            "M " + " L ".join(f"{mx+rx:.3f},{my+ry:.3f}" for rx, ry in ring) + " Z"
            for ring in mrings)
        s.append(f'<path d="{dd}" fill="#c8ccd0" fill-rule="evenodd" '
                 f'stroke="#dc2626" stroke-width="0.5"/>')
        s.append(f'<circle cx="{mx+mhx:.3f}" cy="{my+mhy:.3f}" r="{mhd/2:.3f}" '
                 f'fill="#f4f4f5" stroke="#dc2626" stroke-width="0.5"/>')
    for x, y, phs, vs in parts:    # the same strips, nested for cutting
        s.append(f'<path d="{svg_path_verts(vs, x, y)}" '
                 f'fill="#c8ccd0" stroke="#dc2626" stroke-width="0.8"/>')
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
    # Both layers are red: the whole file is a single through-cut operation.
    # The split only tells the cutter which side of the line the kerf goes.
    d.layer("CUT_OUTER", 1)     # part boundaries - kerf outside the line
    d.layer("CUT_INNER", 1)     # openings and holes - kerf inside the line
    d.rounded_rect("CUT_OUTER", 0, 0, PANEL_W, ph, PANEL_CORNER_R)
    d.rounded_rect("CUT_INNER", x11, y11, cw11, ch11, CUT_R)
    d.rounded_rect("CUT_INNER", x62, y62, cw62, ch62, CUT_R)

    hr = HOLE_DIA / 2
    holes = [hole_xy(spec, ph) for spec in MOUNT_HOLES]
    for hx, hyc in holes:
        d.circle("CUT_INNER", hx, hyc, HOLE_DIA)
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
            d.polygon("CUT_INNER", poly)

    bd = plan_border(PANEL_W, ph,
                     (x11 - ins11[0], y11 - ins11[2]) + SCREEN_11["glass"],
                     (x62 - ins625[0], y62 - ins625[2]) + SCREEN_625["glass"],
                     holes, (x11, y11, cw11, ch11))
    for name, nx, ny, nw, nh, rot, hs in bd["nested"]:
        d.profile("CUT_OUTER", bd["profiles"][name], nx, ny)
        for hxo, hyo in hs:
            d.circle("CUT_INNER", nx + hxo, ny + hyo, HOLE_DIA)

    nm = plan_names((x62, y62, cw62, ch62))
    for n in nm:
        for i, ring in enumerate(n["rings"]):
            # ring 0 is the part boundary, the rest are letter counters
            d.polygon("CUT_OUTER" if i == 0 else "CUT_INNER",
                      [(n["x"] + rx, n["y"] + ry) for rx, ry in ring])

    md = plan_medallion((x11, y11, cw11, ch11), bd["nested"])
    if md:
        for i, ring in enumerate(md["rings"]):
            # ring 0 is the part boundary, the rest are the symbol's own holes
            d.polygon("CUT_OUTER" if i == 0 else "CUT_INNER",
                      [(md["x"] + rx, md["y"] + ry) for rx, ry in ring])
        d.circle("CUT_INNER", md["x"] + md["hole"][0], md["y"] + md["hole"][1],
                 MEDAL_RING_HOLE)

    gg = plan_ginger((x11, y11, cw11, ch11), bd["nested"], md)
    if gg:
        for i, ring in enumerate(gg["rings"]):
            # ring 0 is the part boundary, the rest are counters in the letters
            d.polygon("CUT_OUTER" if i == 0 else "CUT_INNER",
                      [(gg["x"] + rx, gg["y"] + ry) for rx, ry in ring])

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
        + f". Plus {len(bd['nested'])} back stiffener pieces nested inside the "
          "11in window (grey dashed = where they bond behind the panel)"
        + (f", {len(nm)} name pieces in the 6.25in window" if nm else "")
        + (f", the {md['dia']:.0f} mm Hunab Ku keyring above the strips"
           if md else "")
        + (f" and the {gg['w']:.0f} mm \"ginger\" lettering beside it."
           if gg else "."),
        letters=letters, holes=svg_holes,
        names=([(n["x"], n["y"], n["rings"]) for n in nm]
               + ([(gg["x"], gg["y"], gg["rings"])] if gg else [])),
        medal=((md["x"], md["y"], md["rings"], md["hole"], MEDAL_RING_HOLE)
               if md else None),
        parts=[(nx, ny, hs, bd["profiles"][n])
               for n, nx, ny, nw, nh, _, hs in bd["nested"]],
        ghosts=[(sx, sy, bd["profiles"][n]) if False else
                (sx, sy, bd["assembled"][n]) for n, sx, sy, sw, sh in bd["placed"]],
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
                border=bd, names=nm, medal=md, ginger=gg,
                g11rect=(x11 - ins11[0], y11 - ins11[2], g11w, g11h),
                g62rect=(x62 - ins625[0], y62 - ins625[2], g62w, g62h),
                text_w=text_w, baseline=baseline, n_letters=len(letters),
                bridged=", ".join(c for c in BRIDGED if word and c in word))



def plan_border(pw, ph, g11rect, g62rect, holes, win11):
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
    width, capped, actual_clear = {}, {}, {}
    for edge, req in BORDER_REQ.items():
        room = avail[edge] - BORDER_CLEAR[edge]
        width[edge] = min(req, math.floor(room * 10) / 10)
        actual_clear[edge] = avail[edge] - width[edge]
        if width[edge] < req:
            capped[edge] = (req, width[edge], avail[edge])

    # Verticals run the full height between the panel's corner radii, so their
    # square ends stop exactly on the arc tangents and nothing juts past the
    # rounded corner. Horizontals butt between them.
    # Verticals run the panel's FULL height; the piece at each end carries the
    # panel's own corner radius on its outer corner so it matches the profile.
    vy, vh = 0.0, ph
    hx = width["left"]
    hw = pw - width["left"] - width["right"]

    # Each side strip is split into BORDER_SIDE_PIECES butt-jointed lengths so
    # the pieces are short enough to nest inside the 11in window.
    n = BORDER_SIDE_PIECES
    seg = vh / n
    placed, radii, profiles, boxes, desc = [], {}, {}, {}, {}
    R = PANEL_CORNER_R

    # Above the 11in glass the rails can be wider, because the 6.25in screen is
    # 6.04 narrower and sits 3.02 inboard on each side. The piece that spans
    # that boundary is therefore STEPPED rather than a plain rectangle, which
    # closes the gap to the 6.25in glass without adding any extra pieces.
    y_step = gy1 + gh1 + BORDER_MID_CLEAR        # top of the 11in glass + air
    upper = {"left": min(gx2, gx1 + gw1 and gx2) - BORDER_CLEAR["left"],
             "right": (pw - (gx2 + gw2)) - BORDER_CLEAR["right"]}
    upper = {k: math.floor(v * 10) / 10 for k, v in upper.items()}

    for side, sx in (("left", 0.0), ("right", pw - width["right"])):
        for k in range(n):
            name = f"{side} strip {chr(65 + k)}"
            lo = width[side]
            hi = max(lo, upper[side])
            steps = k * seg < y_step < (k + 1) * seg
            bw = hi if steps or (k * seg >= y_step) else lo
            bx = sx if side == "left" else pw - bw
            placed.append((name, bx, vy + k * seg, bw, seg))

            bl = br = tr = tl = 0.0
            if k == 0:
                bl, br = (R, 0.0) if side == "left" else (0.0, R)
            if k == n - 1:
                tl, tr = (R, 0.0) if side == "left" else (0.0, R)
            radii[name] = (bl, br, tr, tl)
            cname = {(1, 0, 0, 0): "bottom-left", (0, 1, 0, 0): "bottom-right",
                     (0, 0, 1, 0): "top-right", (0, 0, 0, 1): "top-left"}.get(
                        tuple(1 if r else 0 for r in radii[name]), None)
            y0 = vy + k * seg
            if steps and hi > lo:
                profiles[name] = prof_step(lo, hi, seg, y_step - k * seg,
                                           tl or tr, side == "right")
                lx = 0.0 if side == "left" else pw - lo
                boxes[name] = [(lx, y0, lo, y_step - y0),
                               (bx, y_step, hi, y0 + seg - y_step)]
                desc[name] = (
                    f"STEPPED, not a rectangle.\n"
                    f"             {lo:.2f} wide for the first {y_step - y0:.2f} "
                    f"of its length, then {hi:.2f} wide for the\n"
                    f"             remaining {y0 + seg - y_step:.2f}. The step is "
                    f"on the INNER edge; the outer edge\n"
                    f"             is straight."
                    + (f" R{PANEL_CORNER_R:.1f} on the {cname} corner."
                       if cname else ""))
            else:
                profiles[name] = prof_rect(bw, seg, radii[name])
                boxes[name] = [(bx, y0, bw, seg)]
                desc[name] = ("plain rectangle"
                              + (f", R{PANEL_CORNER_R:.1f} on the {cname} corner."
                                 if cname else "."))
    width["upper left"], width["upper right"] = upper["left"], upper["right"]
    avail["upper left"], avail["upper right"] = gx2, pw - (gx2 + gw2)
    actual_clear["upper left"] = gx2 - upper["left"]
    actual_clear["upper right"] = (pw - (gx2 + gw2)) - upper["right"]
    ux = upper["left"]
    uw = pw - upper["left"] - upper["right"]
    placed += [
        ("top strip",    ux, ph - width["top"], uw, width["top"]),
        ("bottom strip", hx, 0.0,               hw, width["bottom"]),
    ]
    for nm, bx_, by_, bw, bh in placed[n * 2:]:
        radii[nm] = (0.0, 0.0, 0.0, 0.0)
        profiles[nm] = prof_rect(bw, bh, radii[nm])
        boxes[nm] = [(bx_, by_, bw, bh)]
        desc[nm] = "plain rectangle, square corners."
    if BORDER_MID_BAR:
        # Sits centred in the air gap between the two screens.
        gap_lo, gap_hi = gy1 + gh1, gy2           # 11in glass top, 6.25in bottom
        mid_w = (gap_hi - gap_lo) - 2 * BORDER_MID_CLEAR
        assert mid_w > 0, "no room for a mid bar between the two screens"
        placed.append(("mid bar", ux, gap_lo + BORDER_MID_CLEAR, uw, mid_w))
        radii["mid bar"] = (0.0, 0.0, 0.0, 0.0)
        profiles["mid bar"] = prof_rect(uw, mid_w, radii["mid bar"])
        boxes["mid bar"] = [(ux, gap_lo + BORDER_MID_CLEAR, uw, mid_w)]
        desc["mid bar"] = "plain rectangle, square corners."
        width["mid"] = mid_w
        avail["mid"] = gap_hi - gap_lo
        actual_clear["mid"] = (gap_hi - gap_lo - mid_w) / 2

    # Which holes land in which strip, as offsets inside that strip.
    strip_holes = {}
    for name, sx, sy, sw, sh in placed:
        hits = [(x - sx, y - sy) for x, y in holes
                if sx <= x <= sx + sw and sy <= y <= sy + sh]
        strip_holes[name] = hits

    # No strip may touch either glass footprint.
    for name, *_ in placed:
        for sx, sy, sw, sh in boxes[name]:
            for gx, gy, gw, gh in (g11rect, g62rect):
                clear = (sx + sw <= gx or sx >= gx + gw
                         or sy + sh <= gy or sy >= gy + gh)
                assert clear, (f"{name} overlaps a screen glass footprint "
                               f"(sub-rect {sx:.2f},{sy:.2f} {sw:.2f}x{sh:.2f})")
    # Every hole must end up in exactly one strip, or a screw has nothing to pass through.
    assert sum(len(v) for v in strip_holes.values()) == len(holes), \
        "a mounting hole falls outside every strip"

    # ---- nest every piece inside the 11in window slug ----
    # Turn each piece long-side-vertical; a rotated piece takes its holes with
    # it, via (x, y) -> (h - y, x).
    assembled = {}
    gap, marg = BORDER_NEST_GAP, BORDER_WIN_MARGIN
    wx, wy, ww, wh_ = win11
    cx, nested = wx + marg, []
    for name, _, _, sw, sh in placed:
        rot = sw > sh
        nw, nh = (sh, sw) if rot else (sw, sh)
        hs = [((sh - hy), hx) if rot else (hx, hy)
              for hx, hy in strip_holes[name]]
        assembled[name] = profiles[name]
        profiles[name] = rot90(profiles[name], sh) if rot else profiles[name]
        nested.append((name, cx, wy + marg, nw, nh, rot, hs))
        cx += nw + gap

    # Everything must sit inside the window with a margin, and not touch.
    used_w = cx - gap - (wx + marg)
    assert used_w <= ww - 2 * marg, (
        f"nested pieces need {used_w:.2f} of the {ww - 2 * marg:.2f} available "
        "across the 11in window")
    for name, nx, ny, nw, nh, _, hs in nested:
        assert nx >= wx + marg and nx + nw <= wx + ww - marg, f"{name} outside window (x)"
        assert ny >= wy + marg and ny + nh <= wy + wh_ - marg, f"{name} outside window (y)"
        for hx, hy in hs:
            assert 0 <= hx <= nw and 0 <= hy <= nh, f"{name} hole outside the piece"
    for i in range(len(nested)):
        for j in range(i + 1, len(nested)):
            _, ax, ay, aw, ah, _, _ = nested[i]
            _, bx, by, bw, bh, _, _ = nested[j]
            assert (ax + aw <= bx or bx + bw <= ax
                    or ay + ah <= by or by + bh <= ay), \
                f"nested {nested[i][0]} overlaps {nested[j][0]}"

    return dict(width=width, capped=capped, avail=avail, placed=placed,
                clear=actual_clear, radii=radii, profiles=profiles,
                assembled=assembled, boxes=boxes, desc=desc,
                strip_holes=strip_holes, nested=nested, sheet=(pw, ph),
                nest_used=used_w, nest_room=ww - 2 * marg)


def plan_names(win62):
    """Stack the name pieces inside the 6.25in window slug, centred.

    Returns [] when name_outlines.py is absent. Asserts they fit, so a font or
    size change cannot silently push a name over the window edge.
    """
    words = [w for w in NAME_PIECES if w in NAMES]
    if not words:
        return []
    wx, wy, ww, wh = win62
    m, gap = NAME_MARGIN, NAME_GAP
    tot_h = sum(NAMES[w]["h"] for w in words) + gap * (len(words) - 1)
    max_w = max(NAMES[w]["w"] for w in words)
    assert tot_h <= wh - 2 * m, (
        f"names need {tot_h:.2f} of the {wh - 2 * m:.2f} available height")
    assert max_w <= ww - 2 * m, (
        f"widest name is {max_w:.2f}, only {ww - 2 * m:.2f} available")

    y = wy + (wh - tot_h) / 2          # centre the stack vertically
    out = []
    for w in reversed(words):          # first word ends up on top
        d = NAMES[w]
        out.append(dict(word=w, x=wx + (ww - d["w"]) / 2, y=y,
                        w=d["w"], h=d["h"], rings=d["rings"]))
        y += d["h"] + gap
    for n in out:                      # must sit clear of the window edge
        assert n["x"] >= wx + m - 1e-6 and n["x"] + n["w"] <= wx + ww - m + 1e-6
        assert n["y"] >= wy + m - 1e-6 and n["y"] + n["h"] <= wy + wh - m + 1e-6
    return out

# --------------------------------------------------------------- hunab ku part
def arc_pts(cx, cy, r, a0, a1, ccw, seg=0.25):
    """Points along an arc from a0 to a1 (radians), excluding the last."""
    span = (a1 - a0) % (2 * math.pi) if ccw else -((a0 - a1) % (2 * math.pi))
    n = max(2, int(abs(span) * r / seg) + 1)
    return [(cx + r * math.cos(a0 + span * k / n),
             cy + r * math.sin(a0 + span * k / n)) for k in range(n)]


def medallion_rings(art_dia):
    """The Hunab Ku keyring as closed rings, origin at its bounding-box corner.

    Two things are added to the traced artwork, both for the keyring:

    - the outer boundary is drawn MEDAL_RIM_EXTRA outside the symbol's own
      disc. The artwork's outer ring is about as thin as everything else in it,
      and that ring is what the keyring hangs off, so it gets doubled up. It
      reads as a slightly heavier rim and nothing else moves.
    - a lug on top, filleted into the disc, carrying the keyring hole. There is
      nowhere inside the symbol to put a hole: the widest solid area in it takes
      a 10 mm circle at 55 mm diameter, and that is off to one side, so a hole
      there would both deface it and hang it crooked.

    Returns rings[0] = boundary, rings[1:] = the symbol's own holes.
    """
    assert HUNAB_KU, "hunabku_outline.py is missing"
    s = art_dia / HUNAB_KU["nominal_dia"]
    R = art_dia / 2 + MEDAL_RIM_EXTRA          # outer rim of the part
    rl, rf = MEDAL_LUG_R, MEDAL_LUG_FILLET
    d = R + MEDAL_LUG_STANDOFF                 # lug centre, above the disc
    assert d < R + rl, "lug does not reach the disc"

    # Fillet centre: R + rf from the disc centre, rl + rf from the lug centre.
    A, B = R + rf, rl + rf
    fy = (A * A - B * B + d * d) / (2 * d)
    assert A * A - fy * fy > 0, "no fillet fits between disc and lug"
    fx = math.sqrt(A * A - fy * fy)

    a_disc = math.atan2(fy, fx)                # disc tangent, right-hand side
    a_lug = math.atan2(fy - d, fx)             # lug tangent, right-hand side
    ang_to_o = math.atan2(-fy, -fx)            # fillet centre -> disc tangent
    ang_to_c = math.atan2(d - fy, -fx)         # fillet centre -> lug tangent

    ring = []
    ring += arc_pts(0, 0, R, math.pi - a_disc, a_disc, True)      # the long way
    ring += arc_pts(fx, fy, rf, ang_to_o, ang_to_c, False)        # right fillet
    ring += arc_pts(0, d, rl, a_lug, math.pi - a_lug, True)       # over the lug
    ring += arc_pts(-fx, fy, rf, math.pi - ang_to_c,
                    math.pi - ang_to_o, False)                    # left fillet

    holes = [[(x * s, y * s) for x, y in r] for r in HUNAB_KU["rings"][1:]]
    for h in holes:                            # the artwork must stay in its disc
        assert max(math.hypot(x, y) for x, y in h) < art_dia / 2, \
            "a hole in the artwork crosses its own disc"

    w, h = 2 * R, R + d + rl
    ox, oy = R, R                              # bbox corner -> disc centre
    rings = [[(x + ox, y + oy) for x, y in r] for r in [ring] + holes]
    hole_xy = (ox, oy + d)

    # Narrowest metal and slot scale straight off the traced numbers.
    mm = HUNAB_KU["min_metal"] * art_dia / HUNAB_KU["nominal_dia"]
    ms = HUNAB_KU["min_slot"] * art_dia / HUNAB_KU["nominal_dia"]
    assert min(mm, ms) >= MEDAL_MIN_FEATURE, (
        f"at {art_dia:.1f} mm the symbol needs {min(mm, ms):.2f} mm features, "
        f"below the {MEDAL_MIN_FEATURE:.2f} mm limit - make it bigger")
    neck = min(math.hypot(x - hole_xy[0], y - hole_xy[1])
               for x, y in rings[0]) - MEDAL_RING_HOLE / 2
    assert neck >= 1.5, f"only {neck:.2f} mm of metal around the keyring hole"

    return dict(rings=rings, w=w, h=h, hole=hole_xy, dia=2 * R,
                min_metal=mm, min_slot=ms, neck=neck, art=art_dia)


def free_rects(win, blockers, marg, gap):
    """Maximal free rectangles inside a window slug, above what is already in it.

    Only floors that sit on top of something are considered, which is all this
    nest ever needs: every stiffener piece stands on the bottom edge, so the
    leftovers are always bands above them.
    """
    wx, wy, ww, wh = win
    top = wy + wh - marg
    out = []
    for floor in sorted({wy + marg} | {by + bh + gap for _, by, _, bh in blockers}):
        if floor >= top:
            continue
        blocked = sorted((bx - gap, bx + bw + gap)
                         for bx, by, bw, bh in blockers if by + bh > floor)
        cur = wx + marg
        for lo, hi in blocked + [(wx + ww - marg, wx + ww - marg)]:
            if lo > cur:
                out.append((cur, floor, min(lo, wx + ww - marg) - cur, top - floor))
            cur = max(cur, hi)
    return out


def plan_medallion(win11, nested):
    """Drop the keyring into the space left over above the shorter strips.

    Finds the free rectangle rather than being told where it is, so re-nesting
    the stiffener pieces moves the keyring instead of quietly overlapping one.
    """
    if not (MEDALLION and HUNAB_KU):
        return None
    m = medallion_rings(MEDAL_ART_DIA)
    boxes = [(nx, ny, nw, nh) for _, nx, ny, nw, nh, _, _ in nested]
    fits = [r for r in free_rects(win11, boxes, BORDER_WIN_MARGIN, MEDAL_GAP)
            if r[2] >= m["w"] and r[3] >= m["h"]]
    assert fits, (f"no {m['w']:.1f} x {m['h']:.1f} space left in the 11in "
                  "window for the keyring")
    fx, fy, fw, fh = max(fits, key=lambda r: r[2] * r[3])
    m["x"] = fx + (fw - m["w"]) / 2             # centred in the free rectangle
    m["y"] = fy + (fh - m["h"]) / 2
    m["free"] = (fx, fy, fw, fh)
    return m


def plan_ginger(win11, nested, medal):
    """Put the lettering in what is left of the slug once the keyring has its spot.

    Same free-rectangle search as the keyring, with the keyring itself added as
    something to keep clear of, so the two can never be planned on top of each
    other.
    """
    if not (GINGER_CUT and GINGER):
        return None
    g = dict(GINGER)
    assert g["neck"] >= GINGER_MIN_NECK, (
        f"the lettering's narrowest stroke is {g['neck']:.2f} mm, under the "
        f"{GINGER_MIN_NECK:.2f} mm limit - cut it larger in trace_ginger.py")
    boxes = [(nx, ny, nw, nh) for _, nx, ny, nw, nh, _, _ in nested]
    if medal:
        boxes.append((medal["x"], medal["y"], medal["w"], medal["h"]))
    fits = [r for r in free_rects(win11, boxes, BORDER_WIN_MARGIN, GINGER_GAP)
            if r[2] >= g["w"] and r[3] >= g["h"]]
    assert fits, (f"no {g['w']:.1f} x {g['h']:.1f} space left in the 11in window "
                  "for the lettering - lower TARGET_W in trace_ginger.py")
    fx, fy, fw, fh = max(fits, key=lambda r: r[2] * r[3])
    g["x"] = fx + (fw - g["w"]) / 2
    g["y"] = fy + (fh - g["h"]) / 2
    g["free"] = (fx, fy, fw, fh)
    return g


SPEC = """CUSTOM FRONT PANEL - CUTTING SPECIFICATION
ASUS ROG GT502, aluminium front panel with two touchscreen cutouts
==================================================================

DXF FILE   : {dxf}
MATERIAL   : Aluminium sheet, 3.0 mm thickness
QUANTITY   : 1 off of everything on the sheet - the panel plus the {np} back
             stiffener pieces nested inside its large window, plus {nnm}
             decorative name pieces nested inside the smaller window, plus
             {nmed} keyring and {ngin} lettering piece nested in the large
             window above the stiffeners.
             ONE cutting job, {ntot} parts delivered in total.
PROCESS    : Laser cut (fibre) or waterjet
UNITS      : Millimetres. DXF is AC1009 / R12 ASCII, $INSUNITS = 4 (mm).
GEOMETRY   : Panel outer profile + internal cutouts, plus {np} separate
             stiffener pieces nested INSIDE the large window opening.
             Those pieces are separate parts, NOT features of the panel.
TOLERANCE  : +/- 0.15 mm on all cutout sizes and positions.
LAYERS     : Every contour in this file is a THROUGH-CUT. There is no
             engraving, scoring or rastering anywhere in the drawing, and
             nothing in it should be treated as such.
             All geometry is drawn in ONE colour (red, ACI 1) so there is no
             colour mapping to interpret. Two layers are used purely to say
             which side of the line the kerf belongs on:
               CUT_OUTER  part boundaries - the panel profile and the
                          outline of every separate part nested inside it
               CUT_INNER  openings - windows, holes, and every internal
                          contour of a nested part
             If your workflow needs everything on a single layer, merging
             them is fine; the layer names carry no operation meaning.
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

BACK STIFFENER PIECES - {np} pieces, same 3 mm aluminium
------------------------------------------------------------------
These are SEPARATE PARTS nested INSIDE the large 11 inch window opening.
That material is being removed anyway, so they use no extra sheet: total
sheet extent stays {sheetw:.2f} x {sheeth:.2f}, the panel size.

** CUT ORDER: please cut these {np} pieces BEFORE cutting the large window
   outline that surrounds them. Once the window contour is cut the slug
   they sit in drops away. **

** CUT EVERY PIECE EXACTLY AS DRAWN. Do not simplify any of them to a
   plain rectangle. {nr} of the {np} have a rounded corner, and {ns} of
   those are STEPPED (wider along part of their length). The sizes quoted
   below are BOUNDING sizes - the true outline is in the DXF geometry. **

They bond flat to the BACK of the panel and are not visible in the
finished build.

{striplist}

Strip hole positions are offsets from that strip's own lower-left corner
and match the panel holes, so one screw passes through both layers.
Deburr both faces - these bond flat against the panel.
{namesec}{medalsec}{gingersec}"""


MEDAL_NOTE = """
HUNAB KU KEYRING - 1 off, same 3 mm aluminium
------------------------------------------------------------------
One more separate part, nested inside the LARGE (11 inch) window above
the stiffener pieces. Scrap material again, so no extra sheet.

** CUT ORDER: cut this piece BEFORE the 11 inch window outline, same
   reason as the stiffener pieces. **

   bounding size    {w:.2f} W x {h:.2f} H, drawn at X {x:.2f}, Y {y:.2f}
   disc             {dia:.2f} diameter, centre X {cx:.2f}, Y {cy:.2f}
   keyring hole     {hd:.2f} diameter THROUGH at X {hx:.2f}, Y {hy:.2f}
   contours         1 outer boundary + {nh} internal + the keyring hole

** THE NARROWEST METAL IN THIS PART IS {mm:.2f} mm AND THE NARROWEST SLOT
   {ms:.2f} mm. ** That is the finest work on the sheet. Please confirm you
   can hold it in 3 mm aluminium before cutting; if you cannot, say so
   rather than opening the slots out, and this part will be dropped or
   redrawn. Nothing else on the sheet depends on it.

The outline is a traced symbol, supplied as fine polylines. Cut it exactly
as drawn: do not smooth it, do not re-fit arcs, do not thin or thicken
anything. The stepped edges are meant to be stepped.

The piece is one connected part - every internal contour is a hole that
drops out, and nothing in it is a loose island.
"""


GINGER_NOTE = """
"GINGER" LETTERING - 1 off, same 3 mm aluminium
------------------------------------------------------------------
One more separate part, nested inside the LARGE (11 inch) window beside
the keyring. Scrap material again, so no extra sheet.

** CUT ORDER: cut this piece BEFORE the 11 inch window outline, same
   reason as everything else nested inside it. **

   bounding size    {w:.2f} W x {h:.2f} H, drawn at X {x:.2f}, Y {y:.2f}
   contours         1 outer boundary + {nh} counters, all of which drop out
   narrowest stroke {neck:.2f} mm

This is ONE connected piece of brush lettering, traced from artwork - not
type. The dot of the "i" is a separate shape in the artwork and is tied to
the letter below it by a {weld:.1f} mm WELD TAB drawn into the outline. Without
that tab the dot is a loose disc. Please cut the outline exactly as
supplied: do not remove the tab, do not smooth the curves, do not re-fit
arcs, and do not thin or thicken the strokes.

Curves are supplied as fine polylines, which is what tracing artwork
gives; they are already simplified and are meant to be cut as they are.
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
        np=len(b["border"]["nested"]), nnm=len(b["names"]),
        nmed=1 if b["medal"] else 0, ngin=1 if b["ginger"] else 0,
        ntot=1 + len(b["border"]["nested"]) + len(b["names"])
             + (1 if b["medal"] else 0) + (1 if b["ginger"] else 0),
        gingersec=("" if not b["ginger"] else GINGER_NOTE.format(
            w=b["ginger"]["w"], h=b["ginger"]["h"],
            x=b["ginger"]["x"], y=b["ginger"]["y"],
            nh=len(b["ginger"]["rings"]) - 1, neck=b["ginger"]["neck"],
            weld=b["ginger"]["weld"])),
        nr=sum(1 for r in b["border"]["radii"].values() if any(r)),
        ns=sum(1 for d in b["border"]["desc"].values() if "STEPPED" in d),
        namesec=("" if not b["names"] else
                 "\nDECORATIVE NAME PIECES - {} off, same 3 mm aluminium\n"
                 "------------------------------------------------------------------\n"
                 "Nested inside the SMALLER (6.25 inch) window opening - again,\n"
                 "scrap material, so no extra sheet is used.\n\n"
                 "** CUT ORDER: cut these before the 6.25 inch window outline that\n"
                 "   surrounds them, for the same reason as the stiffener pieces. **\n\n"
                 "Each name is ONE connected piece of script lettering. The outer\n"
                 "contour is the part boundary; the inner contours are letter\n"
                 "counters and drop out. Curves are supplied as fine polylines -\n"
                 "please cut them as drawn, do not re-fit arcs or smooth them.\n\n"
                 + "".join(
                     "   {:<8s} {:7.2f} W x {:6.2f} H   at X {:.2f}, Y {:.2f}"
                     "   ({} contours)\n".format(
                         n["word"], n["w"], n["h"], n["x"], n["y"], len(n["rings"]))
                     for n in b["names"])
                 + "\nTypeface: {}. Narrowest neck in the lettering is {:.2f} mm\n".format(
                       NAME_FONT or "?",
                       min(NAMES[n["word"]].get("min_neck", 0) for n in b["names"]))
                 + "and that is deliberate and cuttable in 3 mm. Please cut the\n"
                   "outlines exactly as supplied: do not smooth them, do not re-fit\n"
                   "arcs, and do not thin or thicken the strokes.\n"
                 ).format(len(b["names"])),
        medalsec=("" if not b["medal"] else MEDAL_NOTE.format(
            w=b["medal"]["w"], h=b["medal"]["h"],
            x=b["medal"]["x"], y=b["medal"]["y"], dia=b["medal"]["dia"],
            cx=b["medal"]["x"] + b["medal"]["w"] / 2,
            cy=b["medal"]["y"] + b["medal"]["dia"] / 2,
            hd=MEDAL_RING_HOLE,
            hx=b["medal"]["x"] + b["medal"]["hole"][0],
            hy=b["medal"]["y"] + b["medal"]["hole"][1],
            nh=len(b["medal"]["rings"]) - 1,
            mm=b["medal"]["min_metal"], ms=b["medal"]["min_slot"])),
        striplist="\n\n".join(
            f"   {name.upper():<16s} bounding size {nw:.2f} W x {nh:.2f} H"
            f"   drawn at X {nx:.2f}, Y {ny:.2f}"
            f"\n      shape: {b['border']['desc'][name]}"
            + (f"\n      NOTE: drawn rotated 90 deg from how it is fitted."
               if rot else "")
            + ("".join(f"\n      hole at X {hx:.2f}, Y {hy:.2f}"
                       for hx, hy in hs) or "\n      no holes")
            for name, nx, ny, nw, nh, rot, hs in b["border"]["nested"]),
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
    for edge in ("left", "right", "top", "bottom", "mid"):
        if edge not in bd["width"]:
            continue
        w = bd["width"][edge]
        note = ""
        if edge in bd["capped"]:
            req, got, av = bd["capped"][edge]
            note = f"  <-- REDUCED from {req:.0f} (only {av:.2f} free)"
        print(f"  {edge:<7s} width {w:6.2f}   free {bd['avail'][edge]:6.2f}"
              f"   clearance to glass {bd['clear'][edge]:5.2f}{note}")
    print()
    for (name, sx, sy, sw, sh), (_, nx, ny, nw, nh, rot, hs) in zip(
            bd["placed"], bd["nested"]):
        print(f"  {name:<15s} {sw:7.2f} x {sh:7.2f}"
              f"   bonds at ({sx:7.2f},{sy:7.2f})"
              f"   nested {nw:6.2f} x {nh:6.2f} at ({nx:7.2f},{ny:7.2f})"
              f"{'  ROTATED 90' if rot else '':<12s} holes: {len(hs)}")
    print(f"  {len(bd['nested'])} pieces use {bd['nest_used']:.2f} of "
          f"{bd['nest_room']:.2f} across the 11in window")
    print(f"  SHEET EXTENT {bd['sheet'][0]:.2f} x {bd['sheet'][1]:.2f}"
          "  (panel only - pieces cost no extra sheet)")
    if b["names"]:
        print(f"\n=== name pieces ({NAME_FONT}, nested in the 6.25in window) ===")
        for n in b["names"]:
            print(f"  {n['word']:<8s} {n['w']:7.2f} x {n['h']:6.2f}"
                  f"   at ({n['x']:.2f}, {n['y']:.2f})"
                  f"   1 outer + {len(n['rings']) - 1} counter(s)")

    if b["medal"]:
        m = b["medal"]
        print(f"\n=== hunab ku keyring (nested above the strips) ===")
        print(f"  disc {m['dia']:.1f} dia, {m['w']:.2f} x {m['h']:.2f} overall"
              f"   at ({m['x']:.2f}, {m['y']:.2f})")
        print(f"  free rectangle {m['free'][2]:.2f} x {m['free'][3]:.2f}"
              f" at ({m['free'][0]:.2f}, {m['free'][1]:.2f})")
        print(f"  narrowest metal {m['min_metal']:.2f}, narrowest slot "
              f"{m['min_slot']:.2f}, keyring hole wall {m['neck']:.2f}")
    if b["ginger"]:
        g = b["ginger"]
        print("\n=== \"ginger\" lettering (traced artwork, beside the keyring) ===")
        print(f"  {g['w']:.2f} x {g['h']:.2f}   at ({g['x']:.2f}, {g['y']:.2f})"
              f"   in a {g['free'][2]:.2f} x {g['free'][3]:.2f} free rectangle")
        print(f"  narrowest stroke {g['neck']:.2f}, {g['welds']} weld tab, "
              f"1 outer + {len(g['rings']) - 1} counters")
    parts = (1 + len(bd["nested"]) + len(b["names"])
             + (1 if b["medal"] else 0) + (1 if b["ginger"] else 0))
    print(f"\ntotal parts on the sheet: {parts}")
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
