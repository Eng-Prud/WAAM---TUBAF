# Conic Discriminant Fit — Weld Bead Profile Classifier

A small interactive Python script that takes measured weld bead profile
points (x, y coordinates) and determines whether the bead's cross-section
shape is a **parabola**, **circle**, **ellipse/circular arc**, or
**hyperbola** — using a mathematically rigorous curve-fitting method
rather than a visual guess.

---

## 1. What problem this solves

When validating a weld bead's mathematical model (e.g. in WAAM — Wire Arc
Additive Manufacturing), it's common to visually compare the bead's
measured profile against known curve shapes (parabola, arc, cosine, etc.)
to see which one it resembles. That approach is subjective — a parabola
and a shallow circular arc can look nearly identical over a short bead
width.

This script instead fits the **general conic equation** directly to your
measured data and computes a single number (the **discriminant**) that
mathematically classifies the curve — no visual judgment required.

---

## 2. The math behind it

### 2.1 The general conic equation

Every parabola, circle, ellipse, and hyperbola can be written using one
equation:

```
A*x^2 + B*x*y + C*y^2 + D*x + E*y + F = 0
```

`A` through `F` are coefficients that define the specific shape. Given a
set of measured (x, y) points, the script solves for these coefficients
using **least-squares fitting** — the same principle used to draw a
"best-fit line" through scattered data, just extended from 2 unknowns
(slope, intercept) to 6 unknowns (A–F).

### 2.2 Removing the scaling ambiguity

If every coefficient (A–F) is multiplied by the same constant, the
equation still describes the same curve — so there are infinitely many
equally valid solutions unless one coefficient is fixed. This script
fixes **F = −1** and rearranges the equation to:

```
A*x^2 + B*x*y + C*y^2 + D*x + E*y = 1
```

This turns the problem into a standard linear least-squares system,
solvable in one step with `numpy.linalg.lstsq`.

### 2.3 The discriminant

Once A, B, and C are known, the script computes:

```
discriminant = B^2 - 4*A*C
```

This single number classifies the curve. In exact theoretical math (no
measurement noise), the classification is clean and unambiguous:

| Δ value (exact) | Curve type |
|---|---|
| Δ = 0 | Parabola |
| Δ < 0, A = C and B = 0 | Circle |
| Δ < 0, A ≠ C | Ellipse / circular arc segment |
| Δ > 0 | Hyperbola |

A true parabola always has Δ = **exactly** 0 — no exceptions. A true
circle always has Δ = **−4A²** (substituting A = C, B = 0 into
B² − 4AC), which since A² is always positive, means a real circle's
discriminant is always **strictly negative**, never exactly zero. In
theory, there is no overlap between the two.

**Why the code doesn't check it that simply.** Real measured data is
never perfectly clean, so the fitted discriminant is essentially never
*exactly* 0 or exactly anything — it comes out as some small number
close to a target value, and the code has to use a tolerance ("close
enough to zero, given expected noise") instead of exact equality. This
creates a practical trap: for a **circle with a large radius** (i.e. a
small A), the discriminant −4A² can come out numerically very close to
zero too — not because it's secretly a parabola, but simply because A
itself is small. This is exactly what happens with a shallow, wide
weld bead arc: A ≈ 0.0278 gives Δ ≈ −0.0031, which is small enough
that checking "is Δ close to 0?" first, on its own, would wrongly
classify it as a parabola.

The fix is a **checking order**, not a change to the math itself:

| Order | Condition checked | Curve type |
|---|---|---|
| 1st | `A ≈ C` and `B ≈ 0` | Circle |
| 2nd (only if not a circle) | discriminant ≈ 0 | Parabola |
| 3rd | discriminant < 0 | Ellipse / circular arc segment |
| 4th | discriminant > 0 | Hyperbola (not physically expected for a weld bead) |

By checking the circle condition (`A ≈ C`, `B ≈ 0`) *before* the
near-zero discriminant check, a large-radius circle is correctly
identified as a circle regardless of how small its discriminant
happens to be — instead of being misclassified as a parabola.

### 2.4 Fit quality check

Since the right-hand side of the equation is fixed at 1 for every point,
there's no natural "variance" for a standard R² score. Instead, the
script reports how close the left-hand side of the equation
(`A*x^2 + B*x*y + C*y^2 + D*x + E*y`) lands to 1 at each of your input
points, and the RMSE (root-mean-square error) of that deviation across
all points. Smaller RMSE means a tighter, more trustworthy fit.

---

## 3. Requirements

- Python 3.8 or later
- [NumPy](https://numpy.org/)

Install NumPy if you don't already have it:

```
python -m pip install numpy
```

---

## 4. How to run it

From a terminal in the folder containing the script:

```
python Conic_Fit.py
```

(On some systems you may need `python3` or `py` instead of `python`.)

### 4.1 What it asks you, step by step

1. **"How many (x, y) points do you have?"**
   Enter a whole number. The script requires **at least 5 points**,
   since there are 5 unknown coefficients (A–E) to solve for. More
   points (10+) are recommended for a more noise-resistant fit.

2. **"Point 1 -- enter as 'x, y'"** (repeated for each point)
   Type the x and y value for each measured point, separated by a
   comma or space, e.g.:
   ```
   -5.651, 2.016
   ```
   x = position across the bead width, y = bead height above the
   substrate (or whatever units your measurement method uses — the
   script is unit-agnostic, just be consistent).

3. **"Classification tolerance"**
   Controls how strict the parabola/circle/ellipse cutoff is, as a
   relative tolerance (default `0.05`). Press Enter to accept the
   default, or type your own value if your measurements are especially
   noisy (use a looser tolerance) or especially precise (use a
   tighter tolerance).

### 4.2 What it prints back

- The fitted conic coefficients (A–F)
- The discriminant value
- The classified curve type (Circle / Parabola / Ellipse-arc / Hyperbola)
- A per-point fit check showing how close each point comes to
  satisfying the fitted equation
- The overall RMSE of that fit — the key number to judge how trustworthy
  the classification is

---

## 5. Example

```
How many (x, y) points do you have? 7
Point 1 -- enter as 'x, y': -5.651, 2.016
Point 2 -- enter as 'x, y': 5.655, 2.006
Point 3 -- enter as 'x, y': 0, 6
Point 4 -- enter as 'x, y': -4.454, 4.020
Point 5 -- enter as 'x, y': 4.462, 4.012
Point 6 -- enter as 'x, y': -2.314, 5.536
Point 7 -- enter as 'x, y': 2.365, 5.514

Classification tolerance ... Press Enter to use default (0.05):

------------------------------------------------------------
Fitted conic coefficients:
  A = 0.027781
  B = 0.000004
  C = 0.027794
  D = -0.000024
  E = -0.000095
  F = -1.000000  (fixed)

Discriminant (B^2 - 4AC) = -0.003089

--> Classified curve type: Circle

RMSE of deviation from 1.0: 0.000052
(Smaller RMSE means the conic equation fits your points more tightly.)
------------------------------------------------------------
```

This tight RMSE (0.00005) confirms the 7 points genuinely trace a
circular arc.

---

## 6. Code structure

| Function | Purpose |
|---|---|
| `get_number_of_points()` | Prompts for and validates the number of points (≥ 5 required) |
| `get_points(n)` | Prompts for each (x, y) pair, one at a time, with input validation |
| `get_tolerance()` | Prompts for the classification tolerance, with a default fallback |
| `fit_conic(x_data, y_data)` | Builds the least-squares matrix and solves for coefficients A–E |
| `classify_curve(A, B, C, discriminant, tolerance_rel)` | Applies the discriminant logic to classify the curve type |
| `main()` | Orchestrates the full flow: prompts → fit → classify → report |

---

## 7. Limitations / things to keep in mind

- **Minimum 5 points are required** to solve the system at all; with
  exactly 5 the fit has zero "slack" to average out measurement noise
  (it will pass through every point exactly). 10+ points is
  recommended for a fit that meaningfully separates real curve shape
  from measurement scatter.
- This script only distinguishes between the **conic family**
  (parabola, circle, ellipse/arc, hyperbola). It does **not** test for
  cosine curves or splines — those require separate methods (Taylor
  series matching for cosine vs. parabola; polynomial-order testing
  and piecewise fitting for splines).
- The tolerance setting is a judgment call — tighter tolerances reduce
  false positives (e.g. calling something a "circle" when it's really
  a slightly eccentric ellipse) but may also fail to classify noisy
  real-world data at all. If your points are scattered from
  measurement noise, consider averaging repeated measurements at each
  x-position before running the fit.
