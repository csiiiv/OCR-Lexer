# Data Model and Interface Contracts

This document defines the first implementation-facing data contracts for OCR-Lexer. The structures are intentionally conservative: raw OCR observations are immutable, derived geometry is explicit, and every interpretive object carries provenance.

## 1. Canonical OCR token

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


@dataclass(frozen=True)
class OCRToken:
    id: str
    page_id: int
    text_raw: str
    text_normalized: str
    bbox: BBox
    confidence: float
    rotation_deg: float | None = None
    source_index: int | None = None
```

### Invariants

- `OCRToken` is immutable after ingestion.
- Raw OCR text is never overwritten by normalization or correction.
- `bbox` remains the reported OCR geometry; deskewing and normalized coordinates are derived measurements.
- Stable token IDs must survive every downstream stage.

## 2. Normalized geometry

```python
@dataclass(frozen=True)
class NormalizedBBox:
    x0: float
    y0: float
    x1: float
    y1: float
```

Normalized coordinates use page width and height:

```text
x_n = x / page_width
y_n = y / page_height
```

Raw and normalized coordinates are both retained.

## 3. Spatial measurement

```python
@dataclass(frozen=True)
class SpatialMeasurement:
    raw: float
    normalized: float
    unit: str
    normalization: str
```

Examples include horizontal gap, vertical gap, baseline residual, and distance to anchor trajectory.

## 4. Local spatial edge

```python
from enum import Enum, auto

class SpatialRelation(Enum):
    LEFT_OF = auto()
    RIGHT_OF = auto()
    ABOVE = auto()
    BELOW = auto()
    SAME_BASELINE = auto()
    SAME_LEFT_ANCHOR = auto()
    SAME_RIGHT_ANCHOR = auto()
    LOCAL_NEIGHBOR = auto()
    UNRELATED = auto()


@dataclass(frozen=True)
class SpatialEdge:
    source_id: str
    target_id: str
    dx: SpatialMeasurement
    dy: SpatialMeasurement
    horizontal_gap: SpatialMeasurement
    vertical_gap: SpatialMeasurement
    x_overlap_ratio: float
    y_overlap_ratio: float
    height_ratio: float
    baseline_delta: SpatialMeasurement
    relation_scores: dict[str, float]
```

`relation_scores` are scores unless explicitly calibrated. They must not be called probabilities by default.

## 5. Candidate run boundary

Anchor discovery should not require finalized visual lines. Instead, it may consume weak local evidence that a token or fragment is a plausible start or end of a horizontal run.

```python
@dataclass(frozen=True)
class RunBoundaryCandidate:
    object_id: str
    boundary: str  # START | END
    score: float
    evidence: dict[str, float]
    source_token_ids: tuple[str, ...]
```

This object deliberately makes no claim that the entire run or visual line has already been reconstructed.

## 6. Logical spatial anchor

```python
class AnchorKind(Enum):
    LEFT_TEXT = auto()
    RIGHT_TEXT = auto()
    RIGHT_NUMERIC = auto()
    DECIMAL = auto()
    BASELINE = auto()


@dataclass(frozen=True)
class SpatialAnchorHypothesis:
    id: str
    page_id: int
    kind: AnchorKind
    intercept: float
    slope: float
    residual_scale: float
    support_object_ids: tuple[str, ...]
    score: float
    evidence: dict[str, float]
```

The initial trajectory model is linear:

```text
x(y) = intercept + slope * y
```

A future implementation may replace the trajectory model while preserving the anchor interface.

### Anchor invariants

- An anchor is not a semantic hierarchy level.
- Anchor IDs are local identifiers, not stable semantic names.
- Absolute x is measured evidence, not an ordinal level.
- A skew-aware anchor may drift across y.

## 7. Anchor membership

```python
@dataclass(frozen=True)
class AnchorMembership:
    object_id: str
    anchor_id: str
    residual: float
    normalized_residual: float
    score: float
    evidence: dict[str, float]
```

Multiple memberships may coexist for one object.

## 8. Anchor graph

Anchors may have ordinal spatial relationships.

```python
class AnchorRelation(Enum):
    SAME = auto()
    STEP_RIGHT = auto()
    STEP_LEFT = auto()
    SKIP_RIGHT = auto()
    SKIP_LEFT = auto()
    UNRESOLVED = auto()


@dataclass(frozen=True)
class AnchorGraphEdge:
    source_anchor_id: str
    target_anchor_id: str
    relation: AnchorRelation
    score: float
    evidence: dict[str, float]
```

The graph captures topology rather than semantic hierarchy.

## 9. Relative spatial transition

```python
@dataclass(frozen=True)
class SpatialTransition:
    source_object_id: str
    target_object_id: str
    relation_scores: dict[str, float]
    evidence: dict[str, float]
```

Expected early relation vocabulary:

- SAME_ANCHOR
- STEP_RIGHT
- STEP_LEFT
- SKIP_RIGHT
- SKIP_LEFT
- SAME_NUMERIC_ANCHOR
- NEXT_NUMERIC_ANCHOR
- NORMAL_VERTICAL_STEP
- LARGE_VERTICAL_STEP
- UNRESOLVED

## 10. Generic hypothesis base

```python
class HypothesisStatus(Enum):
    PROPOSED = auto()
    SUPPORTED = auto()
    SELECTED = auto()
    REJECTED = auto()
    AMBIGUOUS = auto()


@dataclass(frozen=True)
class Evidence:
    name: str
    value: float | str | bool | None
    contribution: float | None
    source_ids: tuple[str, ...]
    description: str | None = None


@dataclass(frozen=True)
class Provenance:
    token_ids: tuple[str, ...]
    hypothesis_ids: tuple[str, ...]
    operations: tuple[str, ...]


@dataclass(frozen=True)
class HypothesisMeta:
    id: str
    score: float
    status: HypothesisStatus
    evidence: tuple[Evidence, ...]
    provenance: Provenance
```

## 11. Visual-line hypothesis

```python
@dataclass(frozen=True)
class VisualLineHypothesis:
    meta: HypothesisMeta
    token_ids: tuple[str, ...]
    baseline_intercept: float
    baseline_slope: float
```

A visual line is geometric only. It does not imply row or semantic entry identity.

## 12. Text-block hypothesis

```python
@dataclass(frozen=True)
class TextBlockHypothesis:
    meta: HypothesisMeta
    token_ids: tuple[str, ...]
    fragment_ids: tuple[str, ...]
    supporting_line_ids: tuple[str, ...]
    reconstructed_text: str
```

The token set is authoritative. `supporting_line_ids` is evidence only. A block may consume a subset of tokens from a visual line.

## 13. Numeric and field hypotheses

```python
@dataclass(frozen=True)
class NumericValue:
    raw_text: str
    parsed_value: float | int | None
    confidence: float
    token_ids: tuple[str, ...]


@dataclass(frozen=True)
class FieldHypothesis:
    meta: HypothesisMeta
    token_ids: tuple[str, ...]
    kind_scores: dict[str, float]
    numeric_value: NumericValue | None
    anchor_ids: tuple[str, ...]
```

Possible generic numeric field kinds include:

- AMOUNT
- COUNT
- PERCENTAGE
- CODE
- DATE
- UNKNOWN_NUMERIC

## 14. Logical entry hypothesis

```python
@dataclass(frozen=True)
class LogicalEntryHypothesis:
    meta: HypothesisMeta
    block_ids: tuple[str, ...]
    field_ids: tuple[str, ...]
    token_ids: tuple[str, ...]
    class_scores: dict[str, float] | None = None
```

A logical entry is a candidate record or structural unit, not necessarily a visual row.

## 15. Entry classification

Generic classes:

```text
STRUCTURAL
DETAIL
TOTAL
HEADER
COLUMN_HEADER
PROSE
FOOTNOTE
PAGE_ARTIFACT
SEPARATOR
UNKNOWN
```

Domain adapters may refine these classes later.

## 16. Entry relation hypothesis

```python
@dataclass(frozen=True)
class EntryRelationHypothesis:
    meta: HypothesisMeta
    source_entry_id: str
    target_entry_id: str
    relation_scores: dict[str, float]
```

Initial relation vocabulary:

```text
PARENT_OF
CHILD_OF
SIBLING_OF
CONTINUATION_OF
TOTAL_OF
HEADER_FOR
NEXT_ENTRY
UNRELATED
```

## 17. Parse state

```python
@dataclass(frozen=True)
class ParseState:
    selected_entry_ids: tuple[str, ...]
    selected_relation_ids: tuple[str, ...]
    open_ancestor_ids: tuple[str, ...]
    score: float
    penalty_score: float
    contradiction_ids: tuple[str, ...]
```

Parse states select among immutable hypotheses.

## 18. Contradiction

```python
@dataclass(frozen=True)
class Contradiction:
    id: str
    kind: str
    hypothesis_ids: tuple[str, ...]
    severity: float
    explanation: str
    reopen_level: str | None
```

Recommended backtracking order:

```text
RELATION -> ENTRY -> BLOCK
```

## 19. Final document AST

```python
@dataclass(frozen=True)
class DocumentNode:
    id: str
    semantic_type: str
    entry_id: str | None
    parent_id: str | None
    child_ids: tuple[str, ...]
    attributes: dict[str, object]
    confidence: float
    provenance: Provenance
```

The AST is semantic. Rendering geometry remains available through provenance rather than being baked into the hierarchy itself.

## 20. Serialization strategy

Recommended stage artifacts:

```text
tokens.jsonl
spatial_edges.jsonl
run_boundaries.jsonl
anchors.jsonl
anchor_memberships.jsonl
anchor_graph.jsonl
spatial_transitions.jsonl
visual_line_hypotheses.jsonl
block_hypotheses.jsonl
field_hypotheses.jsonl
entry_hypotheses.jsonl
entry_classes.jsonl
entry_relations.jsonl
hierarchy.json
```

Every artifact should include parser version, configuration hash, model hash where applicable, input hash, and random seed when stochastic methods are used.

## 21. Determinism contract

For fixed input tokens, configuration, model weights, and seed, the same stage must produce byte-equivalent canonicalized output where practical.

Any nondeterministic accelerator behavior must be documented explicitly.
