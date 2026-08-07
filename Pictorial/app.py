"""
Bead Overlap Simulator -- Interactive Streamlit App
------------------------------------------------------
Run with:  streamlit run app.py

Lets you define a single bead shape (preset or raw fitted equation),
then adjust the number of beads and spacing with sliders, seeing the
combined overlap surface, waviness, and area metrics update live.
"""

import streamlit as st
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bead_overlap import (
    height_at_preset, height_at_equation,
    build_bead_centers, compute_envelope,
    compute_single_bead_area, compute_gap_metrics,
    find_equal_area_spacing, compute_incompressible_gap,
    compute_incompressible_global,
    fit_conic_from_points, classify_curve,
    analyze_circle_or_ellipse, analyze_parabola
)

st.set_page_config(page_title="WAAM Bead Overlap Simulator", layout="centered")
st.title("WAAM Bead Overlap Simulator")
st.caption("Side-by-side bead deposition on a flat substrate")

# ------------------------------------------------------------------
# Bead definition
# ------------------------------------------------------------------
st.header("1. Define the bead shape")
st.write("All beads placed are identical, since they'd be welded with the same process parameters.")

mode = st.radio(
    "Bead definition mode",
    ["Preset shape", "Fit from digitized points", "Raw fitted equation"],
    horizontal=True, key="bead_mode"
)

height_fn = None
approx_width = 20.0
error_message = None

if mode == "Preset shape":
    col1, col2, col3 = st.columns(3)
    with col1:
        shape = st.selectbox("Shape", ["parabola", "circle", "ellipse"])
    with col2:
        width = st.number_input("Width (mm)", min_value=0.1, value=11.3, step=0.1)
    with col3:
        height = st.number_input("Peak height (mm)", min_value=0.1, value=4.0, step=0.1)

    if shape == "circle" and height > width / 2:
        error_message = (
            f"Impossible circle: height ({height}) exceeds half-width ({width/2:.2f}). "
            f"A circular arc can never be taller than half its own width -- "
            f"try an ellipse instead, which allows width and height to be set independently."
        )
    else:
        height_fn = lambda x, w=width, h=height, s=shape: height_at_preset(x, w, h, s)
        approx_width = width

elif mode == "Fit from digitized points":
    st.write(
        "Enter your digitized bead profile points (bead width position x, "
        "bead height y), one per row, as `x, y`. Add rows as needed -- at "
        "least 5 points are required to solve for the 5 unknown coefficients."
    )

    if "point_rows" not in st.session_state:
        st.session_state.point_rows = [""] * 5

    for i in range(len(st.session_state.point_rows)):
        st.session_state.point_rows[i] = st.text_input(
            f"Point {i + 1} (x, y)", value=st.session_state.point_rows[i],
            key=f"point_row_{i}", placeholder="e.g. -5.651, 2.016"
        )

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("➕ Add another point"):
            st.session_state.point_rows.append("")
            st.rerun()
    with col_b:
        if st.button("➖ Remove last point") and len(st.session_state.point_rows) > 5:
            st.session_state.point_rows.pop()
            for i in range(len(st.session_state.point_rows), len(st.session_state.point_rows) + 1):
                st.session_state.pop(f"point_row_{i}", None)
            st.rerun()
    with col_c:
        tolerance_rel = st.number_input(
            "Classification tolerance", min_value=0.001, value=0.05, step=0.01,
            format="%.3f", help="Controls how strict the parabola/circle/ellipse cutoff is."
        )

    if st.button("🔬 Run Conic Fit", type="primary"):
        parsed_x, parsed_y, parse_errors = [], [], []
        for i, raw in enumerate(st.session_state.point_rows):
            raw = raw.strip()
            if not raw:
                continue
            parts = raw.replace(",", " ").split()
            if len(parts) != 2:
                parse_errors.append(f"Point {i+1}: could not read two numbers ('{raw}')")
                continue
            try:
                parsed_x.append(float(parts[0]))
                parsed_y.append(float(parts[1]))
            except ValueError:
                parse_errors.append(f"Point {i+1}: '{raw}' is not two valid numbers")

        if parse_errors:
            st.error("Could not parse some points:\n\n" + "\n\n".join(parse_errors))
        elif len(parsed_x) < 5:
            st.error(f"Need at least 5 valid points to fit (got {len(parsed_x)}).")
        else:
            x_arr, y_arr = np.array(parsed_x), np.array(parsed_y)
            coeffs, X_matrix, Y_vector = fit_conic_from_points(x_arr, y_arr)
            A_f, B_f, C_f, D_f, E_f = coeffs
            F_f = -1.0
            discriminant = B_f**2 - 4 * A_f * C_f
            curve_type = classify_curve(A_f, B_f, C_f, discriminant, tolerance_rel)
            lhs_values = X_matrix @ coeffs
            rmse = float(np.sqrt(np.mean((lhs_values - 1.0) ** 2)))
            st.session_state.conic_fit_result = {
                "A": A_f, "B": B_f, "C": C_f, "D": D_f, "E": E_f, "F": F_f,
                "discriminant": discriminant, "curve_type": curve_type,
                "rmse": rmse, "x_data": x_arr, "y_data": y_arr,
                "lhs_values": lhs_values,
                "width_guess": 2 * float(np.max(np.abs(x_arr))) * 1.1,
            }

    if "conic_fit_result" in st.session_state:
        res = st.session_state.conic_fit_result
        st.subheader("Fit results")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Fitted coefficients:**")
            st.write(f"A = {res['A']:.6f}")
            st.write(f"B = {res['B']:.6f}")
            st.write(f"C = {res['C']:.6f}")
            st.write(f"D = {res['D']:.6f}")
            st.write(f"E = {res['E']:.6f}")
            st.write(f"F = {res['F']:.6f}  (fixed)")
        with col2:
            st.metric("Discriminant (B² − 4AC)", f"{res['discriminant']:.6f}")
            st.metric("Classified curve type", res["curve_type"])
            st.metric("Fit RMSE", f"{res['rmse']:.6f}")

        with st.expander("Per-point fit deviation"):
            for i, (xv, yv, lhs) in enumerate(zip(res["x_data"], res["y_data"], res["lhs_values"])):
                st.write(f"Point {i+1} (x={xv}, y={yv}): LHS = {lhs:.4f}  (deviation {lhs-1.0:+.4f})")

        st.write("**Geometric parameters:**")
        ct = res["curve_type"]
        if "Circle" in ct or ("Ellipse" in ct):
            geo = analyze_circle_or_ellipse(res["A"], res["B"], res["C"], res["D"], res["E"], res["F"])
            if geo["is_circle"]:
                st.write(f"Center: ({geo['center'][0]:.4f}, {geo['center'][1]:.4f})")
                st.write(f"Radius: {geo['semi_major']:.4f}")
                st.write(f"Equation: (x − {geo['center'][0]:.4f})² + (y − {geo['center'][1]:.4f})² = {geo['semi_major']:.4f}²")
            else:
                st.write(f"Center: ({geo['center'][0]:.4f}, {geo['center'][1]:.4f})")
                st.write(f"Semi-major axis: {geo['semi_major']:.4f}  |  Semi-minor axis: {geo['semi_minor']:.4f}")
                st.write(f"Rotation: {geo['rotation_deg']:.4f}°")
                if "c" in geo:
                    st.write(f"Eccentricity: {geo['eccentricity']:.4f}  |  Focal distance: {geo['c']:.4f}")
                    st.write(f"Foci: ({geo['focus1'][0]:.4f}, {geo['focus1'][1]:.4f}) and ({geo['focus2'][0]:.4f}, {geo['focus2'][1]:.4f})")
        elif "Parabola" in ct:
            geo = analyze_parabola(res["A"], res["B"], res["C"], res["D"], res["E"], res["F"])
            st.write(f"Vertex: ({geo['vertex'][0]:.4f}, {geo['vertex'][1]:.4f})")
            st.write(f"Axis direction: {geo['axis_angle_deg']:.4f}° from +x axis")
            st.write(f"Focal length (p): {geo['p']:.4f}  |  Focus: ({geo['focus'][0]:.4f}, {geo['focus'][1]:.4f})")
        else:
            st.write("(Geometric parameters are not computed for a hyperbola -- not physically expected for a weld bead.)")

        st.divider()

        def _load_into_raw_mode():
            st.session_state.coef_A = float(res["A"])
            st.session_state.coef_B = float(res["B"])
            st.session_state.coef_C = float(res["C"])
            st.session_state.coef_D = float(res["D"])
            st.session_state.coef_E = float(res["E"])
            st.session_state.raw_eq_width = float(np.clip(res["width_guess"], 5.0, 80.0))
            st.session_state.bead_mode = "Raw fitted equation"

        st.button(
            "➡️ Use this fitted equation below (switches to Raw fitted equation mode)",
            on_click=_load_into_raw_mode
        )

    # No bead height_fn yet in this mode until the user hands it off --
    # show a placeholder message rather than crashing downstream.
    st.info("Once you've run the fit, click \"Use this fitted equation below\" to load it into the Raw fitted equation mode and continue.")
    st.stop()

else:
    st.write("Enter the fitted coefficients A-E (F is fixed at -1). You can type these "
             "directly, or use \"Fit from digitized points\" above and hand them off automatically.")
    for _k, _v in [("coef_A", 0.0278), ("coef_B", 0.0000), ("coef_C", 0.0278), ("coef_D", 0.0000), ("coef_E", 0.0000)]:
        st.session_state.setdefault(_k, _v)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        A = st.number_input("A", format="%.6f", key="coef_A")
    with col2:
        B = st.number_input("B", format="%.6f", key="coef_B")
    with col3:
        C = st.number_input("C", format="%.6f", key="coef_C")
    with col4:
        D = st.number_input("D", format="%.6f", key="coef_D")
    with col5:
        E = st.number_input("E", format="%.6f", key="coef_E")

    st.session_state.setdefault("raw_eq_width", 20.0)
    approx_width = st.slider(
        "Bead footprint width (mm) -- this is also the physical cutoff: "
        "beyond half this distance from center, the equation is treated "
        "as having no material, even if it would still return a value.",
        5.0, 80.0, key="raw_eq_width"
    )
    height_fn = lambda x, A=A, B=B, C=C, D=D, E=E, hw=approx_width / 2: height_at_equation(x, A, B, C, D, E, valid_half_width=hw)

if error_message:
    st.error(error_message)
    st.stop()

# ------------------------------------------------------------------
# Placement
# ------------------------------------------------------------------
st.header("2. Place the beads")

with st.expander("💡 Suggested equal-area spacing", expanded=True):
    st.write(
        "This is the spacing where overlap area equals valley area (the "
        "materials-balance criterion from the literature) -- it assumes "
        "the molten bead can flow/redistribute during welding. It is "
        "**not** a guarantee of a geometrically flat surface; the plot "
        "below still shows the raw, unflowed geometric envelope."
    )
    eq_result = find_equal_area_spacing(height_fn, search_min=0.1, search_max=approx_width)
    if eq_result is not None:
        eq_spacing, eq_overlap, eq_valley = eq_result
        st.write(f"**Suggested spacing: {eq_spacing:.3f} mm** (overlap area = valley area = {eq_overlap:.3f} mm²)")
    else:
        st.write("Could not find an equal-area spacing in the searched range for this bead shape.")

col1, col2 = st.columns(2)
with col1:
    count = st.slider("Number of beads", min_value=1, max_value=10, value=4)
with col2:
    spacing = st.slider("Center-to-center spacing (mm)", min_value=0.5, max_value=approx_width, value=min(7.0, approx_width), step=0.1)

centers = build_bead_centers(count, spacing)
global_result = compute_incompressible_global(height_fn, centers) if count > 1 else None

# ------------------------------------------------------------------
# Compute + plot
# ------------------------------------------------------------------
x_min = min(centers) - approx_width
x_max = max(centers) + approx_width
x_values, y_values = compute_envelope(height_fn, centers, x_min, x_max, num_samples=800)

st.header("3. Result")

show_incompressible = st.checkbox(
    "Show incompressible material model (the real, physical weld shape)",
    value=True
)
show_details = st.checkbox(
    "Show material redistribution details (where the extra material comes from)",
    value=False
)

OVERLAP_COLOR = "#D98E2B"

fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)

if show_incompressible and count > 1:
    # PRIMARY view: the actual, physical weld outline after redistribution
    # -- filled in solid, the same way every bead has been shown this
    # whole time. This is the answer to "what does the weld look like?"
    #
    # The redistribution only happens BETWEEN bead centers -- the outer
    # flanks of the very first and last bead are untouched, so they're
    # stitched on from the raw (unredistributed) shape to give a complete
    # outline with no missing edges.
    full_x = np.array(x_values)
    full_y = np.array(y_values, dtype=float)
    inner_mask = (full_x >= centers[0]) & (full_x <= centers[-1])
    full_y[inner_mask] = np.interp(full_x[inner_mask], global_result["xs"], global_result["redistributed_envelope"])

    ax.fill_between(full_x, full_y, 0, color="#5DCAA5", alpha=0.6)
    ax.plot(full_x, full_y, color="#0F6E56", lw=2.2,
            label="Actual weld outline (material conserved)")
    # The original, unrealistic "ignore the overlap" shape, for comparison only
    ax.plot(x_values, y_values, color="#993C1D", lw=1.3, linestyle="--",
            label="If material just disappeared (unrealistic)")
else:
    ax.fill_between(x_values, y_values, 0, color="#5DCAA5", alpha=0.6)
    ax.plot(x_values, y_values, color="#0F6E56", lw=2.2, label="Weld outline")

if show_details and count > 1:
    fill_fraction = min(1.0, global_result["total_overlap_area"] / global_result["total_valley_area"]) \
        if global_result["total_valley_area"] > 0 else 1.0
    valley_alpha = 0.08 + 0.42 * fill_fraction

    overlap_label_used = False
    valley_label_used = False
    for i in range(len(centers) - 1):
        c1, c2 = centers[i], centers[i + 1]
        gap_result = compute_incompressible_gap(height_fn, c1, c2)
        ax.fill_between(
            gap_result["xs_wide"], 0, gap_result["overlap_curve_wide"],
            color=OVERLAP_COLOR, alpha=0.5,
            label="Overlap region (material available to redistribute)" if not overlap_label_used else None
        )
        overlap_label_used = True
        ax.fill_between(
            gap_result["xs"], gap_result["raw_envelope"], gap_result["peak"],
            where=(gap_result["raw_envelope"] < gap_result["peak"]),
            color=OVERLAP_COLOR, alpha=valley_alpha,
            label="Valley deficit (where that material is needed)" if not valley_label_used else None
        )
        valley_label_used = True

ax.axhline(0, color="#888780", lw=1)
ax.set_xlabel("x -- position across substrate (mm)")
ax.set_ylabel("y -- combined surface height (mm)")
ax.set_title(f"{count} beads, spacing = {spacing:.1f} mm")
ax.legend(loc="lower center", fontsize=8, frameon=False, ncol=1)
ax.grid(alpha=0.2)
fig.tight_layout()
st.pyplot(fig)

if show_details:
    st.caption(
        "The amber shading is a bookkeeping diagram, not a physical part of "
        "the weld: darker amber shows where two beads' material physically "
        "overlaps (the source), lighter amber shows how much of the gap "
        "between beads still needs filling (the destination) -- faded "
        "in/out depending on how much of that gap is actually being "
        "addressed."
    )
    if global_result["profile_type"] == "convex":
        st.info(
            "ℹ️ At this spacing, there's more overlap material overall than "
            "the valleys need. Since material can't disappear, once every "
            "valley is fully leveled the leftover forms ONE continuous "
            "bulge across the whole run -- not a separate bump per gap."
        )
    elif global_result["profile_type"] == "concave":
        st.info(
            "ℹ️ At this spacing, there isn't enough overlap material to "
            "fully flatten every valley -- the individual beads remain "
            "visible with a shallower (but still present) dip between "
            "them, matching the concave case from the reference literature."
        )

# ------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------
if count > 1:
    gap_metrics = compute_gap_metrics(height_fn, centers)
    single_bead_area = compute_single_bead_area(height_fn)

    any_gap = any(m["has_gap"] for m in gap_metrics)
    if any_gap:
        st.error(
            "⚠️ Gap detected -- the valley touches or drops below the substrate "
            "(y = 0) in at least one gap between beads. This spacing would leave "
            "bare, uncovered substrate exposed between beads."
        )

    max_waviness = max(m["waviness"] for m in gap_metrics)
    avg_overlap_pct = sum(m["overlap_area"] for m in gap_metrics) / len(gap_metrics) / single_bead_area * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Worst-case waviness", f"{max_waviness:.3f} mm")
    col2.metric("Avg. overlap", f"{avg_overlap_pct:.1f} %")
    col3.metric("Single bead area", f"{single_bead_area:.2f} mm²")

    with st.expander("Detailed metrics, per gap between beads", expanded=True):
        for idx, m in enumerate(gap_metrics):
            overlap_pct = (m["overlap_area"] / single_bead_area) * 100
            gap_flag = " ⚠️ GAP" if m["has_gap"] else ""
            st.markdown(f"**Beads {m['gap_index']+1}-{m['gap_index']+2}**{gap_flag}")
            st.write(
                f"- Peak: {m['peak']:.4f} mm | Valley: {m['valley']:.4f} mm | "
                f"Raw waviness: {m['waviness']:.4f} mm"
            )
            st.write(
                f"- Overlap area: {m['overlap_area']:.4f} mm² "
                f"({overlap_pct:.1f}% of a single bead's area)"
            )
            st.write(f"- Valley area (deficit vs. peak level): {m['valley_area']:.4f} mm²")
            st.divider()

        st.markdown("**Incompressible model (whole run, not per-gap):**")
        if global_result["profile_type"] == "flat":
            st.write(
                f"- **Exactly flat** -- total overlap material "
                f"({global_result['total_overlap_area']:.4f} mm²) closely matches "
                f"the total valley deficit ({global_result['total_valley_area']:.4f} mm²) "
                f"across the whole run."
            )
        elif global_result["profile_type"] == "convex":
            st.write(
                f"- **Convex overflow** -- total overlap material "
                f"({global_result['total_overlap_area']:.4f} mm²) exceeds the total "
                f"valley deficit ({global_result['total_valley_area']:.4f} mm²) across "
                f"the whole run. Every valley fully levels out, and the leftover forms "
                f"ONE continuous bulge across the entire run, peaking above "
                f"{global_result['peak']:.4f} mm."
            )
        else:
            st.write(
                f"- **Concave (partial fill)** -- total overlap material "
                f"({global_result['total_overlap_area']:.4f} mm²) is less than the "
                f"total valley deficit needed ({global_result['total_valley_area']:.4f} mm²). "
                f"Individual beads remain visible, each with a shallower dip."
            )

    st.caption(
        "**Overlap area** = the cross-sectional area where two adjacent beads' "
        "material physically coincides. **Valley area** = the area of the dip "
        "relative to the peak height -- how much material would be needed to "
        "fill the valley flat. **Overlap %** = overlap area as a share of a "
        "single bead's own cross-sectional area."
    )
else:
    st.info("Only one bead placed -- no overlap to measure. Increase the bead count above.")