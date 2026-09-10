from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        if self.x1 < self.x0 or self.y1 < self.y0:
            raise ValueError("invalid bbox ordering")

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0

    def vertical_overlap_ratio(self, other: "BBox") -> float:
        overlap = max(0.0, min(self.y1, other.y1) - max(self.y0, other.y0))
        denom = min(self.height, other.height)
        return 0.0 if denom <= 0 else overlap / denom


@dataclass(frozen=True, slots=True)
class OCRToken:
    id: int
    page_id: int
    text_raw: str
    text_normalized: str
    bbox: BBox
    confidence: float
    rotation_deg: float | None = None
    source_index: int | None = None
