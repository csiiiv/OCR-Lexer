from __future__ import annotations

from dataclasses import asdict, dataclass

from .anchors import (
    AnchorConfig,
    AnchorMembership,
    AnchorTransition,
    SpatialAnchorHypothesis,
    build_transitions,
    discover_anchors,
    score_memberships,
)
from .model import OCRToken
from .spatial import (
    NeighborConfig,
    RunBoundaryCandidate,
    SpatialEdge,
    build_directional_neighbors,
    find_run_boundaries,
)


@dataclass(frozen=True, slots=True)
class AnchorPipelineConfig:
    neighbors: NeighborConfig = NeighborConfig()
    anchors: AnchorConfig = AnchorConfig()


@dataclass(frozen=True, slots=True)
class AnchorPipelineResult:
    edges: tuple[SpatialEdge, ...]
    boundaries: tuple[RunBoundaryCandidate, ...]
    anchors: tuple[SpatialAnchorHypothesis, ...]
    memberships: tuple[AnchorMembership, ...]
    transitions: tuple[AnchorTransition, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "spatial_edges": [asdict(x) for x in self.edges],
            "run_boundaries": [asdict(x) for x in self.boundaries],
            "anchors": [asdict(x) for x in self.anchors],
            "memberships": [asdict(x) for x in self.memberships],
            "transitions": [asdict(x) for x in self.transitions],
        }


class AnchorPipeline:
    def __init__(self, config: AnchorPipelineConfig = AnchorPipelineConfig()) -> None:
        self.config = config

    def run(self, tokens: list[OCRToken]) -> AnchorPipelineResult:
        edges = build_directional_neighbors(tokens, self.config.neighbors)
        boundaries = find_run_boundaries(tokens, edges)
        anchors = discover_anchors(boundaries, config=self.config.anchors)
        memberships = score_memberships(boundaries, anchors, self.config.anchors)
        transitions = build_transitions(boundaries, anchors, memberships)
        return AnchorPipelineResult(
            edges=tuple(edges),
            boundaries=tuple(boundaries),
            anchors=tuple(anchors),
            memberships=tuple(memberships),
            transitions=tuple(transitions),
        )
