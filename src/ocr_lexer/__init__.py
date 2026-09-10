"""OCR-Lexer bounded spatial-anchor prototype."""

from .model import BBox, OCRToken
from .pipeline import AnchorPipeline, AnchorPipelineConfig, AnchorPipelineResult

__all__ = [
    "BBox",
    "OCRToken",
    "AnchorPipeline",
    "AnchorPipelineConfig",
    "AnchorPipelineResult",
]
