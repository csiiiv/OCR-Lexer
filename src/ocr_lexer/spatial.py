from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable

from .model import OCRToken


@dataclass(frozen=True, slots=True)
class SpatialEdge:
    source_id: int
    target_id: int
    direction: str
    horizontal_gap: float
    normalized_gap: float
    center_dy: float
    vertical_overlap: float


@dataclass(frozen=True, slots=True)
class RunBoundaryCandidate:
    object_id: int
    page_id: int
    token_id: int
    kind: str
    x: float
    y: float
    scale: float
    score: float


@dataclass(frozen=True, slots=True)
class NeighborConfig:
    bucket_height_factor: float = 2.0
    max_horizontal_gap_factor: float = 4.0
    max_center_dy_factor: float = 0.75
    min_vertical_overlap: float = 0.25


def _page_scale(tokens: Iterable[OCRToken]) -> float:
    heights = [t.bbox.height for t in tokens if t.bbox.height > 0]
    return median(heights) if heights else 1.0


def build_directional_neighbors(
    tokens: list[OCRToken],
    config: NeighborConfig = NeighborConfig(),
) -> list[SpatialEdge]:
    """Return at most one nearest LEFT and RIGHT edge per token.

    The bucket index only limits which objects are compared. The resulting edges
    are local geometric evidence; they do not assert a finalized visual line.
    """
    by_page: dict[int, list[OCRToken]] = {}
    for token in tokens:
        by_page.setdefault(token.page_id, []).append(token)

    edges: list[SpatialEdge] = []
    for page_tokens in by_page.values():
        page_scale = _page_scale(page_tokens)
        bucket_height = max(page_scale * config.bucket_height_factor, 1.0)
        buckets: dict[int, list[OCRToken]] = {}
        for token in page_tokens:
            key = int(token.bbox.cy // bucket_height)
            buckets.setdefault(key, []).append(token)

        for token in page_tokens:
            token_scale = max(token.bbox.height, page_scale, 1e-6)
            bucket_key = int(token.bbox.cy // bucket_height)
            candidates: list[OCRToken] = []
            for key in (bucket_key - 1, bucket_key, bucket_key + 1):
                candidates.extend(buckets.get(key, ()))

            best_left: tuple[float, OCRToken, float, float] | None = None
            best_right: tuple[float, OCRToken, float, float] | None = None
            for other in candidates:
                if other.id == token.id:
                    continue
                scale = max(token_scale, other.bbox.height, 1e-6)
                center_dy = other.bbox.cy - token.bbox.cy
                overlap = token.bbox.vertical_overlap_ratio(other.bbox)
                vertically_plausible = (
                    overlap >= config.min_vertical_overlap
                    or abs(center_dy) / scale <= config.max_center_dy_factor
                )
                if not vertically_plausible:
                    continue

                right_gap = other.bbox.x0 - token.bbox.x1
                if 0 <= right_gap <= config.max_horizontal_gap_factor * scale:
                    item = (right_gap, other, center_dy, overlap)
                    if best_right is None or item[0] < best_right[0]:
                        best_right = item

                left_gap = token.bbox.x0 - other.bbox.x1
                if 0 <= left_gap <= config.max_horizontal_gap_factor * scale:
                    item = (left_gap, other, center_dy, overlap)
                    if best_left is None or item[0] < best_left[0]:
                        best_left = item

            for direction, best in (("LEFT", best_left), ("RIGHT", best_right)):
                if best is None:
                    continue
                gap, other, center_dy, overlap = best
                edges.append(
                    SpatialEdge(
                        source_id=token.id,
                        target_id=other.id,
                        direction=direction,
                        horizontal_gap=gap,
                        normalized_gap=gap / token_scale,
                        center_dy=center_dy,
                        vertical_overlap=overlap,
                    )
                )
    return edges


def find_run_boundaries(
    tokens: list[OCRToken],
    edges: list[SpatialEdge],
) -> list[RunBoundaryCandidate]:
    """Emit weak START/END observations without constructing lines or rows."""
    has_left = {edge.source_id for edge in edges if edge.direction == "LEFT"}
    has_right = {edge.source_id for edge in edges if edge.direction == "RIGHT"}

    boundaries: list[RunBoundaryCandidate] = []
    for token in tokens:
        scale = max(token.bbox.height, 1.0)
        if token.id not in has_left:
            boundaries.append(
                RunBoundaryCandidate(
                    object_id=token.id,
                    page_id=token.page_id,
                    token_id=token.id,
                    kind="START",
                    x=token.bbox.x0,
                    y=token.bbox.cy,
                    scale=scale,
                    score=1.0,
                )
            )
        if token.id not in has_right:
            boundaries.append(
                RunBoundaryCandidate(
                    object_id=token.id,
                    page_id=token.page_id,
                    token_id=token.id,
                    kind="END",
                    x=token.bbox.x1,
                    y=token.bbox.cy,
                    scale=scale,
                    score=1.0,
                )
            )
    return boundaries
