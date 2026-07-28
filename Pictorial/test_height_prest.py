"""
Bead Overlap Simulator - Core Math Module
-------------------------------------------
Step 1: height_at() for simple preset bead shapes (width + height only).
"""

import numpy as np


def height_at_preset(x, width, height, shape="parabola"):
    """
    Return the bead's height at position x, for a simple preset shape
    defined only by its overall width and peak height.

    x       : position across the bead width (same units as width/height)
    width   : total bead width (edge to edge)
    height  : peak height at the center of the bead
    shape   : "parabola" or "circle"

    Returns the height at x, or None if x falls outside the bead's footprint.
    """
    half_width = width / 2.0

    # Outside the bead's footprint -- no material here
    if abs(x) > half_width:
        return None

    if shape == "parabola":
        # y = H * (1 - (x/halfwidth)^2)
        return height * (1 - (x / half_width) ** 2)

    elif shape == "circle":
        # A circular arc can never be taller than half its own width --
        # the tallest possible circular cap over a given width is a
        # semicircle, whose height equals exactly half the width.
        if height > half_width:
            raise ValueError(
                f"Impossible circle: height ({height}) exceeds half-width "
                f"({half_width}). A circular arc's height can never exceed "
                f"half its width -- this bead would need a different shape "
                f"(e.g. parabola) or your width/height values need checking."
            )

        # Circle passing through (-halfwidth, 0), (halfwidth, 0), (0, height)
        R = (half_width ** 2 + height ** 2) / (2 * height)
        center_y = height - R
        value_under_root = R ** 2 - x ** 2
        if value_under_root < 0:
            return None
        return np.sqrt(value_under_root) + center_y

    else:
        raise ValueError(f"Unknown shape: {shape}")


# ------------------------------------------------------------------
# Quick manual test -- run this file directly to sanity-check it
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing height_at_preset()")
    print("-" * 50)

    # A parabola, width 11.3, height 4.0 -- check known points
    print("Parabola, width=11.3, height=4.0:")
    for x_test in [0, 5.65, -5.65, 2.0]:
        y = height_at_preset(x_test, width=11.3, height=4.0, shape="parabola")
        print(f"  x={x_test:>6} -> y={y}")

    print()
    print("Circle, width=11.3, height=4.0 (valid: height < half-width):")
    for x_test in [0, 5.65, -5.65, 2.0]:
        y = height_at_preset(x_test, width=11.3, height=4.0, shape="circle")
        print(f"  x={x_test:>6} -> y={y}")

    print()
    print("Outside the bead footprint (should print None):")
    y = height_at_preset(10.0, width=11.3, height=4.0, shape="parabola")
    print(f"  x=10.0 -> y={y}")

    print()
    print("Impossible circle -- height > half-width (should raise an error):")
    try:
        height_at_preset(0, width=11.3, height=6.0, shape="circle")
    except ValueError as e:
        print(f"  Correctly caught: {e}")