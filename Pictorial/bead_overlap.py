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