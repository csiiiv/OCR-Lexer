# ADR 0004 — Build the Anchor Graph Before Semantic Hierarchy

**Status:** Accepted

## Context

Absolute indentation levels are unstable under skew, page translation, OCR bounding-box noise, crop differences, and local layout changes. Mapping raw x coordinates directly to semantic hierarchy levels therefore creates a brittle coupling between geometry and meaning.

The project needs a representation that captures repeated alignment structure without prematurely deciding that a particular alignment means Program, Region, Operating Unit, child row, or any other domain-specific role.

## Decision

OCR-Lexer will infer a local logical anchor graph before semantic hierarchy is assigned.

The anchor graph represents recurring geometric reference structures and their relative topology. Its vocabulary is geometric:

```text
SAME
STEP_RIGHT
STEP_LEFT
SKIP_RIGHT
SKIP_LEFT
UNRESOLVED
```

Anchor identifiers are local and arbitrary. `A2` does not mean hierarchy level 2.

Semantic interpretation such as `INDENT`, `DEDENT`, parent-child structure, or domain-specific hierarchy is introduced only by later stages using the anchor graph together with textual, numeric, sequential, and document-level evidence.

## Consequences

### Positive

- geometry remains independent from domain semantics;
- skew and page translation can be absorbed by anchor trajectories;
- relative topology is more stable than absolute x bins;
- page-to-page comparison can align anchor graphs rather than raw coordinates;
- hierarchy errors do not require rewriting raw geometric evidence;
- the same spatial layer can support many document families.

### Costs

- anchor discovery becomes an explicit inference problem;
- local anchor systems may need region segmentation or graph alignment;
- ambiguous memberships must be represented and resolved later;
- downstream code cannot assume a simple integer `indent_level` field.

## Rejected alternative

### Quantize absolute x coordinates into indentation levels

Rejected because it makes layout noise and skew appear to be syntax changes and encourages downstream code to treat coordinate bins as semantic hierarchy levels.

## Implementation rule

If downstream code needs an indentation-like signal, it must derive it from relative anchor transitions or another explicitly documented higher-level interpretation. Generic spatial modules must not assign semantic hierarchy based solely on anchor index or raw coordinate.
