"""
Bead Overlap Simulator - Core Math Module (Interactive)
----------------------------------------------------------
Defines a single bead's height at any x-position, using either:
  (a) a preset shape (parabola / circle / ellipse) with width + height, or
  (b) the exact fitted conic equation coefficients (A-F) from Conic_Fit.py,
      which works for ANY conic curve regardless of its classification.

Run this file directly to interactively test it -- no code editing needed.
"""

import numpy as np

# numpy 2.0+ renamed trapz to trapezoid; support both so this runs on
# whichever numpy version is installed.
_trapz = getattr(np, "trapezoid", None) or np.trapz


# ------------------------------------------------------------------
# (a) Preset shapes -- direct formula, one step from x to y
# ------------------------------------------------------------------
def height_at_preset(x, width, height, shape="parabola"):
    """Return the bead's height at position x, for a simple preset shape."""
    half_width = width / 2.0

    if abs(x) > half_width:
        return None  # outside the bead's footprint

    if shape == "parabola":
        return height * (1 - (x / half_width) ** 2)

    elif shape == "circle":
        # A circular arc can never be taller than half its own width --
        # the tallest possible circular cap over a given width is a
        # semicircle, whose height equals exactly half the width.
        if height > half_width:
            raise ValueError(
                f"Impossible circle: height ({height}) exceeds half-width "
                f"({half_width}). Use an ellipse instead, which allows "
                f"width and height to be set independently."
            )
        R = (half_width ** 2 + height ** 2) / (2 * height)
        center_y = height - R
        value_under_root = R ** 2 - x ** 2
        if value_under_root < 0:
            return None
        return np.sqrt(value_under_root) + center_y

    elif shape == "ellipse":
        # Unlike the circle, an ellipse's width and height are fully
        # independent -- no height/width restriction applies.
        value_under_root = 1 - (x / half_width) ** 2
        if value_under_root < 0:
            return None
        return height * np.sqrt(value_under_root)

    else:
        raise ValueError(f"Unknown shape: {shape}")


# ------------------------------------------------------------------
# (b) Raw fitted equation -- any conic, classified or not
#     A*x^2 + B*x*y + C*y^2 + D*x + E*y = 1   (F fixed at -1, as in Conic_Fit.py)
# ------------------------------------------------------------------
def height_at_equation(x, A, B, C, D, E):
    """
    Return the bead's height at position x, solving the conic equation
    directly for y (quadratic in y). Returns the upper branch (top
    surface of the bead), or None if x falls outside the curve's domain.
    """
    a_coef = C
    b_coef = B * x + E
    c_coef = A * x**2 + D * x - 1

    if abs(a_coef) < 1e-12:
        # C is essentially zero -- equation is linear in y, not quadratic
        if abs(b_coef) < 1e-12:
            return None
        return -c_coef / b_coef

    discriminant = b_coef**2 - 4 * a_coef * c_coef
    if discriminant < 0:
        return None  # no real solution here -- outside the curve's domain

    sqrt_disc = np.sqrt(discriminant)
    root1 = (-b_coef + sqrt_disc) / (2 * a_coef)
    root2 = (-b_coef - sqrt_disc) / (2 * a_coef)
    return max(root1, root2)  # upper branch = top surface of the bead


# ------------------------------------------------------------------
# Interactive test harness
# ------------------------------------------------------------------
def get_choice(prompt, valid_options):
    while True:
        raw = input(prompt).strip().lower()
        if raw in valid_options:
            return raw
        print(f"  Please enter one of: {', '.join(valid_options)}")


def get_float(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("  Please enter a number.")


def define_bead_interactively():
    """Ask the user how they want to define a bead, and return a function
    that computes height at any x for that specific bead."""
    mode = get_choice(
        "\nDefine bead using (1) preset shape or (2) raw equation? [1/2]: ",
        ["1", "2"]
    )

    if mode == "1":
        shape = get_choice(
            "  Shape -- parabola, circle, or ellipse?: ",
            ["parabola", "circle", "ellipse"]
        )
        width = get_float("  Bead width (mm): ")
        height = get_float("  Bead peak height (mm): ")
        return lambda x: height_at_preset(x, width, height, shape)

    else:
        print("  Enter the fitted coefficients A-E (F is fixed at -1):")
        A = get_float("    A: ")
        B = get_float("    B: ")
        C = get_float("    C: ")
        D = get_float("    D: ")
        E = get_float("    E: ")
        return lambda x: height_at_equation(x, A, B, C, D, E)


def main():
    print("=" * 60)
    print("Bead Height Function -- Interactive Test")
    print("=" * 60)

    height_fn = define_bead_interactively()

    print("\nNow query the bead's height at any x-position.")
    print("Type a number to check that x, or 'done' to stop.\n")

    while True:
        raw = input("x = ").strip().lower()
        if raw == "done":
            break
        try:
            x_val = float(raw)
        except ValueError:
            print("  Enter a number, or 'done' to stop.")
            continue

        try:
            y_val = height_fn(x_val)
        except ValueError as e:
            print(f"  Error: {e}")
            continue

        if y_val is None:
            print(f"  x={x_val} -> outside the bead's footprint (no material here)")
        else:
            print(f"  x={x_val} -> height = {y_val:.4f}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------
# Step 3: Overlap engine -- place multiple beads side by side and
# compute the resulting composite surface.
# ------------------------------------------------------------------
def build_bead_centers(count, spacing):
    """
    Return a list of x-positions for each bead's center, evenly spaced
    and centered around x=0.

    Example: count=4, spacing=7 -> centers at -10.5, -3.5, 3.5, 10.5
    """
    first_center = -(count - 1) * spacing / 2.0
    return [first_center + i * spacing for i in range(count)]


def envelope_height(x, height_fn, centers):
    """
    Given a single bead's height function (height_fn(x) -> y, centered
    at x=0) and a list of bead center positions, return the height of
    the COMBINED surface at position x -- the tallest bead present there.

    height_fn must be one of the functions from Step 1/2 (or a lambda
    wrapping them), taking a bead-relative x and returning a height or None.
    """
    best = 0.0  # substrate level, if no bead reaches this x at all
    for center in centers:
        val = height_fn(x - center)
        if val is not None and val > best:
            best = val
    return best


def compute_envelope(height_fn, centers, x_min, x_max, num_samples=500):
    """
    Compute the combined surface height across a range of x-positions.
    Returns two lists: x_values, y_values (same length, ready to plot).
    """
    x_values = [x_min + (x_max - x_min) * i / (num_samples - 1) for i in range(num_samples)]
    y_values = [envelope_height(x, height_fn, centers) for x in x_values]
    return x_values, y_values


def compute_waviness(height_fn, centers, num_samples_per_gap=200):
    """
    For each pair of adjacent beads, find the valley (lowest point of the
    combined surface between them) and compare it to the peak height, to
    quantify how much the surface dips between beads.

    Returns a list of (gap_index, peak_height, valley_height, waviness) tuples,
    one entry per adjacent pair of beads.
    """
    results = []
    for i in range(len(centers) - 1):
        left_center = centers[i]
        right_center = centers[i + 1]
        # Sample densely in the gap between these two bead centers
        x_values = [
            left_center + (right_center - left_center) * j / (num_samples_per_gap - 1)
            for j in range(num_samples_per_gap)
        ]
        y_values = [envelope_height(x, height_fn, centers) for x in x_values]
        valley = min(y_values)
        peak = max(y_values)  # the peak of whichever bead is tallest in this window
        waviness = peak - valley
        results.append((i, peak, valley, waviness))
    return results


# ------------------------------------------------------------------
# Step 4: Area metrics -- overlap area, valley area, overlap percentage,
# and gap detection.
# ------------------------------------------------------------------
def _safe_height(height_fn, x):
    """Call height_fn(x) and return 0.0 instead of None (i.e. treat
    'no material here' as zero height for area/integration purposes)."""
    val = height_fn(x)
    return 0.0 if val is None else val


def compute_single_bead_area(height_fn, half_span=50.0, num_samples=2000):
    """
    Compute the cross-sectional area of ONE bead by numerically
    integrating its height function across a generous span (anything
    outside the bead's real footprint contributes 0, so a wide span
    is safe to use for any bead shape or equation).
    """
    xs = np.linspace(-half_span, half_span, num_samples)
    ys = np.array([_safe_height(height_fn, x) for x in xs])
    return _trapz(ys, xs)


def compute_gap_metrics(height_fn, centers, samples_per_gap=1000, overlap_margin=30.0):
    """
    For each pair of adjacent beads, compute:
      - peak, valley, waviness -- computed within the window BETWEEN the
        two bead centers, which correctly contains the dip/valley for
        symmetric bead shapes.
      - overlap_area -- the area where the two beads' material physically
        coincides. IMPORTANT: this must be integrated over the FULL region
        where both beads are present, not just between the two centers --
        for tight spacing, real overlap extends well beyond both centers
        in each direction. A wide margin is used and is always numerically
        safe, since height_fn returns 0 outside a bead's real footprint.
      - valley_area: the area of the dip relative to the peak level, within
        the between-centers window (how much material would be needed to
        fill the valley flat).
      - has_gap: True if the valley touches/goes below 0 (exposed substrate)
    """
    results = []
    for i in range(len(centers) - 1):
        c1, c2 = centers[i], centers[i + 1]

        # --- Peak / valley / waviness / valley_area: within [c1, c2] ---
        xs_gap = np.linspace(c1, c2, samples_per_gap)
        h1_gap = np.array([_safe_height(height_fn, x - c1) for x in xs_gap])
        h2_gap = np.array([_safe_height(height_fn, x - c2) for x in xs_gap])
        envelope = np.maximum(h1_gap, h2_gap)

        peak = float(envelope.max())
        valley = float(envelope.min())
        waviness = peak - valley
        valley_area = float(_trapz(np.clip(peak - envelope, 0, None), xs_gap))
        has_gap = valley <= 1e-9

        # --- Overlap area: over the FULL region where both beads coexist ---
        xs_wide = np.linspace(c1 - overlap_margin, c2 + overlap_margin, samples_per_gap * 2)
        h1_wide = np.array([_safe_height(height_fn, x - c1) for x in xs_wide])
        h2_wide = np.array([_safe_height(height_fn, x - c2) for x in xs_wide])
        overlap_curve = np.minimum(h1_wide, h2_wide)
        overlap_area = float(_trapz(overlap_curve, xs_wide))

        results.append({
            "gap_index": i,
            "peak": peak,
            "valley": valley,
            "waviness": waviness,
            "overlap_area": overlap_area,
            "valley_area": valley_area,
            "has_gap": has_gap,
        })
    return results


# ------------------------------------------------------------------
# Equal-area optimal spacing solver -- works for ANY bead shape
# (preset or raw equation), by numerically finding the spacing where
# overlap_area equals valley_area (bisection search).
# ------------------------------------------------------------------
def find_equal_area_spacing(height_fn, search_min=0.1, search_max=None, tol=1e-4, max_iter=100):
    """
    Find the center-to-center spacing p at which overlap_area equals
    valley_area for two identical beads (the equal-area criterion).

    Returns (p, overlap_area, valley_area) at the solution, or None if
    no sign change is found in the search range (e.g. the beads never
    overlap enough, or always overlap too much).
    """
    if search_max is None:
        # A generous upper bound -- default to twice the single-bead area's
        # implied footprint, refined below if needed.
        search_max = 40.0

    def f(p):
        centers = [0.0, p]
        m = compute_gap_metrics(height_fn, centers)[0]
        return m["overlap_area"] - m["valley_area"]

    lo, hi = search_min, search_max
    f_lo, f_hi = f(lo), f(hi)

    if f_lo * f_hi > 0:
        return None  # no sign change -- can't bisect

    for _ in range(max_iter):
        mid = (lo + hi) / 2
        f_mid = f(mid)
        if abs(f_mid) < tol:
            break
        if f_lo * f_mid < 0:
            hi = mid
            f_hi = f_mid
        else:
            lo = mid
            f_lo = f_mid

    p_solution = (lo + hi) / 2
    centers = [0.0, p_solution]
    m = compute_gap_metrics(height_fn, centers)[0]
    return p_solution, m["overlap_area"], m["valley_area"]