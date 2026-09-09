from __future__ import annotations

from html import escape

from .model import OCRToken
from .pipeline import AnchorPipelineResult


def render_svg(tokens: list[OCRToken], result: AnchorPipelineResult, padding: float = 20.0) -> str:
    if not tokens:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1" />'
    min_x = min(t.bbox.x0 for t in tokens) - padding
    min_y = min(t.bbox.y0 for t in tokens) - padding
    max_x = max(t.bbox.x1 for t in tokens) + padding
    max_y = max(t.bbox.y1 for t in tokens) + padding
    width = max_x - min_x
    height = max_y - min_y

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {min_y} {width} {height}">',
        '<style>text{font:8px sans-serif}.token{fill:none;stroke:#777;stroke-width:.5}.start{fill:#111}.anchor{fill:none;stroke:#000;stroke-width:1;stroke-dasharray:4 3}</style>',
    ]
    for token in tokens:
        b = token.bbox
        lines.append(f'<rect class="token" x="{b.x0}" y="{b.y0}" width="{b.width}" height="{b.height}" />')
        lines.append(f'<text x="{b.x0}" y="{b.y0 - 1}">{escape(token.text_raw)}</text>')

    starts = {(b.page_id, b.object_id): b for b in result.boundaries if b.kind == "START"}
    for boundary in starts.values():
        lines.append(f'<circle class="start" cx="{boundary.x}" cy="{boundary.y}" r="1.8" />')

    page_ids = {t.page_id for t in tokens}
    if len(page_ids) == 1:
        page_id = next(iter(page_ids))
        y0 = min(t.bbox.y0 for t in tokens)
        y1 = max(t.bbox.y1 for t in tokens)
        for anchor in result.anchors:
            if anchor.page_id != page_id:
                continue
            x0 = anchor.x_at(y0)
            x1 = anchor.x_at(y1)
            lines.append(f'<line class="anchor" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" />')
            lines.append(f'<text x="{x0 + 2}" y="{y0 + 8}">A{anchor.ordinal}</text>')

    lines.append("</svg>")
    return "\n".join(lines)
