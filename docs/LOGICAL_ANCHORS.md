# Logical Spatial Anchors

## Purpose

Logical spatial anchors provide a robust intermediate representation between raw OCR geometry and higher-level document grouping.

The primary motivation is that absolute alignment is brittle. The same logical indentation may move across a page because of skew, OCR bounding-box noise, scan translation, crop variation, DPI, or local layout drift.

OCR-Lexer therefore does **not** primarily quantize absolute coordinates. It infers latent spatial anchors and quantizes relationships relative to them.

## 1. Anchor definition

A logical anchor is a latent geometric reference supported by recurring observations.

It is not necessarily a point or fixed x-coordinate. For left/right alignment on a skewed page, an anchor may be modeled as a trajectory:

```text
x_A(y) = a + b*y
```

where `b` can absorb page skew or gradual drift.

More complex models may be introduced only if experiments demonstrate that a linear trajectory is insufficient.

## 2. Anchor types

Initial generic anchor primitives:

```text
LEFT_TEXT_ANCHOR
RIGHT_TEXT_ANCHOR
RIGHT_NUMERIC_ANCHOR
DECIMAL_ANCHOR
BASELINE_ANCHOR
COLUMN_BOUNDARY
REGION_LEFT_BOUNDARY
REGION_RIGHT_BOUNDARY
```

The first prototype should focus on `LEFT_TEXT_ANCHOR`, `RIGHT_NUMERIC_ANCHOR`, and baseline evidence.

Anchor types must remain geometric. `PROGRAM_ANCHOR` or `REGION_ANCHOR` would prematurely introduce domain semantics.

## 3. Candidate observations

Using every OCR token start as a left-anchor observation would create substantial noise because interior words naturally begin at many x positions.

A minimal prerequisite is therefore local adjacency sufficient to identify **candidate text-run starts and ends**.

```text
OCR tokens
    -> local horizontal-neighbor candidates
    -> candidate run starts / ends
    -> anchor discovery
```

This does not require a finalized visual-line segmentation. `candidate run start` is intentionally a weaker hypothesis.

## 4. Membership

For object `i` at vertical position `y_i` and anchor `A`:

```text
r_iA = x_i - x_A(y_i)
```

Membership should use normalized residuals, for example relative to local median token height:

```text
r_norm = r_iA / H_local
```

A candidate may have soft membership in multiple anchors:

```text
P(A2 | object) = 0.58
P(A3 | object) = 0.42
```

Raw x/y and residual values remain available.

## 5. Anchor graph

Anchors form an ordered relational graph rather than merely an array of x positions.

```text
A0 --RIGHT_OF--> A1 --RIGHT_OF--> A2
```

Potential relations include:

```text
LEFT_OF
RIGHT_OF
NEIGHBOR_LEFT
NEIGHBOR_RIGHT
APPROX_EQUAL_STEP
```

The ordinal topology is often more structurally useful than exact inter-anchor distance.

## 6. Relative transitions

For two candidate fragments or entries, downstream logic can derive transitions from their anchor memberships:

```text
SAME
STEP_RIGHT
STEP_LEFT
SKIP_RIGHT
SKIP_LEFT
UNRESOLVED
```

For example:

```text
A0 -> A1 : STEP_RIGHT
A1 -> A2 : STEP_RIGHT
A2 -> A2 : SAME
A2 -> A1 : STEP_LEFT
```

This can later be interpreted semantically as indentation/dedentation, but the spatial layer itself should remain neutral.

## 7. Why this is robust to skew

Consider observed left edges:

```text
y=100  x=101
y=300  x=105
y=500  x=109
y=700  x=113
```

Absolute x clustering may interpret these as drifting alignment. A trajectory such as:

```text
x_A(y) = 99 + 0.02*y
```

explains them as one logical anchor with small residuals.

The structural representation therefore becomes approximately invariant to the global skew that caused the raw x positions to drift.

## 8. Local rather than universal anchor systems

A document page may contain a header, one or more tables, prose, and footnotes with unrelated alignment systems. OCR-Lexer should not force them into a single global anchor vocabulary.

Anchors should be inferable at multiple scopes:

```text
region -> page -> document
```

with broader scopes providing fallback evidence when local observations are insufficient.

Cross-region or cross-page anchor equivalence should be a later hypothesis.

## 9. Cross-page alignment

Page stitching should compare anchor **structure**, not raw coordinates.

```text
Page N:     A0 -> A1 -> A2
Page N+1:   B0 -> B1 -> B2
```

The parser may hypothesize that `A1 ~= B1` and `A2 ~= B2` based on ordinal topology, relative spacing, column structure, surrounding semantics, and continuation evidence even when their absolute coordinates differ.

This turns part of page stitching into an anchor-graph alignment problem.

## 10. Negative-space interpretation

Anchors allow recurring whitespace to become symbolic evidence.

Examples:

```text
same anchor                    -> SAME
next logical anchor right      -> STEP_RIGHT
next logical anchor left       -> STEP_LEFT
large gap to numeric anchor    -> candidate FIELD_SHIFT
return to earlier anchor       -> possible structural closure
```

The important distinction is:

> Do not quantize coordinates. Infer latent spatial anchors, then quantize relationships relative to those anchors.

## 11. Initial data structures

```python
@dataclass
class SpatialAnchorHypothesis:
    id: int
    kind: AnchorKind
    intercept: float
    slope: float
    support_ids: tuple[int, ...]
    score: float
    residual_scale: float


@dataclass
class AnchorMembership:
    object_id: int
    anchor_id: int
    residual: float
    normalized_residual: float
    score: float


@dataclass
class AnchorTransition:
    source_object_id: int
    target_object_id: int
    relation_scores: dict[AnchorRelation, float]
```

Suggested initial relations:

```python
class AnchorRelation(Enum):
    SAME = auto()
    STEP_RIGHT = auto()
    STEP_LEFT = auto()
    SKIP_RIGHT = auto()
    SKIP_LEFT = auto()
    UNRESOLVED = auto()
```

## 12. Candidate fitting

The first implementation should favor deterministic, inspectable methods:

- sparse candidate generation;
- robust linear regression or RANSAC for anchor trajectories;
- residual-based support scoring;
- local-height normalization;
- graph ordering of accepted anchor hypotheses.

Learned models should be introduced only after deterministic baselines expose specific shortcomings.

## 13. Evaluation

The anchor layer should be evaluated independently of logical-row or hierarchy accuracy.

Questions:

1. Can a human identify stable logical alignments on the page?
2. Does the algorithm recover those alignments?
3. Are candidate run starts/ends assigned to the expected anchor?
4. Do memberships remain stable under skew and local drift?
5. Are relative transitions more stable than raw x-difference thresholds?
6. Does the anchor model materially outperform simple absolute x clustering?

A difficult-page test set should deliberately contain skew, multiline descriptions, irregular indentation, numeric columns, page transitions, and OCR bbox noise.

## 14. Diagnostic visualization

The first implementation should include an HTML/image diagnostic overlay showing:

- source OCR boxes;
- candidate run starts/ends;
- inferred anchor trajectories;
- anchor IDs;
- support observations;
- membership residuals/confidences;
- competing memberships;
- anchor graph ordering.

The visualization is considered part of the algorithm-development interface, not optional presentation polish.
