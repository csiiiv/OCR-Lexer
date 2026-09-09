# OCR-Lexer Architecture

## 1. Thesis

OCR-Lexer treats document reconstruction as inference over a noisy two-dimensional token field.

The canonical observations are OCR tokens and measured geometry. Constructs such as visual lines, text blocks, logical rows, document roles, parent-child relations, and hierarchy are interpretations and must not be treated as ground truth merely because they are convenient intermediate representations.

> Tokens are observations; spatial relations are measurements and hypotheses; lines, blocks, and entries are competing interpretations; syntax provides semantic roles; relationships provide structural possibilities; and the final hierarchy is the globally most consistent explanation of the original token field.

## 2. Why a conventional pipeline is brittle

A conventional document parser often assumes:

```text
OCR -> lines -> rows -> classification -> hierarchy
```

This prematurely assumes that a row can be defined before the parser understands the document. In real structured documents:

- one logical entry may span multiple visual lines;
- one visual line may contain several logical fields;
- wrapped text may change indentation;
- amounts may occur on only one line of a multiline description;
- page boundaries may split a logical entry or hierarchy;
- OCR boxes drift due to skew, rotation, cropping, and recognition noise.

Therefore `VisualLine` and `TextBlock` are not necessarily nested concepts. They are different projections over the same observations.

## 3. Representation levels

```text
Level 0  OCR observations
Level 1  local spatial measurements and candidate adjacency
Level 2  logical spatial-anchor hypotheses
Level 3  relative spatial symbols and geometric projections
Level 4  logical text/field hypotheses
Level 5  logical entry hypotheses
Level 6  document-syntax classification
Level 7  entry-relationship hypotheses
Level 8  global document hierarchy
```

These levels describe increasing interpretation, not a requirement for irreversible feed-forward processing.

## 4. Observation layer

An OCR token should remain immutable once ingested.

```python
@dataclass(frozen=True)
class OCRToken:
    id: int
    text: str
    confidence: float
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    rotation: float | None
    source_engine: str | None
```

Measured features such as height, width, estimated orientation, stroke weight, or OCR confidence are observations. Labels such as `header`, `row`, `child`, or `continuation` are not.

## 5. Local spatial evidence

Before semantic grouping, construct sparse candidate relationships among nearby observations.

Possible measured features include:

- horizontal and vertical separation;
- x/y overlap;
- baseline residual;
- height and width ratios;
- local orientation difference;
- normalized distance;
- candidate left/right neighbor relation;
- candidate above/below relation.

The purpose is not to decide which tokens form rows. It is to determine which observations are worth comparing.

## 6. Logical spatial anchors

Absolute coordinate quantization is deliberately avoided as the primary structural representation. Absolute x/y positions are sensitive to translation, crop, DPI, OCR box noise, and skew.

Instead OCR-Lexer infers **logical spatial anchors**: latent geometric references supported by recurring local observations.

For a left alignment anchor, an initial model may be a skew-aware trajectory:

```text
x_A(y) = intercept + slope * y
```

A token or fragment is represented by its residual from the candidate anchor rather than by absolute x alone:

```text
residual = observed_x - x_A(y)
```

Anchor membership is soft and may remain ambiguous.

Anchors are not semantic hierarchy levels. `A2` must never automatically mean `Program`, `Region`, or hierarchy depth 2.

See [LOGICAL_ANCHORS.md](LOGICAL_ANCHORS.md).

## 7. Relative spatial symbolization

Once anchor hypotheses exist, downstream stages should preferentially consume relative relations such as:

```text
SAME_ANCHOR
STEP_RIGHT
STEP_LEFT
SKIP_RIGHT
SKIP_LEFT
SAME_NUMERIC_ANCHOR
NEXT_NUMERIC_ANCHOR
SAME_BASELINE
NORMAL_VERTICAL_STEP
LARGE_VERTICAL_STEP
```

Internally, `STEP_RIGHT` and `STEP_LEFT` are preferred over `INDENT` and `DEDENT` because the latter already imply document syntax. A later semantic layer may interpret a rightward transition as an indent.

Raw and normalized geometry remain available alongside these symbols.

## 8. Negative space as evidence

Whitespace is not merely absence of OCR tokens. It often acts as latent document punctuation.

Examples:

- recurring left alignment -> structural anchor;
- large horizontal separation before a right-aligned number -> field boundary;
- repeated amount right edges -> numeric column anchors;
- increased vertical gap -> possible block or section boundary;
- transition to a rightward logical anchor -> possible nested structure;
- return to a previous anchor -> possible structural closure.

The parser therefore models positive-space and negative-space evidence together.

## 9. Multiple geometric projections

From the same token/anchor graph, construct overlapping hypotheses:

- visual baseline/line hypotheses;
- left/right alignment hypotheses;
- numeric-column hypotheses;
- local region hypotheses;
- text-run hypotheses;
- vertical-gap modes.

No projection is automatically authoritative.

A visual line is a geometric hypothesis: tokens appear to share a writing baseline.

A text block is a logical hypothesis: fragments form one coherent textual unit.

A block may span several visual lines, while a visual line may contain several blocks or fields.

## 10. Text-block hypotheses

Text-block formation may use evidence from several context levels:

- token geometry and OCR confidence;
- local adjacency;
- anchor membership and anchor transitions;
- continuation indentation;
- punctuation and lexical continuity;
- local column boundaries;
- repeated page/document patterns.

The authoritative provenance remains the source token IDs, not a flattened line string.

## 11. Logical entries

A logical entry is a candidate set of textual and value-bearing components that jointly describe one document record or structural unit.

`LogicalEntry` is preferred to `Row` because the source representation may span multiple visual rows or use only part of a visual line.

An entry may contain:

- one or more text blocks;
- zero or more numeric fields;
- several visual-line fragments;
- continuation fragments;
- explicit provenance to all source tokens.

## 12. Document lexer

The document lexer operates after enough grouping exists to form candidate logical entries.

It assigns coarse role probabilities, for example:

```text
STRUCTURAL_LABEL
DETAIL_ENTRY
AMOUNT_ENTRY
TOTAL
HEADER
COLUMN_HEADER
PROSE
FOOTNOTE
PAGE_ARTIFACT
SEPARATOR
UNKNOWN
```

Domain-specific roles should be layered later rather than embedded in the generic lexer.

## 13. Entry relation graph

Classification is distinct from relationship inference.

Candidate relations may include:

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

The output is a graph of possibilities, not immediately a tree.

## 14. Global hierarchy resolution

The final hierarchy is selected by global consistency rather than a greedy local decision.

Conceptually:

```text
T* = argmax_T S(T)
```

where scoring may combine:

- entry confidence;
- relation confidence;
- anchor/indent consistency;
- sequence consistency;
- numeric consistency;
- repeated-pattern consistency;
- cross-page continuity;
- contradiction penalties.

Numerical totals, repeated structures, and downstream semantic constraints can therefore disambiguate earlier grouping decisions.

## 15. Progressive context

Decisions should consume only the context justified by their semantic level:

```text
C0 token       bbox, text, OCR confidence, rotation
C1 local       neighbors, gaps, overlaps, baseline evidence
C2 regional    anchors, columns, indentation modes, local blocks
C3 page        headers, dominant columns, repeated page structure
C4 document    adjacent pages, recurring labels, cross-page continuity
C5 semantic    candidate hierarchy, arithmetic, structural contradictions
```

The amount of context consumed should match the abstraction level of the decision.

## 16. Hypothesis graph

The architecture can be represented as a provenance-preserving hypothesis DAG:

```text
OCRToken
  -> SpatialRelation
  -> AnchorHypothesis / BaselineHypothesis / ColumnHypothesis
  -> TextBlockHypothesis
  -> LogicalEntryHypothesis
  -> EntryClassHypothesis
  -> EntryRelationHypothesis
  -> HierarchyHypothesis
```

A hypothesis should retain:

- source evidence;
- decomposed evidence scores;
- dependencies;
- competing hypotheses;
- confidence;
- status such as `PROPOSED`, `SUPPORTED`, `SELECTED`, `REJECTED`, or `AMBIGUOUS`.

## 17. Preserve ambiguity

When two plausible groupings exist, retain both until sufficient context is available.

Example:

```text
A: General Administration
B: and Support
C: 12,000

Candidate 1: [A + B + C]
Candidate 2: [A] [B + C]
```

Later evidence such as anchor transitions, amount-column patterns, surrounding entries, or arithmetic constraints may resolve the ambiguity.

This is preferable to allowing an early line/row heuristic to irreversibly poison every later stage.

## 18. Probabilistic interpretation

Let:

```text
O = OCR observations
A = anchor/layout hypotheses
B = text-block hypotheses
E = logical-entry hypotheses
C = entry classifications
R = entry relationships
T = hierarchy
```

The conceptual objective is:

```text
P(T, R, C, E, B, A | O)
```

Exact joint inference is not required. Practical implementations may use beam search, staged reranking, dynamic programming, graph optimization, or constraint programming.

The architectural requirement is simply that uncertainty is not collapsed before the evidence required to resolve it exists.

## 19. Domain separation

The generic OCR-Lexer core should model:

```text
OCRToken
SpatialGraph
AnchorHypothesis
VisualLineHypothesis
ColumnHypothesis
TextBlockHypothesis
LogicalEntryHypothesis
EntryClass
EntryRelation
```

A domain adapter can later introduce concepts such as:

```text
Department
Agency
Program
Region
OperatingUnit
PS
MOOE
CO
TOTAL
```

This keeps the core useful beyond a single government-budget layout.

## 20. Immediate boundary

The next implementation work should stop at anchor inference and relative spatial symbolization. Logical entries and hierarchy should not be implemented until this representation has been evaluated against difficult pages.
