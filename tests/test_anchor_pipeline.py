from __future__ import annotations

from ocr_lexer.anchors import AnchorConfig, build_transitions, discover_anchors, score_memberships
from ocr_lexer.model import BBox, OCRToken
from ocr_lexer.pipeline import AnchorPipeline, AnchorPipelineConfig
from ocr_lexer.spatial import NeighborConfig, RunBoundaryCandidate


def tok(i: int, x: float, y: float, text: str = "word", w: float = 20, h: float = 10) -> OCRToken:
    return OCRToken(i, 0, text, text, BBox(x, y, x + w, y + h), 0.99)


def test_local_neighbors_find_run_starts_without_final_lines() -> None:
    tokens = [
        tok(1, 100, 100), tok(2, 125, 100),
        tok(3, 130, 120), tok(4, 155, 120),
    ]
    result = AnchorPipeline(
        AnchorPipelineConfig(
            neighbors=NeighborConfig(max_horizontal_gap_factor=2.0),
            anchors=AnchorConfig(min_support=1),
        )
    ).run(tokens)
    starts = {b.token_id for b in result.boundaries if b.kind == "START"}
    assert starts == {1, 3}


def test_skew_aware_anchor_fit_recovers_two_relative_anchors() -> None:
    obs: list[RunBoundaryCandidate] = []
    i = 0
    for y in (100.0, 150.0, 200.0, 250.0):
        jitter = (-0.5, 0.3, -0.2, 0.4)[i]
        obs.append(RunBoundaryCandidate(i, 0, i, "START", 100 + 0.02 * y + jitter, y, 10, 1.0))
        i += 1
    for y in (115.0, 165.0, 215.0, 265.0):
        jitter = (0.2, -0.4, 0.1, 0.5)[i - 4]
        obs.append(RunBoundaryCandidate(i, 0, i, "START", 140 + 0.02 * y + jitter, y, 10, 1.0))
        i += 1

    anchors = discover_anchors(obs, config=AnchorConfig(merge_distance_factor=1.2, min_support=3))
    assert len(anchors) == 2
    assert [a.ordinal for a in anchors] == [0, 1]
    assert all(abs(a.slope - 0.02) < 0.015 for a in anchors)

    memberships = score_memberships(obs, anchors)
    best = {}
    for m in memberships:
        if m.object_id not in best or m.score > best[m.object_id].score:
            best[m.object_id] = m
    anchor_by_id = {a.id: a for a in anchors}
    assert all(anchor_by_id[best[i].anchor_id].ordinal == 0 for i in range(4))
    assert all(anchor_by_id[best[i].anchor_id].ordinal == 1 for i in range(4, 8))


def test_relative_transitions_are_translation_invariant() -> None:
    def make_obs(shift: float) -> list[RunBoundaryCandidate]:
        xs = [100, 130, 130, 100, 130]
        return [
            RunBoundaryCandidate(i, 0, i, "START", x + shift, 100 + i * 20, 10, 1.0)
            for i, x in enumerate(xs)
        ]

    transition_sequences = []
    for shift in (0.0, 73.0):
        obs = make_obs(shift)
        anchors = discover_anchors(obs, config=AnchorConfig(merge_distance_factor=1.0, min_support=2))
        memberships = score_memberships(obs, anchors)
        transitions = build_transitions(obs, anchors, memberships)
        transition_sequences.append([
            max(t.relation_scores, key=t.relation_scores.get) for t in transitions
        ])

    assert transition_sequences[0] == transition_sequences[1]
    assert transition_sequences[0] == ["STEP_RIGHT", "SAME", "STEP_LEFT", "STEP_RIGHT"]
