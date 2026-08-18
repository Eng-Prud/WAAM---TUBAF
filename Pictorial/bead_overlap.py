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
def height_at_equation(x, A, B, C, D, E, valid_half_width=None):
    """
    Return the bead's height at position x, solving the conic equation
    directly for y (quadratic in y). Returns the upper branch (top
    surface of the bead), or None if x falls outside the curve's domain.

    valid_half_width: if provided, x values beyond +/- this distance
    always return None, regardless of what the algebraic equation says.
    This matters specifically for near-parabolic fits (C very close to
    zero): the equation becomes linear in y in that case, which has NO
    natural point where it stops returning a value -- unlike a genuine
    ellipse/circle, a straight line extrapolates forever. Without this
    bound, evaluating far from the bead's real, physical footprint (e.g.
    at wide bead spacing, or during a wide-range area integration) can
    return large, nonsensical, even negative "heights" instead of
    correctly reporting "no material here".
    """
    if valid_half_width is not None and abs(x) > valid_half_width:
        return None

    a_coef = C
    b_coef = B * x + E
    c_coef = A * x**2 + D * x - 1

    if abs(a_coef) < 1e-12:
        # C is essentially zero -- equation is linear in y, not quadratic.
        # A straight line has no natural domain edge, so without an
        # explicit valid_half_width bound (above), this branch cannot by
        # itself tell "real bead" from "meaningless extrapolation".
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


# ------------------------------------------------------------------
# Step 5: Incompressible-material redistribution model.
#
# The "max envelope" model silently discards material: at any x, only
# the taller bead's height is shown, and the shorter bead's material
# at that same x is not accounted for anywhere. Since real welded
# metal is solid and incompressible, that material can't disappear --
# physically it must be pushed into the adjacent valley instead.
#
# The amount of material discarded by the max-envelope model is
# exactly equal to overlap_area (a direct consequence of area
# accounting: two overlapping regions counted once instead of twice
# lose exactly the overlap amount). This model redistributes that
# exact amount of material into the valley, "filling" it from the
# bottom up (like water settling into a dip) until either the
# material runs out or the valley is completely flat.
# ------------------------------------------------------------------
def compute_incompressible_gap(height_fn, c1, c2, samples=2000, overlap_margin=30.0):
    """
    For a single gap between two bead centers, compute the
    incompressible (material-conserving) redistributed surface.

    Material pools at the LOWEST point of the valley first, like a
    liquid settling under gravity -- filling from the bottom up as a
    flat level, rather than spreading gradually up the bead's own
    walls. This matches physical intuition (molten material flows to
    the lowest point, not smeared evenly across the whole slope).

    Trade-off, stated honestly: this creates a distinct "waterline" at
    the exact point where the flat-filled region meets the bead's
    natural slope -- a real change in steepness right at that point.
    This is physically reasonable (a real liquid pooling against a
    solid slope has a genuine waterline, not a smooth blend into it),
    but it is a visibly different look from a smoothly tapered curve.

    Returns a dict with:
      xs, h1, h2, raw_envelope, redistributed_envelope -- arrays for plotting
      xs_wide, overlap_curve_wide -- the true overlap footprint, for shading
      fill_level, mid_height -- the height the pool rose to, and the
        resulting height at the midpoint
      overlap_area, valley_area, peak, valley -- as before
      profile_type -- "concave", "flat", or "convex"
    """
    xs = np.linspace(c1, c2, samples)
    h1 = np.array([_safe_height(height_fn, x - c1) for x in xs])
    h2 = np.array([_safe_height(height_fn, x - c2) for x in xs])
    raw_envelope = np.maximum(h1, h2)

    peak = float(raw_envelope.max())
    valley = float(raw_envelope.min())
    valley_area = float(_trapz(np.clip(peak - raw_envelope, 0, None), xs))

    xs_wide = np.linspace(c1 - overlap_margin, c2 + overlap_margin, samples * 2)
    h1_wide = np.array([_safe_height(height_fn, x - c1) for x in xs_wide])
    h2_wide = np.array([_safe_height(height_fn, x - c2) for x in xs_wide])
    overlap_curve_wide = np.minimum(h1_wide, h2_wide)
    overlap_area = float(_trapz(overlap_curve_wide, xs_wide))

    # Only as much material as is locally available AND needed gets used
    # here -- any true surplus beyond a full local fill is handled at the
    # whole-run level (compute_incompressible_global), not here.
    fill_amount = min(overlap_area, valley_area)

    def filled_area(level):
        return float(_trapz(np.clip(level - raw_envelope, 0, None), xs))

    lo, hi = valley, peak
    for _ in range(60):
        mid = (lo + hi) / 2
        if filled_area(mid) < fill_amount:
            lo = mid
        else:
            hi = mid
    fill_level = (lo + hi) / 2

    redistributed_envelope = np.maximum(raw_envelope, fill_level)
    mid_height = fill_level

    classification_tol = max(1e-3, peak * 1e-4)
    if mid_height < peak - classification_tol:
        profile_type = "concave"
    elif mid_height > peak + classification_tol:
        profile_type = "convex"
    else:
        profile_type = "flat"

    return {
        "xs": xs,
        "h1": h1,
        "h2": h2,
        "raw_envelope": raw_envelope,
        "redistributed_envelope": redistributed_envelope,
        "xs_wide": xs_wide,
        "overlap_curve_wide": overlap_curve_wide,
        "fill_level": fill_level,
        "mid_height": mid_height,
        "overlap_area": overlap_area,
        "valley_area": valley_area,
        "peak": peak,
        "valley": valley,
        "profile_type": profile_type,
    }


# ------------------------------------------------------------------
# Global (whole-run) incompressible redistribution.
#
# Treating each gap independently (as compute_incompressible_gap does)
# produces one separate bump per gap -- correct in isolation, but for
# 3+ beads this creates a repeating scalloped pattern (each gap
# touching back down to the original peak height at every intermediate
# bead), not the single continuous bulge the literature shows for a
# whole overlapping run. This function instead treats the ENTIRE bead
# sequence as one connected system: all redistributed material pools
# together into ONE smooth bump spanning from the first bead's peak to
# the last bead's peak, only touching the original peak height at
# those two outer ends.
# ------------------------------------------------------------------
def compute_incompressible_global(height_fn, centers, samples=4000, overlap_margin=30.0):
    """
    Compute ONE combined incompressible redistribution curve across an
    entire multi-bead run (not gap-by-gap).

    Key insight from the reference literature: the concave case (not
    enough surplus material) still shows individual bead-like humps
    with a shallower dip -- the beads remain visually distinct. Only
    once there's enough surplus to fully flatten every local valley
    does the whole top become smooth -- flat exactly at balance, or
    rising into ONE single continuous bulge if there's extra. This
    function reproduces that distinction directly, rather than always
    adding a bump on top of the (still wavy) raw envelope.

    Returns a dict with:
      xs, raw_envelope, redistributed_envelope -- arrays spanning the
        whole run, from centers[0] to centers[-1]
      total_overlap_area, total_valley_area -- summed across all gaps
      peak -- the common peak height (identical beads)
      profile_type -- "concave", "flat", or "convex", based on totals
    """
    x_start, x_end = centers[0], centers[-1]
    xs = np.linspace(x_start, x_end, samples)
    raw_envelope = np.array([
        max(_safe_height(height_fn, x - c) for c in centers) for x in xs
    ])
    peak = float(raw_envelope.max())

    per_gap = compute_gap_metrics(height_fn, centers, overlap_margin=overlap_margin)
    total_overlap_area = sum(m["overlap_area"] for m in per_gap)
    total_valley_area = sum(m["valley_area"] for m in per_gap)

    span = x_end - x_start
    surplus = total_overlap_area - total_valley_area

    if surplus >= 0:
        # Enough (or more than enough) material to fully flatten every
        # local valley: the base becomes the flat peak line. Any leftover
        # surplus is redistributed using a Tukey-window-style shape: FLAT
        # across most of the middle, tapering smoothly only near the two
        # ends. This spreads the excess broadly across the whole run
        # (matching the physical intuition that molten material settles
        # rather than piling into one sharp spike) instead of a single
        # narrow raised-cosine peak.
        taper_fraction = 0.5  # fraction of the span used for tapering (split between both ends); the rest is flat
        taper_len = taper_fraction * span / 2
        rel_x = xs - x_start
        unit_bump = np.ones_like(xs)
        rising = rel_x <= taper_len
        falling = rel_x >= (span - taper_len)
        unit_bump[rising] = (1 - np.cos(np.pi * rel_x[rising] / taper_len)) / 2
        unit_bump[falling] = (1 - np.cos(np.pi * (span - rel_x[falling]) / taper_len)) / 2

        unit_area = float(_trapz(unit_bump, xs))
        bump_amplitude = surplus / unit_area if unit_area > 0 else 0.0
        bump = bump_amplitude * unit_bump
        redistributed_envelope = peak + bump
        mid_height = peak + bump_amplitude  # unit_bump is exactly 1 across the flat middle
    else:
        # Not enough material to fully flatten -- fall back to local,
        # per-gap smooth redistribution (still shows individual bead
        # humps with a shallower dip, matching the concave case).
        redistributed_envelope = np.copy(raw_envelope)
        for i in range(len(centers) - 1):
            c1, c2 = centers[i], centers[i + 1]
            gap_result = compute_incompressible_gap(height_fn, c1, c2, samples=samples // (len(centers) - 1) + 2)
            mask = (xs >= c1) & (xs <= c2)
            redistributed_envelope[mask] = np.interp(xs[mask], gap_result["xs"], gap_result["redistributed_envelope"])
        mid_x = (x_start + x_end) / 2
        idx = np.argmin(np.abs(xs - mid_x))
        mid_height = float(redistributed_envelope[idx])

    classification_tol = max(1e-3, peak * 1e-4)
    if mid_height < peak - classification_tol:
        profile_type = "concave"
    elif mid_height > peak + classification_tol:
        profile_type = "convex"
    else:
        profile_type = "flat"

    return {
        "xs": xs,
        "raw_envelope": raw_envelope,
        "redistributed_envelope": redistributed_envelope,
        "total_overlap_area": total_overlap_area,
        "total_valley_area": total_valley_area,
        "peak": peak,
        "mid_height": mid_height,
        "profile_type": profile_type,
    }


# ------------------------------------------------------------------
# Global equal-area spacing finder -- specific to the actual bead
# count, using the WHOLE-RUN totals (not just one pair). This is
# different from find_equal_area_spacing, which only balances a
# single PAIR of beads and can disagree with the true whole-run
# balance point once there are 3+ beads.
# ------------------------------------------------------------------
def find_global_equal_area_spacing(height_fn, count, search_min=0.1, search_max=40.0, tol=1e-4, max_iter=60):
    """
    Find the spacing at which, for a run of `count` identical beads,
    total_overlap_area exactly equals total_valley_area across the
    WHOLE run -- the spacing at which compute_incompressible_global
    reports "flat". Returns (spacing, total_overlap_area, total_valley_area)
    or None if no sign change is found in the search range.
    """
    def f(spacing):
        centers = build_bead_centers(count, spacing)
        r = compute_incompressible_global(height_fn, centers, samples=800)
        return r["total_overlap_area"] - r["total_valley_area"]

    lo, hi = search_min, search_max
    f_lo, f_hi = f(lo), f(hi)
    if f_lo * f_hi > 0:
        return None

    for _ in range(max_iter):
        mid = (lo + hi) / 2
        f_mid = f(mid)
        if abs(f_mid) < tol:
            break
        if f_lo * f_mid < 0:
            hi = mid
        else:
            lo = mid
            f_lo = f_mid
    spacing_solution = (lo + hi) / 2
    centers = build_bead_centers(count, spacing_solution)
    r = compute_incompressible_global(height_fn, centers, samples=800)
    return spacing_solution, r["total_overlap_area"], r["total_valley_area"]


# ------------------------------------------------------------------
# Conic fitting and geometric analysis -- shared backend for both
# the standalone Conic_Fit.py script and the Streamlit app's
# integrated "fit from points" mode. Kept centralized here so both
# entry points use exactly the same, independently-verified math.
# ------------------------------------------------------------------
def fit_conic_from_points(x_data, y_data):
    """Least-squares fit of the general conic (F fixed at -1).
    Returns (A, B, C, D, E), X_matrix, Y_vector."""
    X_matrix = np.column_stack([
        x_data**2, x_data * y_data, y_data**2, x_data, y_data
    ])
    Y_vector = np.ones_like(x_data)
    coeffs, _, _, _ = np.linalg.lstsq(X_matrix, Y_vector, rcond=None)
    return coeffs, X_matrix, Y_vector


def classify_curve(A, B, C, discriminant, tolerance_rel):
    """Classify the conic using the discriminant, checking circle/ellipse
    before the near-zero-discriminant parabola check (a genuine circle
    naturally has a small negative discriminant, -4A^2)."""
    scale = max(abs(A), abs(C), abs(B), 1e-12)
    if abs(B) < tolerance_rel * scale and abs(A - C) < tolerance_rel * scale:
        return "Circle"
    elif abs(discriminant) < tolerance_rel * scale**2:
        return "Parabola"
    elif discriminant < 0:
        return "Ellipse / circular arc segment"
    else:
        return "Hyperbola (not expected for a weld bead)"


def analyze_circle_or_ellipse(A, B, C, D, E, F):
    """Numerically extract center, semi-axes, rotation, and (for a true
    ellipse) focal distance/eccentricity/foci, via eigen-decomposition.
    Verified against known ground-truth circle and ellipse shapes,
    including rotated cases."""
    Q = np.array([[A, B / 2], [B / 2, C]])
    M = np.array([[2 * A, B], [B, 2 * C]])
    rhs = np.array([-D, -E])
    x0, y0 = np.linalg.solve(M, rhs)
    F0 = A * x0**2 + B * x0 * y0 + C * y0**2 + D * x0 + E * y0 + F

    eigvals, eigvecs = np.linalg.eigh(Q)
    axes_sq = [-F0 / lam for lam in eigvals]
    a_sq, b_sq = max(axes_sq), min(axes_sq)
    a, b = np.sqrt(max(a_sq, 0)), np.sqrt(max(b_sq, 0))

    major_idx = np.argmax(axes_sq)
    major_dir = eigvecs[:, major_idx]
    rotation_deg = np.degrees(np.arctan2(major_dir[1], major_dir[0])) % 180
    is_circle = np.isclose(a, b, rtol=1e-6)

    result = {"center": (x0, y0), "semi_major": a, "semi_minor": b,
              "rotation_deg": rotation_deg, "is_circle": is_circle}

    if not is_circle and a_sq > b_sq:
        c = np.sqrt(a_sq - b_sq)
        ecc = c / a
        theta = np.radians(rotation_deg)
        focus1 = (x0 + c * np.cos(theta), y0 + c * np.sin(theta))
        focus2 = (x0 - c * np.cos(theta), y0 - c * np.sin(theta))
        result.update({"c": c, "eccentricity": ecc, "focus1": focus1, "focus2": focus2})

    return result


def analyze_parabola(A, B, C, D, E, F):
    """Numerically extract vertex, axis direction, focal length (p), and
    focus, via eigen-decomposition. Verified against known ground-truth
    parabolas in multiple orientations."""
    Q = np.array([[A, B / 2], [B / 2, C]])
    eigvals, eigvecs = np.linalg.eigh(Q)

    zero_idx = np.argmin(np.abs(eigvals))
    nonzero_idx = 1 - zero_idx
    lam = eigvals[nonzero_idx]
    axis_dir = eigvecs[:, zero_idx]
    perp_dir = eigvecs[:, nonzero_idx]

    D_along_axis = D * axis_dir[0] + E * axis_dir[1]
    E_along_perp = D * perp_dir[0] + E * perp_dir[1]

    Y_shift = E_along_perp / (2 * lam)
    F_shift = F - E_along_perp**2 / (4 * lam)
    X_shift = F_shift / D_along_axis if abs(D_along_axis) > 1e-12 else 0.0
    p_coef = -D_along_axis / lam if abs(lam) > 1e-12 else 0.0

    X_vertex = -X_shift
    Y_vertex = -Y_shift
    vertex = X_vertex * axis_dir + Y_vertex * perp_dir

    true_dir = axis_dir if p_coef >= 0 else -axis_dir
    p = abs(p_coef) / 4.0
    focus = vertex + p * true_dir
    axis_angle_deg = np.degrees(np.arctan2(true_dir[1], true_dir[0])) % 360

    return {"vertex": tuple(vertex), "axis_angle_deg": axis_angle_deg,
            "p": p, "focus": tuple(focus)}