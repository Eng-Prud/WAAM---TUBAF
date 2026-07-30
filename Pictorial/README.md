# WAAM Bead Overlap Simulator ("Pictorial")

An interactive tool for visualizing how multiple weld beads overlap
side-by-side on a flat substrate, and for quantifying the resulting
surface quality — waviness, overlap area, valley area, and gap
detection — for any bead cross-section shape, including your exact
fitted equation from the [Conic discriminant](../Conic%20discriminant/)
tool.

---

## 1. What this tool does

Given a single bead's cross-sectional shape, this tool answers:

> If I place several of these beads side-by-side at a given
> center-to-center spacing, what does the combined surface look like,
> and how smooth or gappy is it?

It supports two ways of defining a bead:

- **Preset shape** — pick parabola, circle, or ellipse, and enter just
  the width and peak height.
- **Raw fitted equation** — enter the exact conic coefficients (A–F)
  produced by `Conic_Fit.py`, so the overlap is computed on your *actual*
  measured bead shape rather than an idealized approximation.

---

## 2. Files

| File | Purpose |
|---|---|
| `bead_overlap.py` | Core math module — no interface, just functions. Can also be run directly for a simple interactive text-based test of the height function alone. |
| `app.py` | The interactive Streamlit app — sliders, live plot, and metrics. This is the main way to use the tool. |

Both files must be in the same folder, since `app.py` imports from
`bead_overlap.py`.

---

## 3. Requirements

- Python 3.8+
- NumPy
- Matplotlib
- Streamlit

Install what's missing:
```
python -m pip install numpy matplotlib streamlit
```

---

## 4. How to run it

```
streamlit run app.py
```
(If `streamlit` isn't recognized as a command, use `python -m streamlit run app.py` instead.)

This opens the app in your browser. From there:

1. **Define the bead shape** — preset or raw equation.
2. **Place the beads** — set how many beads and the spacing between them with sliders.
3. **View the result** — a live plot of the combined surface, plus metrics below it.

---

## 5. The math, explained

### 5.1 Height at a single point (`height_at_preset`, `height_at_equation`)

Every bead, regardless of how it's defined, boils down to one question
asked repeatedly: **"how tall is the bead at this particular x-position?"**

- For **preset shapes**, this is a direct one-step formula (e.g. a
  parabola: `y = H·(1 − (x/half-width)²)`).
- For a **raw fitted equation** (`A·x² + B·xy + C·y² + D·x + E·y = 1`),
  y is tangled up with itself, so the equation is rearranged into a
  quadratic in y and solved with the quadratic formula at each x. Since
  a quadratic always has two solutions (top and bottom of the curve),
  the **upper branch** (the larger root) is used, since a bead only has
  a visible top surface.

Both approaches return `None` wherever a given x falls outside the
bead's footprint (no material there).

### 5.2 Placing multiple beads (`build_bead_centers`, `envelope_height`, `compute_envelope`)

Beads are placed at evenly spaced center positions. At every x-position
across the whole span, the combined surface height is simply **the
tallest bead present at that x** — the same logic as "of everyone
standing at this spot, who's tallest?"

### 5.3 Waviness (`compute_gap_metrics`)

For each pair of adjacent beads:
- **Peak** = the bead height at its highest point in that region
- **Valley** = the lowest point of the combined surface between the two beads
- **Waviness** = Peak − Valley

Waviness measures how much the surface dips between beads, relative to
how tall the beads are.

### 5.4 Area metrics (`compute_gap_metrics`, `compute_single_bead_area`)

- **Overlap area** — the cross-sectional area where two adjacent beads'
  material physically coincides, integrated across the *entire* region
  where both beads are actually present (not just the strip between
  their centers — at tight spacing, real overlap extends well beyond
  both centers in each direction, so the full region must be measured).
- **Valley area** — the area of the dip relative to the peak height:
  how much material would be needed to fill the valley flat, up to
  peak level. This is a fuller picture than the single-point "valley"
  number, since it accounts for the whole shape of the dip.
- **Overlap percentage** — overlap area expressed as a percentage of
  a single bead's own cross-sectional area, for an intuitive
  "beads are sharing X% of their material" figure.
- **Gap detection** — flags when the valley touches or drops below
  y = 0, meaning bare, uncovered substrate would be exposed between
  beads at that spacing.

All areas are computed by numerical integration (the trapezoidal
rule), which works identically regardless of whether the bead came
from a preset formula or a raw fitted equation.

### 5.5 Equal-area optimal spacing (`find_equal_area_spacing`)

This function numerically searches for the spacing at which
**overlap area equals valley area** — a materials-balance criterion
from the WAAM literature, verified against a published closed-form
result for parabolic beads (`p = (2/3)·width`), which the solver
reproduces to four decimal places.

**Important — what this criterion does and does not mean:**

This is *not* a "make the surface flat" calculation. All calculations
in this tool — including this one — treat beads as solid, already-
hardened shapes stacked next to each other, with no material movement
modeled at all. The equal-area spacing simply confirms that the
*amount* of spare material sitting in the overlap zones mathematically
matches the *amount* missing in the valley, at that specific spacing.

In practice, real WAAM deposition involves briefly molten metal that
*can* flow and redistribute somewhat before solidifying — so this
spacing is used in the literature as a physically-informed **starting
point** for real trials, on the reasoning that if the weld pool flows
even a little, the real result should end up flatter than the raw
static picture this tool draws. It is not a guarantee of flatness, and
this tool does not simulate any flow, melting, or material
redistribution — it only shows the "nothing has moved yet" geometric
envelope.

---

## 6. Interpreting the app's output

- **The solid filled curve** is the actual combined surface, assuming
  no material movement (the honest, conservative picture).
- **The dashed reference line** in each gap shows the peak height held
  flat across that gap — a visual reference for what "fully flowed and
  leveled" would look like. The visible gap between the solid curve and
  the dashed line *is* the valley area, made visible.
- **Worst-case waviness** is the single largest dip across all gaps
  between beads, not an average — since the roughest point on the
  surface matters more than the typical one.
- **A red gap warning** means the current spacing is wide enough that
  bare substrate would be exposed between beads — a genuine coverage
  defect, not just a smoothness issue.

---

## 8. Example: testing with a real digitized bead

This walks through using the tool with an actual fitted bead equation,
rather than an idealized preset shape.

### 8.1 The real bead used in this example

Seven points were digitized from a real CuSn WAAM bead cross-section
and fitted using `Conic_Fit.py`, which classified it as a **circle**
with these coefficients:

| Coefficient | Value |
|---|---|
| A | 0.027781 |
| B | 0.000004 |
| C | 0.027794 |
| D | −0.000024 |
| E | −0.000095 |
| F | −1.000000 (fixed) |

The bead's real peak height was 6.0 mm, with edges around 2.0 mm, over
a total width of about 11.3 mm.

### 8.2 Running the app with this data

1. Start the app:
   ```
   streamlit run app.py
   ```
2. Under **"1. Define the bead shape"**, select **Raw fitted equation**.
3. Enter the coefficients above into the A–E input boxes exactly as
   shown (these are also the app's default values, so they may
   already be filled in).
4. Under **"2. Place the beads"**, set the number of beads (e.g. 4)
   and adjust the spacing slider.

### 8.3 What to expect

- At **x = 0**, the height should read exactly **6.0000** (the bead's
  measured peak).
- At **x = 5.651** (close to the bead's real measured edge), the
  height should be close to **2.0** — matching the original digitized
  point.
- The **suggested equal-area spacing** box should show a value
  specific to this exact bead shape (not the same number a generic
  circle preset of the same width/height would give, since the real
  fitted equation captures the bead's actual — very slightly
  asymmetric — shape).

### 8.4 Comparing against an idealized preset

To see how much the idealized preset shapes differ from this real
bead, switch to **Preset shape**, select **ellipse**, and enter
width = 11.3, height = 6.0 (matched to the same overall size). Compare
the height at a few x-positions between the two modes — they will
match closely near the center (x = 0) but diverge increasingly toward
the edges, since the preset assumes perfect symmetry while the real
bead does not.

---

## 9. Limitations

- **Single layer, side-by-side only.** Multi-layer stacking (a new
  bead deposited on top of an already-wavy previous layer, rather than
  a flat substrate) is not modeled.
- **No material flow, melting, or redistribution is simulated.**
  Every number in this tool describes the static, as-placed geometry.
- **All beads in a placement are assumed identical**, matching the
  assumption that they'd be welded with the same process parameters.
- **The equal-area spacing is a starting point, not a flatness
  guarantee** — see Section 5.5.
- For the raw-equation mode, the plotting width is a rough guess (used
  only to decide how far to draw the plot), since the exact footprint
  isn't directly available from A–F alone the way it is for preset
  shapes.

---

## 10. Changelog

**Fixed: overlap area under-counted at tight spacing.**
`compute_gap_metrics` originally integrated overlap area only across
the strip between the two bead centers (`x` from `c1` to `c2`). At
tight spacing, most of the real overlapping material sits *outside*
that narrow strip — each bead's footprint extends well past its own
center toward its neighbor — so overlap area was being significantly
under-counted the closer beads were placed together. This produced a
counter-intuitive result where tighter spacing showed a *smaller*
overlap percentage than wider spacing.

The fix integrates overlap area across the full region where both
beads are actually present, using a wide integration window (safe
regardless of bead shape, since height outside a bead's real footprint
is always 0). Overlap percentage now decreases smoothly and
monotonically as spacing increases, as physically expected. This was
re-verified against the parabola case's known analytic equal-area
spacing (`p = (2/3)·width`), which still matches to four decimal
places after the fix — confirming the correction didn't disturb the
values that were already validated.

Peak, valley, waviness, and valley area were unaffected by this bug —
they were already correctly restricted to the between-centers window,
which is the right region for measuring the dip itself.