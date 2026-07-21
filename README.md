# WAAM — TUBAF

Codebase for my internship at **TU Bergakademie Freiberg (TUBAF)**,
Freiberg, Saxony, Germany, focused on **Wire Arc Additive Manufacturing
(WAAM)** of copper-tin (CuSn) alloy components.

This repository collects the software tools, mathematical models, and
process-control scripts developed over the course of the internship —
spanning robotic path planning, weld process control via DART, and
geometric/mathematical modeling of deposited weld bead profiles.

---

## Context

WAAM builds near-net-shape metal parts by depositing a continuous metal
wire, layer by layer, using a welding arc as the heat source — offering
significantly higher deposition rates than powder-bed additive methods,
at the cost of coarser geometric control. Achieving a dimensionally
accurate, structurally sound part therefore depends on two tightly
coupled problems: **precisely controlling how the robot and torch move**,
and **precisely understanding the geometry of the bead each pass
produces** — since final part quality is ultimately governed by how
successive beads overlap to form a continuous surface.

This repository is organized around that dependency: process control on
one side, geometric/mathematical modeling on the other, with the goal of
closing the loop between them.

---

## Hardware & software environment

| Component | Role |
|---|---|
| **DOOSAN cobot** | 6-axis collaborative robot arm executing torch motion for WAAM deposition |
| **DART** | Process control software used to program torch position/trajectory, shielding gas parameters, and coordinate the deposition sequence |
| **Fume extraction system** | Integrated into the deposition workflow for operator safety during welding |
| **CuSn (copper-tin / tin bronze) wire** | Alloy system under investigation, deposited onto CuSn substrate plates |
| **Python 3.14 / NumPy / SciPy** | Numerical backbone for curve fitting, geometric modeling, and data analysis |

---

## Repository scope

### 1. Robotic path planning
Development and refinement of toolpath strategies for the DOOSAN cobot —
governing torch trajectory, travel speed, and layer-to-layer positioning
during multi-pass WAAM deposition.

### 2. Process parameter studies (DART)
Controlled trials varying weld current and shielding gas composition,
executed and logged through DART, to characterize their effect on bead
geometry, penetration quality, and deposition continuity. Weld quality
is assessed in part through **contact angle analysis** at the bead toe,
used as a proxy indicator for penetration quality (obtuse angle →
favorable penetration; acute angle → poor penetration).

### 3. Mathematical modeling of weld bead geometry
The central open engineering question this repository works toward:

> **Can the cross-sectional profile of a single weld bead be described
> by an exact, closed-form mathematical model — and if so, can that
> model be used to predict optimal bead-to-bead overlap for a smooth,
> void-free multi-pass surface?**

Bead overlap strategy is typically approached empirically or with
simplified parabolic assumptions in the literature. This work instead
treats bead profile identification as a **model validation problem**:
digitized cross-section data (width, height, and full coordinate
profiles) is tested against candidate closed-form curve families —
parabolic, circular arc, cosine, and elliptical — using quantitative,
reproducible methods rather than visual curve matching. Where a bead's
true profile does not reduce to any closed-form family (e.g. due to
asymmetric wetting, arc drag, or undercut), the modeling approach falls
back to piecewise (spline) representations.

Current validation methods implemented or in development:

- **Conic discriminant classification** — fitting the general conic
  equation to digitized bead coordinates via least-squares, then using
  the discriminant to rigorously classify the profile as parabolic,
  circular, elliptical, or neither (see [`Conic discriminant/`](./Conic%20discriminant/))
- **Curvature consistency analysis** — checking whether local curvature
  along the bead profile is constant (circular arc signature) or
  varies systematically (parabolic/elliptical signature)
- **Polynomial order testing** — determining the minimum polynomial
  order that explains the profile without overfitting, as a precursor
  check before committing to a specific closed-form family
- **Taylor series coefficient matching** — distinguishing visually
  similar candidates (e.g. parabola vs. cosine) via their higher-order
  series expansion signatures

The end objective is a validated geometric model of bead cross-section
that can be fed forward into overlap-spacing calculations — enabling
multi-pass deposition strategies that minimize surface waviness and
inter-bead voids without relying on trial-and-error parameter sweeps.

---

## Repository structure

```
WAAM---TUBAF/
├── Conic discriminant/     # Conic-fit bead profile classifier (see its own README)
├── GcodeConverter/         # G-code generation / conversion utilities for path planning
└── README.md               # This file
```

Each subdirectory contains its own README with a focused technical
explanation of that component's method and usage.

---

## Author

Prudence Njoroge — Mechanical Engineering student, Jomo Kenyatta University of
Agriculture and Technology (JKUAT), Kenya. Erasmus intern at TU
Bergakademie Freiberg, working on WAAM process development for CuSn
alloy systems.