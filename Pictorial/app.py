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
    compute_incompressible_global
)

st.set_page_config(page_title="WAAM Bead Overlap Simulator", layout="centered")
st.title("WAAM Bead Overlap Simulator")
st.caption("Side-by-side bead deposition on a flat substrate")

# ------------------------------------------------------------------
# Bead definition
# ------------------------------------------------------------------
st.header("1. Define the bead shape")
st.write("All beads placed are identical, since they'd be welded with the same process parameters.")

mode = st.radio("Bead definition mode", ["Preset shape", "Raw fitted equation"], horizontal=True)

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

else:
    st.write("Enter the fitted coefficients A-E from Conic_Fit.py (F is fixed at -1):")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        A = st.number_input("A", value=0.0278, format="%.6f")
    with col2:
        B = st.number_input("B", value=0.0000, format="%.6f")
    with col3:
        C = st.number_input("C", value=0.0278, format="%.6f")
    with col4:
        D = st.number_input("D", value=0.0000, format="%.6f")
    with col5:
        E = st.number_input("E", value=0.0000, format="%.6f")
    height_fn = lambda x, A=A, B=B, C=C, D=D, E=E: height_at_equation(x, A, B, C, D, E)
    approx_width = st.slider("Approx. plotting width (mm) -- for display range only", 5.0, 60.0, 20.0)

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
    full_x = x_values
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