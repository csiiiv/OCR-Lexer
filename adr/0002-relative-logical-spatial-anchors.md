# ADR 0002: Use Relative Logical Spatial Anchors

- Status: Accepted
- Date: 2026-09-10

## Context

Whitespace, indentation, and alignment carry substantial document syntax, but absolute coordinates are noisy. OCR boxes vary; scans may be translated or cropped; DPI differs; and skew causes logical alignments to drift in x as y changes.

Fixed bins such as `x=100 -> indent level 1` would therefore create brittle early decisions.

## Decision

OCR-Lexer will not use absolute coordinate quantization as its primary structural representation.

Instead it will:

1. infer latent logical spatial anchors from recurring local geometry;
2. allow anchors to be skew-aware trajectories rather than fixed coordinates;
3. assign soft membership of observations/fragments to anchors;
4. organize anchors relationally/ordinally;
5. derive relative spatial symbols such as `SAME`, `STEP_RIGHT`, `STEP_LEFT`, `SKIP_RIGHT`, and `SKIP_LEFT`;
6. retain raw and normalized geometry alongside the symbolic representation.

Anchor IDs do not encode hierarchy depth or semantic role.

## Consequences

The representation should be more invariant to skew, translation, crop, DPI, and bbox noise. Anchor discovery becomes an explicit prerequisite and must be independently evaluated. Cross-page alignment can later compare anchor topology rather than requiring raw coordinate equality.
