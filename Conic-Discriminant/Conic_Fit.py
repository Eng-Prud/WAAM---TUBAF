"""
Conic Discriminant Fit for Weld Bead Profile (Interactive Version)
--------------------------------------------------------------------
Prompts you for your bead profile points and settings, fits the
general conic equation:
    A*x^2 + B*x*y + C*y^2 + D*x + E*y = 1   (F fixed at -1)
using least squares, then computes the discriminant to classify
the curve shape (parabola / circle / ellipse-arc / hyperbola).

Just run this script -- no code editing required for new data.
"""

import numpy as np


def get_number_of_points():
    """Ask the user how many (x, y) points they have. Must be >= 5,
    since there are 5 unknown coefficients (A, B, C, D, E) to solve for."""
    while True:
        raw = input("How many (x, y) points do you have? ").strip()
        try:
            n = int(raw)
        except ValueError:
            print("  Please enter a whole number.")
            continue
        if n < 5:
            print("  You need at least 5 points to solve for the 5 unknown "
                  "coefficients (A-E). More points (10+) gives a more "
                  "reliable, noise-resistant fit.")
            continue
        return n


def get_points(n):
    """Prompt the user for each (x, y) point, one at a time."""
    x_vals = []
    y_vals = []
    print(f"\nEnter your {n} points (bead width position x, bead height y).")
    for i in range(1, n + 1):
        while True:
            raw = input(f"  Point {i} -- enter as 'x, y' (e.g. -3.0, 1.8): ").strip()
            parts = raw.replace(",", " ").split()
            if len(parts) != 2:
                print("    Could not read two numbers. Try again, e.g. -3.0, 1.8")
                continue
            try:
                x_val = float(parts[0])
                y_val = float(parts[1])
            except ValueError:
                print("    Both values must be numbers. Try again.")
                continue
            x_vals.append(x_val)
            y_vals.append(y_val)
            break
    return np.array(x_vals), np.array(y_vals)


def get_tolerance():
    """Ask the user for the classification tolerance, or use a sensible default."""
    default = 0.05
    raw = input(
        f"\nClassification tolerance (relative, controls how strict the "
        f"parabola/circle/ellipse cutoff is). Press Enter to use the "
        f"default ({default}), or type your own value: "
    ).strip()
    if raw == "":
        return default
    try:
        val = float(raw)
        if val <= 0:
            print("  Tolerance must be positive -- using default instead.")
            return default
        return val
    except ValueError:
        print("  Could not read that as a number -- using default instead.")
        return default


def fit_conic(x_data, y_data):
    """Build the least-squares matrix and solve for A, B, C, D, E (F fixed at -1)."""
    X_matrix = np.column_stack([
        x_data**2,          # column for A
        x_data * y_data,    # column for B
        y_data**2,          # column for C
        x_data,              # column for D
        y_data               # column for E
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


def main():
    print("=" * 60)
    print("Conic Discriminant Fit -- Weld Bead Profile Classifier")
    print("=" * 60)

    n = get_number_of_points()
    x_data, y_data = get_points(n)
    tolerance_rel = get_tolerance()

    coeffs, X_matrix, Y_vector = fit_conic(x_data, y_data)
    A, B, C, D, E = coeffs
    F = -1.0

    print("\n" + "-" * 60)
    print("Fitted conic coefficients:")
    print(f"  A = {A:.6f}")
    print(f"  B = {B:.6f}")
    print(f"  C = {C:.6f}")
    print(f"  D = {D:.6f}")
    print(f"  E = {E:.6f}")
    print(f"  F = {F:.6f}  (fixed)")

    discriminant = B**2 - 4 * A * C
    print(f"\nDiscriminant (B^2 - 4AC) = {discriminant:.6f}")

    curve_type = classify_curve(A, B, C, discriminant, tolerance_rel)
    print(f"\n--> Classified curve type: {curve_type}")

    # Fit quality check: how close the left-hand side lands to 1 at each point
    lhs_values = X_matrix @ coeffs
    residuals_from_1 = lhs_values - 1.0
    rmse = np.sqrt(np.mean(residuals_from_1 ** 2))

    print("\nFit check -- left-hand side value at each point (target = 1.0):")
    for i, val in enumerate(lhs_values):
        print(f"  Point {i+1}: {val:.4f}  (deviation: {val - 1.0:+.4f})")

    print(f"\nRMSE of deviation from 1.0: {rmse:.6f}")
    print("(Smaller RMSE means the conic equation fits your points more tightly.)")
    print("-" * 60)


if __name__ == "__main__":
    main()