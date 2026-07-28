"""
Bead Overlap Simulator - Step 3 Runner
------------------------------------------
Defines ONE bead shape (all beads are assumed identical, since they'd be
welded with the same process parameters), places multiple copies of it
side by side at a chosen spacing, computes the combined surface, and
plots the result.
"""

import matplotlib
matplotlib.use("Agg")  # no display needed -- we save to a file
import matplotlib.pyplot as plt

from bead_overlap import (
    height_at_preset, height_at_equation,
    build_bead_centers, compute_envelope, compute_waviness
)


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


def get_int(prompt, minimum=1):
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
            if val < minimum:
                print(f"  Must be at least {minimum}.")
                continue
            return val
        except ValueError:
            print("  Please enter a whole number.")


def define_single_bead():
    """Ask the user to define ONE bead shape (reused for every bead placed)."""
    mode = get_choice(
        "\nDefine the bead shape using (1) preset shape or (2) raw equation? [1/2]: ",
        ["1", "2"]
    )
    if mode == "1":
        shape = get_choice("  Shape -- parabola, circle, or ellipse?: ",
                            ["parabola", "circle", "ellipse"])
        width = get_float("  Bead width (mm): ")
        height = get_float("  Bead peak height (mm): ")
        return lambda x: height_at_preset(x, width, height, shape), width
    else:
        print("  Enter the fitted coefficients A-E (F is fixed at -1):")
        A = get_float("    A: ")
        B = get_float("    B: ")
        C = get_float("    C: ")
        D = get_float("    D: ")
        E = get_float("    E: ")
        # Rough width estimate for plotting range -- just needs to be generous
        width = 20.0
        return lambda x: height_at_equation(x, A, B, C, D, E), width


def main():
    print("=" * 60)
    print("Bead Overlap Simulator -- Step 3")
    print("=" * 60)

    height_fn, approx_width = define_single_bead()

    count = get_int("\nHow many beads to place side by side?: ", minimum=1)
    spacing = get_float("Center-to-center spacing between beads (mm): ")

    centers = build_bead_centers(count, spacing)
    print(f"\nBead centers: {[round(c, 2) for c in centers]}")

    x_min = min(centers) - approx_width
    x_max = max(centers) + approx_width
    x_values, y_values = compute_envelope(height_fn, centers, x_min, x_max, num_samples=800)

    # --- Metrics ---
    if count > 1:
        waviness_results = compute_waviness(height_fn, centers)
        print("\nWaviness between adjacent beads:")
        for i, peak, valley, waviness in waviness_results:
            print(f"  Beads {i+1}-{i+2}: peak={peak:.4f}  valley={valley:.4f}  waviness={waviness:.4f}")
        max_waviness = max(w for _, _, _, w in waviness_results)
        print(f"\nWorst-case waviness across all gaps: {max_waviness:.4f} mm")
    else:
        print("\nOnly one bead placed -- no overlap to measure.")

    total_span = max(centers) + approx_width / 2 - (min(centers) - approx_width / 2)
    print(f"Approximate total coverage width: {total_span:.2f} mm")

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax.fill_between(x_values, y_values, 0, color="#5DCAA5", alpha=0.6)
    ax.plot(x_values, y_values, color="#0F6E56", lw=2)
    ax.axhline(0, color="#888780", lw=1)
    ax.set_xlabel("x -- position across substrate (mm)")
    ax.set_ylabel("y -- combined surface height (mm)")
    ax.set_title(f"{count} beads, spacing = {spacing} mm")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    output_path = "overlap_result.png"
    fig.savefig(output_path)
    print(f"\nPlot saved to: {output_path}")


if __name__ == "__main__":
    main()