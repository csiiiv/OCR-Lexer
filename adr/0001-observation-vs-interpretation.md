# ADR 0001: Separate Observation from Interpretation

- Status: Accepted
- Date: 2026-09-10

## Context

OCR pipelines commonly harden convenient intermediate constructs such as lines and rows before enough evidence exists to know whether those constructs correspond to logical document units. Errors then propagate irreversibly into classification and hierarchy.

## Decision

OCR tokens and measured geometry are canonical observations. Lines, blocks, logical entries, semantic roles, relationships, and hierarchy are hypotheses derived from those observations.

Intermediate hypotheses must preserve provenance to their source observations and should retain competing interpretations where ambiguity is material.

## Consequences

- Later stages can reconsider earlier grouping choices.
- Debugging can identify the abstraction level at which an error arose.
- Data structures are somewhat richer than a simple destructive ETL pipeline.
- The system can expose uncertainty rather than fabricating a single confident interpretation.
