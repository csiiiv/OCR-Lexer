# OCR-Lexer: A Hypothesis-Driven Spatial Lexer for Structured Document Reconstruction

## Abstract

OCR systems usually output words, bounding boxes, and confidence scores. Structured-document reconstruction then tries to convert these observations into lines, rows, tables, semantic entries, and hierarchy. A common implementation strategy performs this as a sequence of irreversible transformations: tokens are grouped into lines, lines become rows, rows receive semantic labels, and hierarchy is inferred from row order and indentation.

That approach is brittle because the abstractions are not naturally nested. A visual line can contain multiple logical fields. A logical text block can span several visual lines. A logical entry can contain multiple blocks and numeric fields. Page boundaries can cut through entries. Indentation can drift because of skew. OCR bounding boxes can move by several pixels even when the document's actual logical alignment is unchanged.

OCR-Lexer treats the page differently. OCR tokens are immutable observations. Spatial relations, visual lines, fields, blocks, entries, semantic classes, entry relationships, and hierarchy are progressively higher-level hypotheses. Multiple interpretations may coexist until enough context exists to resolve them. The architecture combines sparse two-dimensional adjacency, relative spatial anchors, overlapping layout projections, coarse semantic classification, relation scoring, global constraints, contradiction handling, and provenance.

The central design principle is:

> Tokens are observations. Structure is an explanation of those observations.

## 1. Motivation

Structured documents encode meaning through both visible content and whitespace. A heading, table row, continuation line, child item, subtotal, or footer may be distinguishable not only by words but by indentation, alignment, vertical gaps, amount columns, repeated anchors, and position relative to neighboring structures.

This makes document reconstruction more similar to parsing than to plain OCR cleanup. However, unlike source code, most document syntax is not represented by explicit punctuation. The equivalent of delimiters such as braces, commas, or indentation tokens is often latent in geometry.

A useful conceptual analogy is a lexer. A conventional lexer converts a character stream into symbolic tokens. OCR-Lexer converts a noisy two-dimensional token field into a richer symbolic representation of spatial and semantic evidence.

The analogy must not be taken too literally. Source code is primarily one-dimensional and has explicit lexical rules. Documents are two-dimensional, noisy, partially ordered, and often ambiguous. OCR-Lexer therefore uses contextual classification and hypothesis graphs rather than a single deterministic token stream.

## 2. Failure of the conventional pipeline

A conventional pipeline often resembles:

```text
OCR
  -> line grouping
  -> row detection
  -> row classification
  -> hierarchy
```

This implies several assumptions that routinely fail:

```text
OCR line = visual line
visual line = table row
row = logical entry
logical entry = hierarchy node
```

Consider a description that wraps across three physical lines while numeric amounts occur only on the middle line. A visual-line-first row parser must either split one logical entry into several rows or absorb the numeric fields into a text block. Both are artifacts of forcing one partition to serve multiple roles.

The architecture therefore separates distinct questions:

1. Which tokens are locally related in two-dimensional space?
2. Which tokens plausibly share a physical baseline?
3. Which token subsets form coherent text fragments or fields?
4. Which fragments jointly form one logical entry?
5. What semantic role does that entry play?
6. How does it relate to neighboring entries?
7. What global hierarchy best explains the relationship graph?

Each question introduces a new level of interpretation.

## 3. Observation versus interpretation

The lowest layer consists of immutable OCR observations:

- source page;
- raw text;
- normalized text preview;
- bounding polygon or box;
- OCR confidence;
- optional rotation and visual measurements;
- stable source identifiers.

The OCR token must never be rewritten to match later structure. Corrections and normalizations are represented as derived operations with provenance.

Higher layers are explicitly hypotheses:

- same-baseline hypothesis;
- column-alignment hypothesis;
- logical-anchor hypothesis;
- text-block hypothesis;
- numeric-field hypothesis;
- logical-entry hypothesis;
- entry-class hypothesis;
- parent/continuation/total relationship hypothesis;
- final document-node selection.

This distinction enables local errors to remain recoverable. A mistaken visual-line assignment does not necessarily prevent a correct text block if block formation can still operate on the original token set.

## 4. Two-dimensional relation graph

OCR tokens form the vertices of a sparse spatial graph.

For each token, the system generates only plausible nearby candidates using structures such as spatial buckets, sweep-line indexes, k-nearest neighbors, or directional nearest-neighbor searches.

Candidate edges retain measured evidence such as:

- horizontal and vertical displacement;
- horizontal and vertical gap;
- x/y overlap ratios;
- height compatibility;
- relative width;
- baseline residual;
- left- and right-edge alignment;
- local token density.

The graph must remain sparse. Global O(n^2) token comparisons are unnecessary and would obscure locality.

The first relation vocabulary should remain geometric rather than semantic:

- LEFT_OF;
- RIGHT_OF;
- ABOVE;
- BELOW;
- SAME_BASELINE;
- SAME_LEFT_ANCHOR;
- SAME_RIGHT_ANCHOR;
- LOCAL_NEIGHBOR;
- UNRELATED.

## 5. Negative space as evidence

Whitespace is not an absence of information. It often carries syntax.

Examples include:

- indentation between structural levels;
- gaps separating labels from numeric fields;
- large vertical gaps separating sections;
- repeated right alignment defining amount columns;
- page margins defining recurring artifact zones;
- continuation-line indentation.

Raw gaps should be retained as measurements, but downstream logic should not repeatedly reason over absolute pixel values alone. OCR box noise, DPI changes, page translation, and skew make absolute values unstable.

The system therefore normalizes spatial measurements and derives symbolic interpretations from them.

## 6. Logical spatial anchors

The preferred abstraction is not absolute coordinate quantization. It is a latent logical anchor.

An anchor represents a recurring geometric reference supported by multiple observations. A left-text anchor, for example, can initially be modeled as a skew-aware line:

\[
x_A(y) = a + by
\]

where `b` captures page skew or drift.

For an object observed at `(x, y)`, its residual to anchor `A` is:

\[
r_A = x - x_A(y)
\]

The residual is normalized by local text scale before membership is scored.

This representation is more stable than absolute clustering. Several observations whose raw x positions drift down a skewed page may all have near-zero residual to the same anchor.

Anchors are local hypotheses, not semantic hierarchy levels. A sequence of anchors A0, A1, A2 does not mean Department, Program, Region. It means only that repeated left-alignment modes exist and have an ordinal relationship.

## 7. Relative spatial symbolization

Once anchors are inferred, downstream stages should primarily consume relative transitions rather than raw anchor coordinates.

Candidate symbols include:

- SAME_ANCHOR;
- STEP_RIGHT;
- STEP_LEFT;
- SKIP_RIGHT;
- SKIP_LEFT;
- SAME_NUMERIC_ANCHOR;
- NEXT_NUMERIC_ANCHOR;
- NORMAL_VERTICAL_STEP;
- LARGE_VERTICAL_STEP;
- UNRESOLVED.

A later syntax layer may interpret STEP_RIGHT as an indentation event, but the spatial layer should not embed that semantic assumption.

The strongest representation keeps three levels simultaneously:

1. raw measurement;
2. normalized measurement;
3. relative symbolic interpretation with score or membership.

No earlier representation is discarded.

## 8. Soft membership and ambiguity

Anchor assignment should be soft when evidence is weak. An object near two anchors may retain competing memberships rather than being forced into one bin.

For example:

```text
A2 membership = 0.58
A3 membership = 0.42
```

This can yield competing transition scores such as:

```text
SAME       0.38
STEP_RIGHT 0.55
OTHER      0.07
```

Higher-level evidence can resolve the ambiguity later.

The same principle applies throughout the parser. Block, entry, class, and relationship alternatives should survive until their resolving context is available.

## 9. Overlapping layout projections

Visual lines and text blocks are not nested abstractions.

A visual line is a geometric hypothesis about a shared physical baseline. A text block is a semantic or textual hypothesis about fragments that belong together. A visual line may contain description text and several amount fields. A text block may span multiple visual lines.

Therefore the system should derive several overlapping projections from the same token graph:

- baseline or visual-line hypotheses;
- left/right anchor hypotheses;
- column hypotheses;
- numeric-field hypotheses;
- indentation modes;
- local region hypotheses;
- text-fragment hypotheses.

These projections provide evidence to block and entry construction but are not strict parent-child layers.

## 10. Logical text blocks

A text block is a hypothesis that one or more token fragments form one coherent textual expression.

Candidate continuation evidence can include:

- compatible left-anchor membership;
- small vertical step;
- absence or presence of competing numeric fields;
- local region consistency;
- punctuation;
- capitalization;
- hyphenation;
- lexical continuation;
- neighboring repeated patterns.

The authoritative membership of a text block is its token set. Visual-line membership is supporting evidence only.

Text normalization operations such as whitespace joining, dehyphenation, or OCR spelling correction must preserve source-token provenance.

## 11. Logical entries

The term `logical entry` is preferred over `row`.

A logical entry is a candidate record or structural unit composed from text blocks and fields. It may span several visual lines and need not correspond to a rectangular table row.

A candidate entry may include:

- description block;
- code field;
- PS amount;
- MOOE amount;
- CO amount;
- total amount;
- marker or sequence field;
- source token set;
- supporting anchor transitions;
- local evidence decomposition.

Entry construction should remain independent from hierarchy assignment.

## 12. Document lexer

Once logical entries exist, a document lexer assigns broad semantic roles.

A generic vocabulary may include:

- STRUCTURAL;
- DETAIL;
- TOTAL;
- HEADER;
- COLUMN_HEADER;
- PROSE;
- FOOTNOTE;
- PAGE_ARTIFACT;
- SEPARATOR;
- UNKNOWN.

The classifier may initially be heuristic and later replaced by logistic regression, gradient boosting, a small neural model, or graph/transformer methods. The interface should remain stable so scoring implementations are replaceable.

Domain-specific types should be introduced by an adapter. For a budget document, generic STRUCTURAL entries might later refine into Department, Agency, Program, Region, or Operating Unit. Such concepts must not leak into generic spatial inference.

## 13. Entry relationship graph

Classification answers what an entry is. Relationship inference answers how entries relate.

Candidate relations include:

- PARENT_OF;
- CHILD_OF;
- SIBLING_OF;
- CONTINUATION_OF;
- TOTAL_OF;
- HEADER_FOR;
- NEXT_ENTRY;
- UNRELATED.

The relation scorer does not build the final document tree. It supplies candidate edges and evidence to a later global solver.

Candidate generation should prioritize recall while remaining bounded to plausible neighborhoods: recent preceding entries, open structural candidates, similar anchors, nearby totals, and cross-page continuation candidates.

## 14. Global hierarchy resolution

The final hierarchy is the globally most consistent interpretation of selected entries and relationships.

A conceptual objective is:

\[
S(T)=w_eS_e+w_rS_r+w_aS_a+w_nS_n+w_pS_p+w_cS_c-P
\]

where terms may represent:

- entry confidence;
- relation confidence;
- anchor/indent consistency;
- numeric consistency;
- repeated-pattern consistency;
- sequence/context consistency;
- contradiction penalties.

Constraints should usually be soft. Indentation, for example, is strong evidence but not an absolute hierarchy rule.

Numeric totals can be particularly valuable because they offer independent semantic evidence. If one parent assignment makes component totals consistent while another does not, arithmetic can resolve a spatial ambiguity.

## 15. Contradiction-directed backtracking

A global contradiction should reopen the narrowest relevant ambiguity rather than restarting the parser.

A practical order is:

```text
relationship alternative
    -> entry grouping alternative
        -> block grouping alternative
```

Only when necessary should earlier geometric hypotheses be reconsidered.

This requires hypotheses to remain immutable and parse states to select among alternatives instead of rewriting earlier outputs.

## 16. Hypothesis DAG and provenance

Every derived hypothesis records:

- source token IDs;
- dependencies on lower-level hypotheses;
- evidence terms;
- aggregate score;
- status such as PROPOSED, SUPPORTED, SELECTED, REJECTED, or AMBIGUOUS;
- transformation operations.

Dependencies form a directed acyclic graph. Competing hypotheses may share the same source observations.

Every final AST node must be traceable back to the exact OCR tokens that support it.

## 17. Page boundaries

A page boundary is a rendering boundary, not necessarily a semantic boundary.

Cross-page inference should compare relative anchor structure, repeated fields, open entry state, and semantic patterns rather than absolute coordinates. Two pages can have translated or skewed layouts yet share equivalent anchor graphs.

This turns page stitching partly into a local graph-alignment problem.

## 18. Evaluation

Each layer must be independently evaluable.

Recommended metrics include:

- same-baseline pairwise precision/recall;
- anchor recovery and anchor-membership accuracy;
- relative-transition accuracy;
- block token-membership precision/recall/F1;
- entry field-assignment accuracy;
- numeric parsing accuracy;
- entry-class accuracy;
- parent relationship accuracy;
- ancestor accuracy;
- subtree exact match;
- tree edit distance.

Failure analysis should identify the earliest layer where the correct hypothesis disappeared. This is more useful than observing only that the final hierarchy was wrong.

## 19. Implementation strategy

The project should begin with deterministic and inspectable methods:

```text
hand-designed score
    -> logistic regression
    -> gradient boosting
    -> small MLP
    -> transformer/GNN only if justified
```

The first prototype should stop at relative spatial symbolization. It should test whether logical anchors actually improve invariance under skew, OCR jitter, page translation, and varying whitespace.

Only after that representation is validated should the parser proceed to text blocks and logical entries.

## 20. Core invariants

1. Raw OCR evidence is immutable.
2. Every interpretation has provenance.
3. A visual line is geometric, not semantic.
4. Text blocks operate on token subsets, not mandatory whole visual lines.
5. Visual lines and text blocks may intersect without nesting.
6. Logical entries are not synonymous with physical rows.
7. Entry classification does not assign hierarchy.
8. Relationship scoring does not itself construct the final tree.
9. Global constraints may reject locally strong hypotheses.
10. Backtracking selects alternatives instead of rewriting evidence.
11. Page boundaries are layout boundaries, not semantic prohibitions.
12. Domain-specific semantics do not leak into generic spatial inference.
13. Absolute coordinates remain measurements, not logical levels.
14. Spatial symbolization is derived primarily from relative logical anchors.

## Conclusion

OCR-Lexer models structured-document reconstruction as inference over a noisy two-dimensional token field. Tokens are observations; spatial relations and logical anchors provide geometric evidence; lines, blocks, and entries are competing interpretations; semantic classes provide document roles; entry relationships provide structural possibilities; and the final hierarchy is the globally most consistent explanation of the original evidence.

The architecture deliberately resists irreversible simplification. Its purpose is not to make uncertainty disappear early, but to preserve enough evidence that later context can resolve it correctly.
