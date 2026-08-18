# ASUS ROG GT502 — custom aluminium front panel with two touchscreens

A 3 mm aluminium replacement front panel for the ASUS ROG GT502, with two
windows for Waveshare touchscreens bonded from behind with 3M VHB tape. Cutting
the metal away (rather than mounting the screens outside it) is what leaves the
touch surface exposed and usable.

## Files

| File | What it is |
| --- | --- |
| `GT502_front_panel_194x384_both_screens.dxf` | **The part.** Send this to the laser cutter. |
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

## Before you order

1. Print `..._PRINT_1to1.svg` at **100% / actual size** — no fit-to-page. It is
   194 × 384, so use **A3**. Check the scale bar reads 100 mm, then lay the real
   screens and the cut sheet on it.
2. Confirm the hole diameter (above).
3. Check depth clearance: the 11″ is ~12 mm deep with its connectors.

## Assembly notes

- Screens bond to the **back** face. It must be flat and deburred.
- Fit the two bottom screws **before** bonding the 11″ screen. Those holes sit
  4.21 mm from the 11″ glass edge; an M3 head (~6 mm OD) leaves 2.82 mm and a
  washer (~7 mm) 2.32 mm. It fits, but not with a screwdriver in the way.
  Anything with a flange over ~11 mm OD will touch the glass.
- Glass-to-glass air gap between the two screens is 9.00 mm.
- Clean the bezel with IPA before taping. VHB reaches full strength over ~72 h.

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
| `WORD` | Set to a string to also emit a variant with text cut into the top band |

The script asserts rather than trusting the numbers: no window may clip an
active area, glass may not overhang any edge, the two screens may not collide
behind the panel, and every hole must clear both windows and all four edges. A
bad edit fails loudly instead of producing an uncuttable part.

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
