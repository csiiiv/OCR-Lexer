# ADR 0003: Preserve Competing Hypotheses

- Status: Accepted
- Date: 2026-09-10

## Context

A locally plausible grouping can be contradicted by later evidence such as amount columns, repeated structures, page continuation, arithmetic totals, or hierarchy constraints. Greedy selection at line/block/entry formation loses alternatives before that evidence exists.

## Decision

Material ambiguities should be represented as competing scored hypotheses rather than immediately collapsed to a single interpretation.

Each hypothesis should retain source evidence, decomposed evidence scores, dependencies, competing alternatives, confidence, and selection status.

Global search must be bounded to avoid combinatorial explosion. Candidate generation should remain local and cheap; richer evaluation and pruning occur later.

## Consequences

- Later evidence can resolve earlier ambiguity.
- Beam search or another bounded search strategy will eventually be required.
- Diagnostics must expose why one hypothesis outranks another.
- The parser becomes an inference system rather than a one-way transformation pipeline.
