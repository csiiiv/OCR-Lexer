# Experiment Protocol: Logical Spatial Anchors

## Objective

Before OCR-Lexer proceeds to text blocks, logical entries, or hierarchy, the project must demonstrate that logical spatial anchors produce a more stable representation than direct absolute-coordinate grouping.

The initial experiment therefore asks one narrow question:

> Given OCR tokens from difficult pages, can skew-aware local anchor hypotheses recover stable relative spatial relationships despite OCR jitter, translation, spacing variation, and page skew?

## Competing methods

At minimum, compare:

### Baseline A — absolute x clustering

Cluster candidate left starts and numeric right edges directly in raw page coordinates.

### Baseline B — normalized x clustering

Cluster coordinates normalized by page width.

### Proposed method — logical anchor trajectories

Infer recurring anchor trajectories, initially using:

```text
x(y) = intercept + slope * y
```

and score observations by residual from the fitted trajectory.

The experiment must not assume the proposed method is better. Promotion requires measured improvement.

## Dataset composition

Create a bounded reviewed corpus containing approximately 20–30 pages initially, deliberately biased toward difficult cases:

- noticeable skew;
- mild local geometric drift;
- multiline descriptions;
- inconsistent indentation;
- multiple text columns;
- right-aligned numeric columns;
- sparse amount columns;
- headers and footers sharing similar x positions with body text;
- page transitions;
- examples where visually similar indentation has different semantic meaning;
- examples where semantically related entries have slightly different raw starts.

The first corpus should include both positive examples and adversarial controls.

## Annotation unit

The evaluation should avoid requiring final document semantics.

Annotators identify:

1. candidate horizontal run starts and ends;
2. visually recurring logical left anchors;
3. visually recurring numeric/right anchors;
4. anchor membership of selected objects;
5. relative transitions between selected neighboring objects.

Anchor labels are local to a page or region and must not use semantic names such as `PROGRAM_LEVEL`.

Recommended annotation identifiers:

```text
L0, L1, L2 ...
N0, N1, N2 ...
```

These identifiers are arbitrary local labels.

## Region policy

One page may contain multiple independent anchor systems. Annotators should mark local layout regions where forcing one global anchor graph would be misleading.

Examples:

```text
header region
main table region
secondary table region
footnote region
```

The experiment should evaluate both:

- page-wide anchor discovery;
- region-local anchor discovery.

This determines whether explicit region inference is required before reliable anchors.

## Candidate run-boundary experiment

Because finalized visual lines are not a prerequisite, first evaluate weak run-boundary detection.

A token or local fragment can be a candidate `START` when evidence includes:

- no strong same-baseline predecessor nearby;
- a large leftward whitespace boundary;
- strong overlap/alignment with nearby starts;
- local text geometry suggesting a new horizontal run.

Similarly, a candidate `END` may be supported by:

- no strong same-baseline successor;
- large rightward whitespace;
- recurring right alignment;
- numeric formatting.

Measure recall more heavily than precision initially. Missing a true run start can prevent anchor discovery; extra candidates can later be rejected by robust fitting.

## Anchor fitting methods to compare

Start with interpretable methods:

1. robust linear regression;
2. RANSAC line fitting;
3. Theil–Sen estimator;
4. simple clustering after global deskew correction.

Do not introduce a learned model until these baselines are measured.

## Anchor membership

For object `o` and anchor `A`:

```text
residual(o,A) = x_o - x_A(y_o)
```

Normalize residual using local scale, preferably robust local median token height:

```text
normalized_residual = residual / local_median_height
```

Membership scoring should retain at least the top two candidate anchors when margins are small.

## Relative transition labels

Initial transition vocabulary:

```text
SAME
STEP_RIGHT
STEP_LEFT
SKIP_RIGHT
SKIP_LEFT
UNRESOLVED
```

For numeric anchors:

```text
SAME_NUMERIC_ANCHOR
NEXT_NUMERIC_ANCHOR_RIGHT
NEXT_NUMERIC_ANCHOR_LEFT
UNRESOLVED
```

The transition evaluator should compare topology, not raw anchor IDs.

For example, if annotation uses `L2` and the algorithm calls the same physical anchor `A7`, that is not an error if graph alignment maps them consistently.

## Metrics

### Run-boundary metrics

- start-candidate recall;
- start-candidate precision;
- end-candidate recall;
- end-candidate precision.

### Anchor recovery

Use a bipartite match between predicted and annotated anchors based on supporting-object overlap and trajectory residual.

Report:

- anchor precision;
- anchor recall;
- anchor F1;
- mean normalized residual for matched anchors;
- unsupported/spurious anchor count.

### Membership

- top-1 anchor membership accuracy;
- top-2 coverage;
- mean reciprocal rank;
- ambiguous-case calibration by score margin.

### Relative transition

- SAME accuracy;
- STEP_RIGHT accuracy;
- STEP_LEFT accuracy;
- skip-transition accuracy;
- macro F1;
- confusion matrix.

### Stability tests

Apply controlled perturbations to the same token field:

- page x translation;
- page y translation;
- synthetic rotation/skew;
- random bbox jitter;
- mild scale change;
- selective token removal.

Compare how often the inferred relative transition sequence changes.

A major goal of logical anchors is invariance under transformations that should not change document syntax.

## Promotion criteria

Logical anchors may become a canonical upstream representation when:

1. relative-transition accuracy exceeds both absolute and normalized coordinate baselines on the reviewed difficult-page corpus;
2. synthetic x/y translation produces effectively no topology change;
3. mild skew causes substantially fewer transition errors than absolute clustering;
4. OCR bbox jitter near realistic magnitudes does not cause widespread anchor reassignment;
5. ambiguous memberships are surfaced rather than silently forced;
6. detected anchors remain inspectable in a visual overlay;
7. the algorithm does not require semantic row or hierarchy labels;
8. failures can be attributed to run-boundary generation, anchor fitting, membership, or topology separately.

No fixed numeric threshold is declared yet. Thresholds should be chosen after the first annotated baseline results are available.

## Diagnostic viewer requirements

The first implementation should render:

- source OCR tokens;
- candidate run starts/ends;
- fitted anchor trajectories;
- supporting objects per anchor;
- rejected outliers;
- top anchor memberships and scores;
- anchor graph edges;
- relative transitions.

Selecting an anchor should show:

```text
anchor id
kind
trajectory parameters
support count
support object ids
residual distribution
score
fitting method
configuration/version
```

Selecting an object should show its competing anchor memberships.

## Failure taxonomy

Every failure should be tagged at the earliest responsible stage:

```text
RB  run-boundary candidate missing/spurious
AF  anchor fitting failure
AM  anchor membership failure
AG  anchor graph/topology failure
ST  spatial transition failure
RG  region-context failure
OCR source token/bbox failure
```

This taxonomy prevents downstream symptoms from being mistaken for root causes.

## Expected first result

The first successful milestone is not a hierarchy tree.

It is a page overlay and artifact set where a human can inspect a noisy or skewed OCR token field and see that the system has reconstructed a stable relative spatial coordinate system without assigning document semantics.
