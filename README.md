# ASUS ROG GT502 — custom aluminium front panel with two touchscreens

A 3 mm aluminium replacement front panel for the ASUS ROG GT502, with two
windows for Waveshare touchscreens bonded from behind with 3M VHB tape. Cutting
the metal away (rather than mounting the screens outside it) is what leaves the
touch surface exposed and usable.

## Files

| File | What it is |
| --- | --- |
| `GT502_front_panel_194x384_both_screens.dxf` | **Everything to be cut.** The panel plus the 4 back stiffener strips, nested on one sheet as a single cutting job. Send this to the laser cutter. |
| `CUTTING_SPEC.txt` | Vendor sheet: material, tolerance, kerf, finish, every coordinate. Send with the DXF. |
| `GT502_front_panel_194x384_both_screens_PRINT_1to1.svg` | True-scale check print. See "Before you order". |
| `GT502_front_panel_194x384_both_screens.svg` | Screen preview, with screen glass and active areas shown as reference. |
| `generate_panel_dxf.py` | Generates all four of the above from the constants at the top. Single source of truth. |
| `FrontAluminiumPanel.txt` | Measured outer size of the panel. |
| `Waveshare-11inch.png`, `Waveshare-6.25inch.png` | Manufacturer dimension drawings the screen numbers come from. |

Do not hand-edit the DXF or the spec — change a constant in the script and
re-run it, so the drawing, the print sheet and the spec can never disagree.

## The part

Sheet is **194.00 W × 384.00 H**, 3 mm aluminium, 3.0 mm corner radius.
Origin for all coordinates is the **lower-left corner**, X right, Y up.

| Feature | Size | Position (lower-left) |
| --- | --- | --- |
| Upper window — 6.25″, landscape | 147.18 × 68.70, R2 | X 26.41, Y 287.49 |
| Lower window — 11″, portrait | 153.22 × 241.67, R2 | X 23.39, Y 27.81 |
| Mounting holes, 4 off | Ø3.20 through | see below |

The DXF also carries 7 back stiffener pieces nested **inside** the 11″ window —
see "Back stiffener layer". Sheet extent stays **194 × 384**, so those pieces
cost no extra material. One job, one sheet, 8 parts delivered.

Aluminium between the two windows: **18.00 mm**. Both windows sit **3.00 mm
right of the sheet centreline** — this is deliberate, from test-fitting the
first cut sheet. Left and right margins are *not* equal; work to coordinates.

### Mounting holes

| Hole | X, Y | As measured |
| --- | --- | --- |
| top left | 63.00, 371.00 | 63 from left, 13 from top |
| top right | 134.00, 371.00 | 60 from right, 13 from top |
| bottom left | 30.00, 16.00 | 30 from left, 16 from bottom |
| bottom right | 164.00, 16.00 | 30 from right, 16 from bottom |

All to hole **centre**. Not a symmetric pattern: the top pair is 71.00 apart and
1.5 mm off-centre, the bottom pair 134.00 apart and centred. These came off the
case, so they are correct as given rather than tidy.

> **Open item — hole diameter is an assumption.** Ø3.20 is M3 clearance,
> chosen because no fastener was specified. Confirm before cutting; holes are
> the one feature you cannot correct afterwards. Change `HOLE_DIA` if wrong.

## Screens

Numbers taken from the Waveshare drawings in this folder.

| | Glass (outer) | Active area | Bezel |
| --- | --- | --- | --- |
| 11″, portrait | 165.22 × 253.67 | 148.02 × 236.47 | 8.60 all round |
| 6.25″, landscape | 159.18 × 74.70 | 144.18 × 66.60 | 7.50 sides, 4.05 top/bottom |

Each window is smaller than the glass but larger than the active area, so the
metal overlaps the black bezel and no pixels are clipped.

### VHB tape land

The overlap between metal and bezel is the only place tape can go:

| | Land available |
| --- | --- |
| 11″ | 6.0 mm all four edges |
| 6.25″ | 6.0 mm sides, 3.0 mm top and bottom |

**12 mm VHB will not fit anywhere.** The widest bezel on either screen is
8.60 mm, and the 6.25″ has only 4.05 mm top and bottom — this is a limit of the
screens, not of the drawing. Slit 12 mm tape lengthwise into 6 mm strips, or
buy a 6 mm roll (3M 5952 and GPH both come in 6 mm). Never let tape overhang
into a window: the grey foam shows through the glass.

The 6.0 mm land also leaves 2.60 mm of visible black border around the 11″
image (1.50 / 1.05 mm on the 6.25″). That border is your placement tolerance —
VHB gives you exactly one attempt, so it is margin worth keeping.

## Back stiffener layer

A second 3 mm layer bonded to the **back** of the panel to stiffen it. **7
separate pieces**, all nested inside the 11″ window opening — that slug is
scrap anyway, so they use no extra sheet and the total extent stays 194 × 384.
None of it is visible in the finished build.

| Piece | Bounding size | Bonds at | Shape | Holes |
| --- | --- | --- | --- | --- |
| left strip A | 17.00 × 192.00 | X 0, Y 0 | rect, R3 bottom-left | — |
| left strip B | 20.00 × 192.00 | X 0, Y 192 | **stepped** 17→20, R3 top-left | — |
| right strip A | 11.00 × 192.00 | X 183, Y 0 | rect, R3 bottom-right | — |
| right strip B | 14.00 × 192.00 | X 180, Y 192 | **stepped** 11→14, R3 top-right | — |
| top strip | 160.00 × 24.50 | X 20, Y 359.50 | rect | 2 |
| bottom strip | 166.00 × 21.50 | X 17, Y 0 | rect | 2 |
| mid bar | 160.00 × 8.50 | X 20, Y 275.74 | rect | — |

Three details that are easy to lose, and all three are in the cutting spec:

- **The side pieces each carry one R3 corner** — the one that lands at a panel
  corner. That lets them run the panel's full 384 mm (2 × 192) instead of
  stopping at the corner arc tangents, which cost 6 mm per side.
- **The two upper side pieces are stepped, not rectangular.** They are 17/11 mm
  wide alongside the 11″ glass and widen to 20/14 mm above it. See below.
- **The three horizontals are drawn rotated 90°** from how they are fitted, to
  nest inside the window. Their holes rotate with them.

### Why the side pieces step

The 6.25″ glass is 159.18 wide against the 11″'s 165.22, so it sits 3.02 mm
inboard on each side. A full-height rectangular rail has to be sized for the
wider screen, which leaves a 3.41 mm gap beside the top screen. Stepping the
rail above the 11″ glass closes that to **0.41 mm** without adding pieces or
butt joints. The step sits at Y 275.74 — the top of the 11″ glass plus 0.25 mm
of air, the same line the mid bar sits on.

### Clearances — all four edges run tight

Widths are capped from the live glass positions, not chosen freely: the screens
bond to the panel's own cutouts, so a piece reaching under the glass would sit
that screen on a 3 mm step and tilt it.

| Edge | Free margin | Cut at | Clearance |
| --- | --- | --- | --- |
| left, lower | 17.39 | 17.00 | 0.39 |
| left, upper | 20.41 | 20.00 | 0.41 |
| right, lower | 11.39 | 11.00 | 0.39 |
| right, upper | 14.41 | 14.00 | 0.41 |
| top | 24.81 | 24.50 | 0.31 |
| bottom | 21.81 | 21.50 | 0.31 |
| mid bar | 9.00 gap | 8.50 | 0.25 each side |

**Everything hangs off where the 11″ screen ends up.** Six of those clearances
are under 0.5 mm, and they are all measured from that screen's glass. Bond the
11″ first, measure the actual gaps, then fit the pieces — they are plain
stock you can file, the screen is not.

### The mid bar

Sits in the 9.00 mm gap between the two screens, 8.50 wide with 0.25 mm of air
each side. Its job is to give the 6.25″ screen a bottom edge to sit down onto —
nothing else locates that screen vertically, since it is a small screen in a
large window with only 3 mm of bezel overlap top and bottom. With the 24.50 mm
top strip above it, the 6.25″ glass is captured in a 75.265 mm slot for a
74.700 mm glass: **0.565 mm total slack**.

Fit order matters: **mid bar before the 6.25″ screen**, or it is no use as a
datum. Full sequence — 11″ screen, mid bar, 6.25″ screen, then the perimeter
pieces.

### Holes in the pieces

Top and bottom strips carry matching Ø3.20 holes so one screw passes through
both layers. Offsets are from each piece's own lower-left corner **as drawn**:

| Piece | Holes | Pitch |
| --- | --- | --- |
| top strip | (13.00, 43.00) and (13.00, 114.00) | 71.00 |
| bottom strip | (5.50, 13.00) and (5.50, 147.00) | 134.00 |

Those pitches match the panel's top and bottom hole pitches exactly. The four
side pieces have no holes.

### Nest

The 7 pieces occupy 140.50 of the 143.22 mm available across the window, with
4 mm between pieces and a 5 mm margin to the window edge. **That is full** —
there is no room for another piece or another width increase without starting a
second row. The ~63 mm of unused height above the shorter pieces is the only
spare space left.

The spec tells the cutter to **cut all 7 pieces before the window outline that
surrounds them** — once that contour is cut, the slug they sit in drops away.

## Before you order

1. Print `..._PRINT_1to1.svg` at **100% / actual size** — no fit-to-page. It is
   194 × 384, so use **A3**. Check the scale bar reads 100 mm, then lay the real
   screens and the cut sheet on it.
2. Confirm the hole diameter (above).
3. Check depth clearance: the 11″ is ~12 mm deep with its connectors.

## Assembly notes

Everything bonds to the **back** face, which must be flat and deburred. The
order matters, because several pieces are datums for the ones after them and
six clearances are under 0.5 mm.

1. **Fit the two bottom screws first.** Those holes sit 4.21 mm from the 11″
   glass edge; an M3 head (~6 mm OD) leaves 2.82 mm and a washer (~7 mm) 2.32.
   It fits, but not with a screwdriver in the way once the screen is on.
   Anything with a flange over ~11 mm OD will touch the glass.
2. **Bond the 11″ screen**, centred in its window. Everything else is measured
   from it. VHB gives you one attempt.
3. **Measure the real gaps** left and right before any side piece goes on. You
   need ≥ 17.4 mm left and ≥ 11.4 mm right against the lower rails, and
   ≥ 20.4 / ≥ 14.4 above the step. If a gap is short, file the inner edge of
   that piece — the pieces are plain stock, the screen is not.
4. **Fit the mid bar**, seated against the 11″ glass top edge.
5. **Set the 6.25″ screen down onto the mid bar.** That bar is the only thing
   locating it vertically.
6. **Fit the remaining pieces** — side rails, top strip, bottom strip.

Other notes:

- Glass-to-glass air gap between the two screens is 9.00 mm; the mid bar takes
  8.50 of it.
- Clean the bezel with IPA before taping. VHB reaches full strength over ~72 h.
- **12 mm VHB will not fit anywhere** — see "VHB tape land". Slit it to 6 mm.
- The bottom strip leaves a 3.90 mm web above each of its holes. Fine, but
  don't overtighten there.

## Regenerating

```sh
python3 generate_panel_dxf.py
```

No dependencies beyond the standard library. It prints every dimension and
clearance it used. Constants worth knowing, all near the top of the script:

| Constant | Meaning |
| --- | --- |
| `PANEL_W`, `PANEL_H` | Sheet outer size |
| `CUT_GAP` | Nominal metal between the two windows |
| `INS_11`, `INS_625` | Per-edge bezel overlap (= the VHB land) |
| `WIN_DX`, `WIN_11_DY`, `WIN_625_DY` | Fit corrections applied to the windows |
| `MOUNT_HOLES`, `HOLE_DIA` | Hole table and diameter |
| `BORDER_REQ`, `BORDER_CLEAR` | Back stiffener widths and per-edge glass clearance |
| `BORDER_MID_BAR`, `BORDER_MID_CLEAR` | The bar between the two screens |
| `BORDER_SIDE_PIECES` | How many pieces each side rail splits into |
| `BORDER_NEST_GAP`, `BORDER_WIN_MARGIN` | Spacing of the nested pieces |
| `WORD` | Set to a string to also emit a variant with text cut into the top band |

The script asserts rather than trusting the numbers: no window may clip an
active area, glass may not overhang any edge, the two screens may not collide
behind the panel, every hole must clear both windows and all four edges, no
stiffener piece may overlap a glass footprint (checked against each piece's real
sub-rectangles, not its bounding box, so a step is not a false positive), every
hole must land in exactly one piece, every nested piece must sit inside the
window with margin, and no piece may overlap the panel or another piece. A bad
edit fails loudly instead of producing an uncuttable part.

### Optional cut-through lettering

Setting `WORD` (e.g. `"URANTIA TECH"`) pushes the screens down and cuts text
into the band above the top screen. Glyphs for `A C E H I N P R T U` are built
in as squared monoline caps.

`A`, `P` and `R` are **stencil** letters: each has a fixed-width gap in one bar
tying the middle of the letter to the surrounding metal. Without it the centre
of the letter is an island with nothing holding it, and it drops out of the
sheet during cutting. Do not close those gaps, and tell the vendor not to
substitute a normal font.

## Revision history

- **v1** — cut and test-fitted. Windows were centred on the width; mounting
  holes were a symmetric 28/10 pattern.
- **v2 (current)** — corrections measured off the v1 sheet: both windows moved
  3 right; 11″ window 3 down; 6.25″ window 3 up; all four holes repositioned.
  Window-to-window metal went from 12.00 to 18.00 as a direct consequence of
  moving the two screens apart.
- **v3** — added the back stiffener layer as 4 strips nested beside the panel.
- **v4 (current)** — stiffener reworked to 7 pieces nested *inside* the 11″
  window, so it costs no extra sheet. Side rails split in two and given the
  panel's R3 corner so they run full height; the upper pair stepped to close the
  gap beside the 6.25″ screen from 3.41 to 0.41. Added the mid bar. Top strip
  widened to 24.50 and bottom to 21.50 so both screens are captured. All cut
  geometry unified to one colour on two kerf-side layers.
