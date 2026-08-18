#!/usr/bin/env python3
"""Trace the "ginger" lettering into a cut outline -> ginger_outline.py.

Source is ginger_source.png, the artwork as supplied: white lettering on a
transparent background, so the shape lives in the ALPHA channel and the RGB is
white everywhere. Alpha is what gets thresholded here; opening the file in a
viewer that flattens it onto white shows nothing at all.

The artwork is a raster, not a font, so there is no typeface to find and no
hinting to argue with - the pixels ARE the drawing. Steps:

  1. Threshold alpha at half, then clean: single-pixel specks and pinhole gaps
     left by the export are dropped. They are export noise, and a 0.1 mm hole
     is not something to hand a laser.
  2. Trace the pixel boundary exactly, round the 0.09 mm staircase off it with
     corner-cutting passes, and simplify with Douglas-Peucker. The steps are
     well inside the drawing's own tolerance either way; this is about not
     handing a cutter a path made of ten thousand tiny right angles.
  4. The i-dot is a separate piece - as it is in any script - so it gets a weld
     tab, the same 2.5 mm tie name_outlines.py uses for the same reason.
  5. Measure the narrowest stroke off the finished outline, and bake it in.

Run offline; needs pillow and shapely. The panel generator needs neither.

    pip install pillow shapely && python3 trace_ginger.py
"""

import math
import os

from PIL import Image
from shapely.geometry import LineString, Polygon
from shapely.ops import nearest_points, unary_union

from trace_hunabku import min_width, raster, simplify

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ginger_source.png")
OUT = os.path.join(HERE, "ginger_outline.py")

TARGET_W = 76.0            # width of the finished part, mm
MIN_SPECK = 40             # drop ink blobs smaller than this, px
MIN_HOLE = 200             # fill holes smaller than this, px
SMOOTH = 3                 # corner-cutting passes over the staircase
SIMPLIFY = 0.03            # Douglas-Peucker, mm
WELD = 2.5                 # weld tab width, mm
RASTER = 900               # px across, for the stroke measurement


# ------------------------------------------------------------------- raster in
def load_mask():
    """Alpha channel -> (mask, w, h), cropped to the ink and cleaned up."""
    im = Image.open(SRC).convert("RGBA")
    a = im.split()[3]
    a = a.crop(a.getbbox())
    w, h = a.size
    px = a.load()
    mask = [px[x, y] > 128 for y in range(h) for x in range(w)]

    def blobs(sel):
        seen = [False] * (w * h)
        out = []
        for i in range(w * h):
            if sel(i) and not seen[i]:
                stack, seen[i] = [i], True
                cells, edge = [], False
                while stack:
                    j = stack.pop()
                    cells.append(j)
                    r, c = divmod(j, w)
                    if r in (0, h - 1) or c in (0, w - 1):
                        edge = True
                    for k, ok in ((j-1, c > 0), (j+1, c < w-1),
                                  (j-w, r > 0), (j+w, r < h-1)):
                        if ok and sel(k) and not seen[k]:
                            seen[k] = True
                            stack.append(k)
                out.append((cells, edge))
        return out

    specks = holes = 0
    for cells, _ in blobs(lambda i: mask[i]):
        if len(cells) < MIN_SPECK:
            specks += 1
            for j in cells:
                mask[j] = False
    for cells, edge in blobs(lambda i: not mask[i]):
        if not edge and len(cells) < MIN_HOLE:
            holes += 1
            for j in cells:
                mask[j] = True
    print(f"  {w} x {h} px ink, dropped {specks} speck(s), filled {holes} pinhole(s)")
    return mask, w, h


# ------------------------------------------------------------- boundary tracing
def trace(mask, w, h):
    """Pixel-edge boundaries of the ink, as closed loops of (x, y) in px.

    Every ink pixel contributes the four edges of its square; an edge shared
    with another ink pixel cancels, so what survives is exactly the boundary,
    already consistently directed. Chaining that is bulletproof in a way that
    interpolating a contour out of a hard-edged alpha channel is not - and the
    staircase it leaves is smoothed off immediately afterwards.
    """
    def ink(x, y):
        return 0 <= x < w and 0 <= y < h and mask[y * w + x]

    edges = {}
    for y in range(h):
        for x in range(w):
            if not ink(x, y):
                continue
            for a, b, nx, ny in (((x, y), (x+1, y), x, y-1),
                                 ((x+1, y), (x+1, y+1), x+1, y),
                                 ((x+1, y+1), (x, y+1), x, y+1),
                                 ((x, y+1), (x, y), x-1, y)):
                if not ink(nx, ny):
                    edges.setdefault(a, []).append(b)

    loops = []
    while edges:
        start = next(iter(edges))
        loop, pt, prev = [start], start, None
        while True:
            outs = edges.get(pt)
            if not outs:
                break
            if len(outs) > 1 and prev:         # diagonal pinch: keep turning
                dx, dy = pt[0] - prev[0], pt[1] - prev[1]
                outs.sort(key=lambda q: (q[0] - pt[0]) * dy - (q[1] - pt[1]) * dx)
            nxt = outs.pop(0)
            if not outs:
                del edges[pt]
            prev, pt = pt, nxt
            if pt == start:
                break
            loop.append(pt)
        if len(loop) > 12:
            loops.append(loop)
    return loops


def chaikin(loop, rounds):
    """Corner cutting - turns the pixel staircase into a smooth path."""
    for _ in range(rounds):
        out = []
        for i, (x, y) in enumerate(loop):
            nx, ny = loop[(i + 1) % len(loop)]
            out.append((0.75*x + 0.25*nx, 0.75*y + 0.25*ny))
            out.append((0.25*x + 0.75*nx, 0.25*y + 0.75*ny))
        loop = out
    return loop


# -------------------------------------------------------------------- geometry
def to_polygons(rings):
    """Rings -> shapely polygons, each hole attached to the ring containing it."""
    flat = []
    for r in rings:                            # buffer(0) fixes any self-touch,
        g = Polygon(r).buffer(0)               # and may split a ring in two
        flat += [g] if g.geom_type == "Polygon" else list(g.geoms)
    polys = sorted((p for p in flat if not p.is_empty), key=lambda p: -p.area)
    depth = [sum(1 for q in polys if q is not p
                 and q.contains(p.representative_point())) for p in polys]
    out = []
    for p, d in zip(polys, depth):
        if d % 2:
            continue
        holes = [list(q.exterior.coords) for q, dq in zip(polys, depth)
                 if dq % 2 and p.contains(q.representative_point())]
        out.append(Polygon(list(p.exterior.coords), holes))
    return out


def weld(polys):
    """Tie the loose pieces - the i-dot - onto the body of the word."""
    polys = sorted(polys, key=lambda p: -p.area)
    joined, rest, tabs = polys[0], polys[1:], 0
    while rest:
        rest.sort(key=lambda p: joined.distance(p))
        p = rest.pop(0)
        a, b = nearest_points(joined, p)
        gap = a.distance(b)
        joined = unary_union([joined, p,
                              LineString([a, b]).buffer(WELD / 2,
                                                        cap_style="square")])
        tabs += 1
        print(f"  welded a loose piece across a {gap:.2f} mm gap")
    assert joined.geom_type == "Polygon", "welding did not make one piece"
    return joined, tabs


def main():
    mask, w, h = load_mask()
    mm = TARGET_W / w                          # px -> mm
    rings = [[(x * mm, (h - y) * mm) for x, y in chaikin(loop, SMOOTH)]
             for loop in trace(mask, w, h)]    # y flips: pixels run downwards
    print(f"  {len(rings)} contour(s) before welding")

    piece, welds = weld(to_polygons(rings))
    loops = [list(piece.exterior.coords)] + [list(r.coords) for r in piece.interiors]
    x0 = min(x for r in loops for x, _ in r)
    y0 = min(y for r in loops for _, y in r)
    loops = [simplify([(x - x0, y - y0) for x, y in r], SIMPLIFY) for r in loops]
    for i, r in enumerate(loops):              # boundary CCW, counters CW
        if Polygon(r).exterior.is_ccw != (i == 0):
            r.reverse()

    pw = max(x for r in loops for x, _ in r)
    ph = max(y for r in loops for _, y in r)
    half = max(pw, ph) / 2 * 1.02
    centred = [[(x - pw / 2, y - ph / 2) for x, y in r] for r in loops]
    m = raster(centred, RASTER, half)
    mmpx = 2 * half / RASTER
    area = sum(m) * mmpx * mmpx
    neck = min_width([bool(v) for v in m], RASTER, mmpx, probe=4.0,
                     min_area=1.0 / area)      # ignore anything under 1 mm2
    print(f"  {pw:.2f} x {ph:.2f} mm, {len(loops)} contour(s), {welds} weld(s), "
          f"narrowest stroke {neck:.2f} mm, {sum(len(r) for r in loops)} pts")

    with open(OUT, "w") as f:
        f.write(HEADER.format(w=pw, h=ph, neck=neck, weld=WELD, welds=welds,
                              tol=SIMPLIFY, n=len(loops)))
        f.write("GINGER = {\n")
        f.write(f'    "w": {pw:.3f}, "h": {ph:.3f},\n')
        f.write(f'    "neck": {neck:.2f}, "welds": {welds}, '
                f'"weld": {WELD:.1f},\n')
        f.write('    "rings": [\n')
        for r in loops:
            f.write("        [" + ", ".join(f"({x:.3f},{y:.3f})" for x, y in r)
                    + "],\n")
        f.write("    ],\n}\n")
    print("wrote", OUT)


HEADER = '''"""Outline of the "ginger" lettering, frozen. GENERATED - do not edit.

Regenerate with trace_ginger.py, which explains every step. Source artwork is
ginger_source.png, as supplied - white on transparent, so the shape is in its
alpha channel.

Coordinates are mm AT THE CUT SIZE, {w:.2f} x {h:.2f}, relative to the piece's
own bounding-box lower-left corner, y up. Do not scale them: the weld tab is a
fixed {weld:.1f} mm and would scale with everything else. Change TARGET_W in the
tracer and re-run instead.

rings[0] is the part boundary and the other {n} are counters that drop out. The
i-dot is a separate piece in the artwork and is tied on with {welds} weld tab -
without it the dot is a loose disc. Simplified to {tol} mm.

Narrowest stroke at this size is {neck:.2f} mm, measured off the finished
outline. That is nearly twice the {weld:.1f} mm-class necks in the name pieces,
so the lettering asks nothing unusual of the cutter.
"""

'''


if __name__ == "__main__":
    main()
