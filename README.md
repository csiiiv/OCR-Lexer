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

## Documents

- [Architecture](docs/ARCHITECTURE.md)
- [Logical Spatial Anchors](docs/LOGICAL_ANCHORS.md)
- [Stage Contracts](docs/STAGE_CONTRACTS.md)
- [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)
- [ADR 0001 — Observation vs Interpretation](adr/0001-observation-vs-interpretation.md)
- [ADR 0002 — Relative Logical Spatial Anchors](adr/0002-relative-logical-spatial-anchors.md)
- [ADR 0003 — Preserve Competing Hypotheses](adr/0003-preserve-competing-hypotheses.md)

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

## Status

Architecture and experimental design phase.
