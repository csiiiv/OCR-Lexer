# OCR-Lexer

A research and implementation repository for reconstructing structured documents from OCR tokens using hypothesis-driven spatial reasoning.

The central idea is that OCR tokens are **observations**, while lines, blocks, rows, semantic roles, relationships, and hierarchy are progressively higher-level **hypotheses**.

OCR-Lexer is intentionally broader than a conventional OCR post-processor. It treats the page as a noisy two-dimensional token field and attempts to recover latent document syntax from both positive-space evidence (text, numbers, marks) and negative-space evidence (gaps, indentation, alignment, spacing, page structure).

## Core principle

> Do not collapse uncertainty before the information needed to resolve it exists.

The architecture therefore favors:

- immutable OCR observations;
- sparse local spatial relationships;
- logical spatial anchors rather than absolute x/y bins;
- relative spatial symbols such as `SAME_ANCHOR`, `STEP_RIGHT`, and `STEP_LEFT`;
- overlapping visual-line, column, block, and entry hypotheses;
- coarse document-role classification before hierarchy construction;
- an entry relation graph followed by global constraint resolution;
- end-to-end provenance from final document nodes back to source OCR tokens.

## High-level architecture

```text
OCR TOKENS
    |
    v
LOCAL SPATIAL MEASUREMENTS / ADJACENCY
    |
    v
LOGICAL SPATIAL ANCHORS
    |
    v
RELATIVE SPATIAL SYMBOLIZATION
    |
    +----------------------+----------------------+
    |                      |                      |
    v                      v                      v
VISUAL-LINE           COLUMN / FIELD         REGION / GAP
HYPOTHESES            HYPOTHESES             HYPOTHESES
    |                      |                      |
    +-----------+----------+----------+-----------+
                |                     |
                v                     v
          TEXT-BLOCK             VALUE/FIELD
          HYPOTHESES             HYPOTHESES
                \                     /
                 \                   /
                  v                 v
                  LOGICAL ENTRIES
                        |
                        v
                  DOCUMENT LEXER
                        |
                        v
                ENTRY RELATION GRAPH
                        |
                        v
              GLOBAL CONSTRAINT SOLVER
                        |
                        v
                   DOCUMENT AST
```

Arrows indicate evidence flow, not irreversible destructive transforms. Higher-level contradictions may cause selection of alternative lower-level hypotheses while preserving the underlying OCR observations.

## Core documents

- [Technical Paper](docs/TECHNICAL_PAPER.md) — consolidated rationale and full parser model
- [Architecture](docs/ARCHITECTURE.md) — system decomposition and evidence flow
- [Logical Spatial Anchors](docs/LOGICAL_ANCHORS.md) — skew-aware, relative anchor model
- [Data Model](docs/DATA_MODEL.md) — implementation-facing structures and serialization contracts
- [Stage Contracts](docs/STAGE_CONTRACTS.md) — prerequisites, outputs, and forbidden assumptions for each layer
- [Anchor Experiment Protocol](docs/EXPERIMENT_PROTOCOL.md) — baseline comparison, annotation, metrics, and promotion criteria
- [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md) — staged prototype plan

## Architecture decisions

- [ADR 0001 — Observation vs Interpretation](adr/0001-observation-vs-interpretation.md)
- [ADR 0002 — Relative Logical Spatial Anchors](adr/0002-relative-logical-spatial-anchors.md)
- [ADR 0003 — Preserve Competing Hypotheses](adr/0003-preserve-competing-hypotheses.md)
- [ADR 0004 — Anchor Graph Before Semantics](adr/0004-anchor-graph-before-semantics.md)

## Schemas

Initial machine-readable contracts live under [`schemas/`](schemas/):

- `ocr-token.schema.json`
- `spatial-anchor.schema.json`
- `anchor-membership.schema.json`

These are deliberately small first contracts. Additional schemas should be added only as their abstractions become stable enough to implement and test.

## Initial research target

The first implementation milestone deliberately stops before logical rows or hierarchy:

1. retain canonical OCR tokens;
2. derive sparse local spatial measurements;
3. detect candidate run starts/ends;
4. infer skew-aware logical anchor hypotheses;
5. assign soft anchor memberships;
6. derive relative anchor transitions;
7. visualize and evaluate the result on difficult pages.

Only after that representation is demonstrated to be stable should the parser move on to text blocks, logical entries, document syntax, and hierarchy.

The first experiment explicitly compares logical anchor trajectories against raw absolute-x and normalized-x clustering. The anchor abstraction is promoted only if it demonstrates better stability and transition accuracy on difficult pages.

## Status

Architecture and experimental design phase. The next implementation target is the bounded spatial-anchor prototype, not an end-to-end document parser.
