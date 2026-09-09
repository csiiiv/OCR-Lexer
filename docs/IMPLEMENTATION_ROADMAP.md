# Implementation Roadmap

## Guiding strategy

Build and evaluate each prerequisite before relying on it at the next abstraction level. Avoid implementing logical rows or hierarchy merely to make the demo look complete.

## Phase 0 — Corpus and diagnostics

- Select 20–30 deliberately difficult pages.
- Include skew, multiline descriptions, irregular indentation, amount columns, cross-page continuations, and OCR bbox noise.
- Preserve source page images and canonical OCR tokens.
- Define diagnostic output conventions.

**Exit criterion:** a reproducible test corpus and token overlay exist.

## Phase 1 — Canonical observations

Implement immutable `OCRToken` and measured geometry.

Suggested modules:

```text
ocr_lexer/
  observations/
    token.py
    geometry.py
```

**Exit criterion:** all later objects can reference stable token IDs and page coordinates.

## Phase 2 — Sparse local adjacency

Suggested modules:

```text
ocr_lexer/
  spatial/
    measurements.py
    neighbors.py
```

Generate candidate nearby comparisons rather than an all-pairs graph.

Measure raw and normalized geometry without assigning semantic meaning.

**Exit criterion:** diagnostic views can show plausible left/right/above/below candidate relationships.

## Phase 3 — Candidate run starts and ends

Determine whether a token plausibly begins or ends a local horizontal run without requiring finalized line grouping.

Suggested module:

```text
ocr_lexer/spatial/run_boundaries.py
```

**Exit criterion:** candidate run boundaries provide a useful, lower-noise observation set for anchor fitting.

## Phase 4 — Logical spatial anchors

Suggested modules:

```text
ocr_lexer/
  spatial/
    anchors/
      model.py
      candidates.py
      fit.py
      membership.py
      graph.py
      transitions.py
```

Initial anchor model:

```text
x(y) = intercept + slope*y
```

Use robust fitting and normalized residuals.

**Exit criterion:** inferred left-text and numeric-right anchors remain stable on skewed/noisy pages and outperform simple absolute-x clustering.

## Phase 5 — Relative spatial symbolization

Produce soft relationships:

```text
SAME
STEP_RIGHT
STEP_LEFT
SKIP_RIGHT
SKIP_LEFT
UNRESOLVED
```

Retain raw and normalized measurements.

**Exit criterion:** relative transitions are demonstrably more stable than fixed pixel thresholds across the test corpus.

## Phase 6 — Geometric projections

Develop overlapping hypotheses for:

- visual baselines/lines;
- numeric columns;
- local regions;
- vertical gap modes;
- text fragments.

Do not force these into one tree.

**Exit criterion:** visual-line hypotheses can coexist with field/block boundaries that split or cross those lines.

## Phase 7 — Text-block hypotheses

Infer coherent textual units using geometry, anchors, lexical continuity, and regional/page context.

**Exit criterion:** multiline descriptions can be reconstructed without requiring every visual line to be one logical row.

## Phase 8 — Logical entries

Combine text blocks and value fields into candidate record-like units.

**Exit criterion:** entry grouping is evaluated independently of hierarchy.

## Phase 9 — Document lexer

Assign coarse role probabilities to logical entries.

Start deterministic/explicit. Progress only as justified:

```text
hand-designed scoring
  -> logistic regression
  -> gradient boosting
  -> small MLP
  -> transformer/GNN if evidence warrants it
```

**Exit criterion:** role classification has a standalone benchmark and error taxonomy.

## Phase 10 — Entry relation graph

Infer candidate structural relationships without immediately constructing a tree.

**Exit criterion:** relation precision/recall can be measured independently of final hierarchy.

## Phase 11 — Global solver

Use graph constraints, numerical consistency, repeated patterns, cross-page evidence, and contradiction penalties to select a coherent document structure.

Consider bounded beam search or another controlled ambiguity mechanism.

**Exit criterion:** global resolution improves hierarchy accuracy over greedy local decisions without losing provenance.

## Phase 12 — Bounded backtracking

Allow high-level contradictions to select alternative lower-level hypotheses.

Do not mutate original OCR observations.

**Exit criterion:** known ambiguous cases can be corrected by downstream evidence without reparsing the source from scratch.

## Evaluation by abstraction

Maintain separate metrics for:

- OCR/token quality;
- adjacency quality;
- run-boundary quality;
- anchor recovery;
- anchor membership;
- relative-transition stability;
- visual-line grouping;
- text-block grouping;
- logical-entry grouping;
- syntax classification;
- entry relations;
- final hierarchy;
- numerical consistency.

This separation is necessary to locate failures rather than reporting only end-to-end success/failure.

## First implementation target

The first code milestone ends after Phase 5 and includes a diagnostic viewer.

Do **not** implement hierarchy as part of the first prototype.
