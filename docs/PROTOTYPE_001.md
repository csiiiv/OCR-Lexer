# Prototype 001 — Relative Spatial Anchors

## Scope

This prototype implements only the lowest bounded experiment described in the architecture:

```text
OCR tokens
  -> local directional neighbors
  -> weak run-boundary candidates
  -> skew-aware logical anchor hypotheses
  -> soft anchor memberships
  -> ordinal relative transitions
  -> JSON + SVG diagnostics
```

It deliberately does **not** implement visual-line finalization, text blocks, logical rows/entries, semantic classes, document hierarchy, or NEP-specific rules.

## Current algorithm

### Local adjacency

Tokens are indexed in coarse vertical buckets. Each token searches only nearby buckets for the nearest plausible left and right neighbor. Plausibility uses vertical overlap or normalized center-y distance plus a bounded horizontal gap.

The resulting edge means only "locally plausible horizontal neighbor." It does not mean "same finalized line."

### Candidate run boundaries

A token without a plausible left neighbor becomes a weak `START` observation. A token without a plausible right neighbor becomes an `END` observation. This intentionally over-generates boundaries at large field gaps; downstream anchor evidence is expected to separate recurring structural starts from incidental ones.

### Anchor discovery

The prototype currently:

1. estimates a shared page skew/drift from pairs that are plausibly on the same anchor;
2. projects run-start observations to a common reference y;
3. performs simple one-dimensional clustering only as a discovery bootstrap;
4. robustly fits each supported cluster as `x(y)` using a median pairwise slope and median intercept;
5. orders fitted anchors left-to-right locally.

Absolute coordinates are therefore used only for candidate discovery. Structural output is represented by fitted anchor membership and ordinal transitions.

### Soft membership

Each run start receives a normalized residual to every page-local anchor. A Gaussian-like score converts the residual to membership weight, normalized across candidate anchors. Ambiguous memberships are retained above a small threshold.

### Relative transitions

For consecutive run-start observations on a page, membership mass is propagated into:

- `SAME`
- `STEP_RIGHT`
- `STEP_LEFT`
- `SKIP_RIGHT`
- `SKIP_LEFT`
- `UNRESOLVED`

These are geometric symbols. They do not yet mean indent/dedent or parent/child.

## Tests in Prototype 001

The bounded tests currently verify:

1. candidate run starts can be recovered from local adjacency without a finalized visual-line structure;
2. two skewed anchors with bbox jitter are recovered and assigned correctly;
3. translating all x coordinates by a constant amount leaves the relative transition sequence unchanged.

The tested local snapshot passed all three tests before being committed.

## Diagnostic SVG

The CLI can render a lightweight SVG containing token boxes, run-start points, and fitted anchor trajectories. This is not a replacement for raster/PDF overlay; it is an initial inspection surface intended to expose incorrect anchor fitting quickly.

## CLI

```bash
pip install -e '.[dev]'
ocr-lexer anchors tokens.jsonl -o anchors.json --svg anchors.svg
pytest
```

Each JSONL token accepts either a bbox object or `[x0, y0, x1, y1]` array.

## Known limitations

- The discovery bootstrap still uses a page-level corrected-x clustering step. This must be compared against more relational alternatives rather than silently promoted as final architecture.
- Global skew estimation assumes enough repeated starts exist to produce plausible near-x pairs.
- Curved scan distortion is not modeled; anchors are straight trajectories only.
- Run boundaries are token-level and may be over-produced around large field gaps.
- Only left/start anchors are implemented. Numeric right-edge anchors are intentionally deferred until the left-anchor experiment is evaluated.
- Cross-page anchor-graph alignment is not implemented.
- Membership scores are heuristic scores, not calibrated probabilities.

## Promotion gate

Do not build hierarchy on Prototype 001. First evaluate it on difficult real pages against at least:

- raw absolute-x clustering;
- normalized-x clustering;
- the fitted relative-anchor representation.

Promotion requires materially better stability under skew, translation, OCR bbox jitter, and varying whitespace, with failures attributable through the diagnostic artifacts.
