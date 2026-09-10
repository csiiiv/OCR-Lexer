from __future__ import annotations

from dataclasses import dataclass
from math import exp
from statistics import median

from .spatial import RunBoundaryCandidate


@dataclass(frozen=True, slots=True)
class AnchorConfig:
    merge_distance_factor: float = 1.0
    min_support: int = 2
    min_pair_dy_factor: float = 2.0
    max_pair_dx_factor: float = 1.5
    max_abs_slope: float = 0.25
    membership_sigma_floor: float = 0.35
    membership_keep_threshold: float = 0.02


@dataclass(frozen=True, slots=True)
class SpatialAnchorHypothesis:
    id: int
    page_id: int
    kind: str
    intercept: float
    slope: float
    reference_y: float
    support_ids: tuple[int, ...]
    score: float
    residual_scale: float
    ordinal: int

    def x_at(self, y: float) -> float:
        return self.intercept + self.slope * (y - self.reference_y)


@dataclass(frozen=True, slots=True)
class AnchorMembership:
    object_id: int
    anchor_id: int
    residual: float
    normalized_residual: float
    score: float


@dataclass(frozen=True, slots=True)
class AnchorTransition:
    source_object_id: int
    target_object_id: int
    relation_scores: dict[str, float]


def _median_slope(points: list[RunBoundaryCandidate], reference_y: float) -> float:
    if len(points) < 2:
        return 0.0
    slopes: list[float] = []
    scale = median([p.scale for p in points])
    min_dy = max(1.0, 2.0 * scale)
    for i, a in enumerate(points):
        for b in points[i + 1 :]:
            dy = b.y - a.y
            if abs(dy) < min_dy:
                continue
            slopes.append((b.x - a.x) / dy)
    return median(slopes) if slopes else 0.0


def estimate_global_skew(
    observations: list[RunBoundaryCandidate],
    config: AnchorConfig,
) -> float:
    """Estimate shared x drift using only pairs that are plausibly same-anchor.

    This is a bootstrap estimate. Absolute x is used only to discover plausible
    pairs; final structural evidence is expressed relative to fitted anchors.
    """
    if len(observations) < 2:
        return 0.0
    scale = median([o.scale for o in observations])
    min_dy = config.min_pair_dy_factor * scale
    max_dx = config.max_pair_dx_factor * scale
    slopes: list[float] = []
    for i, a in enumerate(observations):
        for b in observations[i + 1 :]:
            dy = b.y - a.y
            dx = b.x - a.x
            if abs(dy) < min_dy or abs(dx) > max_dx:
                continue
            slope = dx / dy
            if abs(slope) <= config.max_abs_slope:
                slopes.append(slope)
    return median(slopes) if slopes else 0.0


def _cluster_corrected_x(
    observations: list[RunBoundaryCandidate],
    slope: float,
    reference_y: float,
    config: AnchorConfig,
) -> list[list[RunBoundaryCandidate]]:
    if not observations:
        return []
    scale = median([o.scale for o in observations])
    threshold = config.merge_distance_factor * scale
    corrected = sorted(
        ((o.x - slope * (o.y - reference_y), o) for o in observations),
        key=lambda item: item[0],
    )
    clusters: list[list[RunBoundaryCandidate]] = []
    centers: list[float] = []
    for value, obs in corrected:
        if not clusters or abs(value - centers[-1]) > threshold:
            clusters.append([obs])
            centers.append(value)
            continue
        clusters[-1].append(obs)
        vals = [p.x - slope * (p.y - reference_y) for p in clusters[-1]]
        centers[-1] = median(vals)
    return clusters


def discover_anchors(
    observations: list[RunBoundaryCandidate],
    *,
    kind: str = "LEFT_TEXT",
    config: AnchorConfig = AnchorConfig(),
) -> list[SpatialAnchorHypothesis]:
    starts = [o for o in observations if o.kind == "START"]
    if not starts:
        return []
    anchors: list[SpatialAnchorHypothesis] = []
    pages = sorted({o.page_id for o in starts})
    next_id = 0
    for page_id in pages:
        page_obs = [o for o in starts if o.page_id == page_id]
        reference_y = median([o.y for o in page_obs])
        global_slope = estimate_global_skew(page_obs, config)
        clusters = _cluster_corrected_x(page_obs, global_slope, reference_y, config)
        fitted: list[SpatialAnchorHypothesis] = []
        for cluster in clusters:
            if len(cluster) < config.min_support:
                continue
            slope = _median_slope(cluster, reference_y)
            slope = max(-config.max_abs_slope, min(config.max_abs_slope, slope))
            intercept = median([p.x - slope * (p.y - reference_y) for p in cluster])
            norm_residuals = [
                abs(p.x - (intercept + slope * (p.y - reference_y))) / max(p.scale, 1e-6)
                for p in cluster
            ]
            residual_scale = median(norm_residuals) if norm_residuals else 0.0
            score = len(cluster) / (len(cluster) + residual_scale + 1.0)
            fitted.append(
                SpatialAnchorHypothesis(
                    id=next_id,
                    page_id=page_id,
                    kind=kind,
                    intercept=intercept,
                    slope=slope,
                    reference_y=reference_y,
                    support_ids=tuple(sorted(p.object_id for p in cluster)),
                    score=score,
                    residual_scale=residual_scale,
                    ordinal=-1,
                )
            )
            next_id += 1

        fitted.sort(key=lambda a: a.x_at(reference_y))
        for ordinal, anchor in enumerate(fitted):
            anchors.append(
                SpatialAnchorHypothesis(
                    id=anchor.id,
                    page_id=anchor.page_id,
                    kind=anchor.kind,
                    intercept=anchor.intercept,
                    slope=anchor.slope,
                    reference_y=anchor.reference_y,
                    support_ids=anchor.support_ids,
                    score=anchor.score,
                    residual_scale=anchor.residual_scale,
                    ordinal=ordinal,
                )
            )
    return anchors


def score_memberships(
    observations: list[RunBoundaryCandidate],
    anchors: list[SpatialAnchorHypothesis],
    config: AnchorConfig = AnchorConfig(),
) -> list[AnchorMembership]:
    memberships: list[AnchorMembership] = []
    for obs in observations:
        if obs.kind != "START":
            continue
        candidates = [a for a in anchors if a.page_id == obs.page_id]
        raw: list[tuple[SpatialAnchorHypothesis, float, float, float]] = []
        for anchor in candidates:
            residual = obs.x - anchor.x_at(obs.y)
            normalized = residual / max(obs.scale, 1e-6)
            sigma = max(config.membership_sigma_floor, anchor.residual_scale * 2.0)
            likelihood = exp(-0.5 * (normalized / sigma) ** 2)
            raw.append((anchor, residual, normalized, likelihood))
        total = sum(item[3] for item in raw)
        if total <= 0:
            continue
        for anchor, residual, normalized, likelihood in raw:
            score = likelihood / total
            if score >= config.membership_keep_threshold:
                memberships.append(
                    AnchorMembership(
                        object_id=obs.object_id,
                        anchor_id=anchor.id,
                        residual=residual,
                        normalized_residual=normalized,
                        score=score,
                    )
                )
    return memberships


def build_transitions(
    observations: list[RunBoundaryCandidate],
    anchors: list[SpatialAnchorHypothesis],
    memberships: list[AnchorMembership],
) -> list[AnchorTransition]:
    anchor_by_id = {a.id: a for a in anchors}
    by_object: dict[int, list[AnchorMembership]] = {}
    for membership in memberships:
        by_object.setdefault(membership.object_id, []).append(membership)

    starts = sorted(
        (o for o in observations if o.kind == "START"),
        key=lambda o: (o.page_id, o.y, o.x),
    )
    transitions: list[AnchorTransition] = []
    for source, target in zip(starts, starts[1:]):
        if source.page_id != target.page_id:
            continue
        relation_scores = {
            "SAME": 0.0,
            "STEP_RIGHT": 0.0,
            "STEP_LEFT": 0.0,
            "SKIP_RIGHT": 0.0,
            "SKIP_LEFT": 0.0,
            "UNRESOLVED": 0.0,
        }
        source_members = by_object.get(source.object_id, [])
        target_members = by_object.get(target.object_id, [])
        if not source_members or not target_members:
            relation_scores["UNRESOLVED"] = 1.0
        else:
            for sm in source_members:
                for tm in target_members:
                    sa = anchor_by_id[sm.anchor_id]
                    ta = anchor_by_id[tm.anchor_id]
                    delta = ta.ordinal - sa.ordinal
                    mass = sm.score * tm.score
                    if delta == 0:
                        key = "SAME"
                    elif delta == 1:
                        key = "STEP_RIGHT"
                    elif delta == -1:
                        key = "STEP_LEFT"
                    elif delta > 1:
                        key = "SKIP_RIGHT"
                    else:
                        key = "SKIP_LEFT"
                    relation_scores[key] += mass
            total = sum(relation_scores.values())
            if total < 1.0:
                relation_scores["UNRESOLVED"] += 1.0 - total
        transitions.append(
            AnchorTransition(
                source_object_id=source.object_id,
                target_object_id=target.object_id,
                relation_scores=relation_scores,
            )
        )
    return transitions
