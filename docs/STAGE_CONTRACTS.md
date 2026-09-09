# Stage Contracts

A stage contract states what a layer may consume, what it may produce, and—most importantly—what it must not assume.

Core rule:

> A later abstraction may use earlier evidence, but an earlier abstraction must not depend on a concept that has only been defined at a later semantic level.

## 0. OCR Observation

**Requires:** source OCR output.

**Produces:** immutable tokens, boxes/polygons, page identity, confidence, measured visual properties.

**Must not assume:** reading order, lines, rows, blocks, hierarchy, semantic role.

## 1. Local Spatial Measurement / Adjacency

**Requires:** OCR observations.

**Produces:** sparse candidate neighbors and measured geometric features such as gap, overlap, relative orientation, baseline residual, and normalized distance.

**May use:** spatial indexes, k-nearest candidates, sweep-line searches, bounding-box intersection tests.

**Must not assume:** finalized lines, rows, text blocks, semantic hierarchy.

## 2. Candidate Run Boundaries

**Requires:** tokens and local horizontal adjacency evidence.

**Produces:** hypotheses that a token plausibly starts or ends a local horizontal text run.

**May use:** absence/presence of plausible left/right neighbors, local gap evidence, baseline compatibility.

**Must not assume:** a complete or correct visual-line segmentation.

## 3. Logical Anchor Discovery

**Requires:** candidate run boundaries and local geometry.

**Produces:** skew-aware anchor hypotheses, support observations, residual scales, anchor topology.

**May use:** robust regression, RANSAC, local normalization, recurring alignment evidence.

**Must not assume:** that an anchor corresponds to a hierarchy depth or semantic type.

## 4. Anchor Membership / Relative Spatial Symbols

**Requires:** anchor hypotheses and candidate objects.

**Produces:** soft anchor memberships and relative transitions such as `SAME`, `STEP_RIGHT`, `STEP_LEFT`, `SKIP_RIGHT`, `SKIP_LEFT`.

**Must retain:** raw and normalized geometry.

**Must not assume:** that `STEP_RIGHT` means child or that `STEP_LEFT` means parent closure.

## 5. Geometric Projection Hypotheses

Examples include visual lines, columns, numeric columns, local regions, and vertical-gap modes.

**Requires:** OCR observations, adjacency, anchors, relative spatial symbols.

**Produces:** overlapping geometric groupings.

**Must not assume:** that any one projection is the authoritative document segmentation.

## 6. Text-Block Hypotheses

**Requires:** source tokens plus any useful geometric projections.

**Produces:** candidate coherent textual units with provenance and confidence.

**May use:** geometry, anchors, lexical continuity, punctuation, hyphenation, regional context, page context.

**Must not assume:** hierarchy or parent assignment.

## 7. Logical-Entry Hypotheses

**Requires:** text blocks, value/field hypotheses, source geometry.

**Produces:** candidate record-like units that may span multiple visual lines or partial lines.

**Must not assume:** hierarchy.

## 8. Document Syntax Classification

**Requires:** logical entries and contextual evidence.

**Produces:** coarse role probabilities such as structural label, detail, amount entry, total, header, prose, footnote, artifact, unknown.

**Must not assign:** parent-child relationships merely from class labels.

## 9. Entry Relationship Inference

**Requires:** logical entries, classifications, layout evidence, sequence and document context.

**Produces:** scored candidate relations such as parent, sibling, continuation, total-of, header-for, next-entry, unrelated.

**Must not assume:** that the candidate graph is already a tree.

## 10. Global Hierarchy Solver

**Requires:** entry hypotheses, relation graph, constraints, provenance.

**Produces:** globally consistent selected hierarchy/document AST plus unresolved ambiguity where necessary.

**May use:** numerical consistency, repeated structure, cross-page continuity, contradiction penalties, beam search or other global search.

**Must preserve:** traceability from selected nodes back to all source observations and hypotheses.

## Backward influence

The contracts define conceptual prerequisites, not a prohibition on reconsideration.

A global contradiction may reduce the score of an entry hypothesis, which may in turn favor another block grouping. The original observations are never mutated. Higher-level evidence changes hypothesis selection, not historical measurements.
