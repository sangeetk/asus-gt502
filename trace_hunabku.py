#!/usr/bin/env python3
"""Trace the Hunab Ku artwork into cuttable outlines -> hunabku_outline.py.

Source: "Maya calendar (Hunab-Ku).svg" from Wikimedia Commons, released into
the PUBLIC DOMAIN by its author (user Keepscases). A copy is kept here as
hunab_ku_source.svg so this script needs no network.

What it does, and why each step exists:

  1. Flattens the artwork's single black path to polylines. The file draws the
     whole symbol as ONE path with four subpaths, filled EVEN-ODD: subpath 0 is
     the disc, the other three are the white areas. Rendered any other way
     (nonzero) the top half of the symbol comes out inverted, so even-odd is
     not a preference here, it is the artwork.
  2. Replaces subpath 0 with an exact least-squares circle. It is a circle in
     the file (r = 250.02 +/- 0.2 of 250) and the part boundary wants to be a
     true circle, not a 1600-point approximation of one.
  3. Normalises to a 100.00 mm nominal disc diameter, y UP (the SVG is y down),
     origin at the disc centre. generate_panel_dxf.py scales from there.
  4. Simplifies with Douglas-Peucker so the frozen file is readable.
  5. Measures the narrowest metal and the narrowest slot by rasterising and
     morphologically opening the result, and bakes those two numbers in. They
     are what decides whether the piece is cuttable at a given diameter, so
     they must come off the geometry rather than off an eyeball.

Everything is stdlib, but it is still run once and frozen, matching
name_outlines.py, so the panel generator stays a single file with no work to
do at import time.
"""

import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "hunab_ku_source.svg")
OUT = os.path.join(HERE, "hunabku_outline.py")

PATH_ID = "path2885"        # the black path: the whole symbol
NOMINAL_DIA = 100.0         # frozen coordinates are mm at this disc diameter
FLAT_TOL = 0.02             # bezier flattening, artwork units (disc = 500)
SIMPLIFY = 0.03             # Douglas-Peucker, mm at NOMINAL_DIA
RASTER = 900                # px across the disc, for the feature measurement


# ------------------------------------------------------------------- svg paths
def tokenize(d):
    return re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?", d)


def flatten(d, tol):
    """SVG path -> [subpath], each a list of (x, y). M/L/H/V/C/S/Z only."""
    t = tokenize(d)
    i = 0
    subs, cur = [], []
    x = y = sx = sy = 0.0
    cmd = None
    c2 = None

    def num():
        nonlocal i
        v = float(t[i])
        i += 1
        return v

    def bez(p0, p1, p2, p3):
        L = math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)
        n = max(4, min(400, int(3 * (L / tol) ** 0.5)))
        out = []
        for k in range(1, n + 1):
            s = k / n
            m = 1 - s
            out.append((m**3*p0[0] + 3*m*m*s*p1[0] + 3*m*s*s*p2[0] + s**3*p3[0],
                        m**3*p0[1] + 3*m*m*s*p1[1] + 3*m*s*s*p2[1] + s**3*p3[1]))
        return out

    while i < len(t):
        if re.match(r"[A-Za-z]", t[i]):
            cmd = t[i]
            i += 1
        c = cmd
        if c in "Mm":
            if cur:
                subs.append(cur)
            a, b = num(), num()
            x, y = (x + a, y + b) if c == "m" else (a, b)
            sx, sy = x, y
            cur = [(x, y)]
            cmd = "l" if c == "m" else "L"
            c2 = None
        elif c in "Ll":
            a, b = num(), num()
            x, y = (x + a, y + b) if c == "l" else (a, b)
            cur.append((x, y))
            c2 = None
        elif c in "Hh":
            a = num()
            x = x + a if c == "h" else a
            cur.append((x, y))
            c2 = None
        elif c in "Vv":
            b = num()
            y = y + b if c == "v" else b
            cur.append((x, y))
            c2 = None
        elif c in "CcSs":
            if c in "Cc":
                a1, b1, a2, b2, a3, b3 = (num() for _ in range(6))
                if c == "c":
                    p1, p2, p3 = (x+a1, y+b1), (x+a2, y+b2), (x+a3, y+b3)
                else:
                    p1, p2, p3 = (a1, b1), (a2, b2), (a3, b3)
            else:
                a2, b2, a3, b3 = (num() for _ in range(4))
                p2, p3 = ((x+a2, y+b2), (x+a3, y+b3)) if c == "s" else ((a2, b2), (a3, b3))
                p1 = (2*x - c2[0], 2*y - c2[1]) if c2 else (x, y)
            cur += bez((x, y), p1, p2, p3)
            c2, x, y = p2, p3[0], p3[1]
        elif c in "Zz":
            if cur:
                subs.append(cur)
            cur = []
            x, y = sx, sy
            cmd, c2 = None, None
        else:
            raise SystemExit("unhandled path command %r" % c)
    if cur:
        subs.append(cur)
    return subs


# -------------------------------------------------------------------- geometry
def fit_circle(pts):
    """Least-squares circle through pts -> (cx, cy, r)."""
    n = len(pts)
    sx = sy = sxx = syy = sxy = sxz = syz = sz = 0.0
    for x, y in pts:
        z = x*x + y*y
        sx += x; sy += y; sz += z
        sxx += x*x; syy += y*y; sxy += x*y
        sxz += x*z; syz += y*z
    a = [[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, float(n)]]
    b = [sxz, syz, sz]
    for col in range(3):                       # gaussian elimination
        p = max(range(col, 3), key=lambda r: abs(a[r][col]))
        a[col], a[p] = a[p], a[col]
        b[col], b[p] = b[p], b[col]
        for r in range(col + 1, 3):
            f = a[r][col] / a[col][col]
            for k in range(col, 3):
                a[r][k] -= f * a[col][k]
            b[r] -= f * b[col]
    s = [0.0]*3
    for r in (2, 1, 0):
        s[r] = (b[r] - sum(a[r][k]*s[k] for k in range(r+1, 3))) / a[r][r]
    cx, cy = s[0]/2, s[1]/2
    return cx, cy, math.sqrt(s[2] + cx*cx + cy*cy)


def simplify(pts, eps):
    """Douglas-Peucker on a closed ring, keeping it closed."""
    def dp(seq):
        if len(seq) < 3:
            return seq
        x0, y0 = seq[0]
        x1, y1 = seq[-1]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        worst, wi = -1.0, 0
        for i in range(1, len(seq) - 1):
            x, y = seq[i]
            d = (abs(dy*x - dx*y + x1*y0 - y1*x0) / L if L > 1e-12
                 else math.hypot(x - x0, y - y0))
            if d > worst:
                worst, wi = d, i
        if worst <= eps:
            return [seq[0], seq[-1]]
        return dp(seq[:wi + 1])[:-1] + dp(seq[wi:])
    # split the ring at two far-apart points so no long chord can shortcut it
    h = len(pts) // 2
    return dp(pts[:h + 1])[:-1] + dp(pts[h:] + [pts[0]])[:-1]


def area(p):
    return 0.5 * sum(p[i][0]*p[(i+1) % len(p)][1] - p[(i+1) % len(p)][0]*p[i][1]
                     for i in range(len(p)))


BIG = 1e12                  # stands in for infinity in the distance transform


# ------------------------------------------------- narrowest metal / slot check
def raster(rings, n, half):
    """Even-odd fill of rings into an n x n mask covering [-half, half]^2."""
    edges = []
    for r in rings:
        for i in range(len(r)):
            edges.append((r[i], r[(i + 1) % len(r)]))
    mask = bytearray(n * n)
    for row in range(n):
        y = -half + (row + 0.5) * 2 * half / n
        xs = []
        for (x0, y0), (x1, y1) in edges:
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) / (y1 - y0) * (x1 - x0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            a = int((xs[k] + half) * n / (2 * half))
            b = int((xs[k+1] + half) * n / (2 * half))
            for px in range(max(0, a), min(n, b)):
                mask[row * n + px] = 1
    return mask


def _dt1d(f):
    """Felzenszwalb & Huttenlocher 1D squared distance transform."""
    n = len(f)
    d = [0.0]*n; v = [0]*n; z = [0.0]*(n+1); k = 0
    v[0], z[0], z[1] = 0, -BIG, BIG
    for q in range(1, n):
        s = (((f[q] + q*q) - (f[v[k]] + v[k]*v[k])) / (2*q - 2*v[k])
             if q != v[k] else BIG)
        while s <= z[k]:
            k -= 1
            s = ((f[q] + q*q) - (f[v[k]] + v[k]*v[k])) / (2*q - 2*v[k])
        k += 1
        v[k], z[k], z[k+1] = q, s, BIG
    k = 0
    for q in range(n):
        while z[k+1] < q:
            k += 1
        d[q] = (q - v[k])**2 + f[v[k]]
    return d


def edt(inside, n):
    """Squared distance from each pixel to the nearest pixel NOT in `inside`."""
    f = [0.0 if not inside[i] else BIG for i in range(n*n)]
    g = [0.0]*(n*n)
    for c in range(n):
        col = _dt1d([f[r*n + c] for r in range(n)])
        for r in range(n):
            g[r*n + c] = col[r]
    out = [0.0]*(n*n)
    for r in range(n):
        out[r*n:(r+1)*n] = _dt1d(g[r*n:(r+1)*n])
    return out


def min_width(inside, n, mm_per_px, probe=3.0, min_area=0.0006, show=""):
    """Width of the narrowest real feature in `inside`, in mm.

    Opening the set with a disc of radius t deletes everything narrower than
    2t. What is left over - the "thin set" - is split into connected pieces and
    each piece is measured by its own largest inscribed circle, so a piece that
    is 1 mm wide reports 1 mm however long it is. Sharp corners always shed a
    few pixels, so pieces below min_area of the phase are discarded as noise
    rather than reported as hairline features.
    """
    d = edt(inside, n)
    t = probe / 2 / mm_per_px
    er = [v > t*t for v in d]
    d2 = edt([not e for e in er], n)
    thin = [inside[i] and not d2[i] <= t*t for i in range(n*n)]
    total = sum(1 for v in inside if v)
    seen = [False]*(n*n)
    feats = []
    for i in range(n*n):
        if not thin[i] or seen[i]:
            continue
        stack, seen[i] = [i], True
        count, widest = 0, 0.0
        while stack:
            j = stack.pop()
            count += 1
            widest = max(widest, d[j])
            r, c = divmod(j, n)
            for k, ok in ((j-1, c > 0), (j+1, c < n-1), (j-n, r > 0), (j+n, r < n-1)):
                if ok and thin[k] and not seen[k]:
                    seen[k] = True
                    stack.append(k)
        if count >= total * min_area:
            feats.append((2 * math.sqrt(widest) * mm_per_px, count))
    feats.sort()
    if show:
        print(f"  {show}: " + ", ".join(f"{w:.2f} mm ({c} px)" for w, c in feats[:6]))
    return feats[0][0]


# ------------------------------------------------------------------------ main
def main():
    svg = open(SRC).read()
    m = re.search(r'id="%s"[^>]*?\sd="([^"]*)"' % PATH_ID, svg, re.S)
    subs = flatten(m.group(1), FLAT_TOL)
    assert len(subs) == 4, f"expected 4 subpaths, got {len(subs)}"

    cx, cy, r = fit_circle(subs[0])
    dev = max(abs(math.hypot(x - cx, y - cy) - r) for x, y in subs[0])
    assert dev < 0.5, f"subpath 0 is not a circle: {dev:.3f} off"

    s = NOMINAL_DIA / (2 * r)                 # artwork units -> mm at nominal
    rings = []
    for i, p in enumerate(subs):
        if i == 0:                            # exact circle for the boundary
            n = 720
            q = [(NOMINAL_DIA/2 * math.cos(2*math.pi*k/n),
                  NOMINAL_DIA/2 * math.sin(2*math.pi*k/n)) for k in range(n)]
        else:                                 # y flips: SVG is y down, we are y up
            q = simplify([((x - cx)*s, -(y - cy)*s) for x, y in p], SIMPLIFY)
        if (area(q) > 0) != (i == 0):         # boundary CCW, holes CW
            q.reverse()
        rings.append([(round(x, 3), round(y, 3)) for x, y in q])

    half = NOMINAL_DIA/2 * 1.02
    mm_per_px = 2*half/RASTER
    mask = raster(rings, RASTER, half)
    metal = [bool(v) for v in mask]
    hole = [not v for v in metal]
    mm = min_width(metal, RASTER, mm_per_px, show="thinnest metal")
    ms = min_width(hole, RASTER, mm_per_px, show="narrowest slots")
    print(f"at {NOMINAL_DIA:.0f} mm disc: narrowest metal {mm:.2f} mm, "
          f"narrowest slot {ms:.2f} mm")
    print("points per ring:", [len(r) for r in rings])

    with open(OUT, "w") as f:
        f.write(HEADER.format(dia=NOMINAL_DIA, metal=mm, slot=ms,
                              tol=SIMPLIFY, n=sum(len(r) for r in rings)))
        f.write("HUNAB_KU = {\n")
        f.write(f'    "nominal_dia": {NOMINAL_DIA:.1f},\n')
        f.write(f'    "min_metal": {mm:.2f},\n')
        f.write(f'    "min_slot": {ms:.2f},\n')
        f.write('    "rings": [\n')
        for ring in rings:
            f.write("        [" + ", ".join(f"({x:.3f},{y:.3f})" for x, y in ring)
                    + "],\n")
        f.write("    ],\n}\n")
    print("wrote", OUT)


HEADER = '''"""Hunab Ku outline, frozen for the panel generator. GENERATED - do not edit.

Regenerate with trace_hunabku.py, which explains every step. Source artwork is
hunab_ku_source.svg, public domain, from Wikimedia Commons.

Coordinates are mm at a {dia:.0f} mm disc diameter, origin at the disc centre,
y UP. Scale linearly for any other diameter. rings[0] is the part boundary (a
true circle); rings[1:] are the holes - the white areas of the symbol. Curves
are flattened and simplified to {tol} mm at that nominal size, {n} points total.

At {dia:.0f} mm the narrowest metal is {metal:.2f} mm and the narrowest slot is
{slot:.2f} mm, both in the eight antennae. Those two numbers scale with the
diameter and are what decides whether a given size can be cut at all.
"""

'''


if __name__ == "__main__":
    main()
