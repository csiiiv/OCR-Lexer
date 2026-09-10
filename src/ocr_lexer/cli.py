from __future__ import annotations

import argparse
import json
from pathlib import Path

from .diagnostics import render_svg
from .model import BBox, OCRToken
from .pipeline import AnchorPipeline


def _load_jsonl(path: Path) -> list[OCRToken]:
    tokens: list[OCRToken] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            bbox = row["bbox"]
            if isinstance(bbox, list):
                bbox = {"x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3]}
            tokens.append(
                OCRToken(
                    id=int(row["id"]),
                    page_id=int(row.get("page_id", 0)),
                    text_raw=str(row["text_raw"]),
                    text_normalized=str(row.get("text_normalized", row["text_raw"])),
                    bbox=BBox(**bbox),
                    confidence=float(row.get("confidence", 1.0)),
                    rotation_deg=row.get("rotation_deg"),
                    source_index=row.get("source_index"),
                )
            )
    return tokens


def main() -> None:
    parser = argparse.ArgumentParser(prog="ocr-lexer")
    subparsers = parser.add_subparsers(dest="command", required=True)
    anchors = subparsers.add_parser("anchors", help="run bounded spatial-anchor prototype")
    anchors.add_argument("input", type=Path, help="OCR token JSONL")
    anchors.add_argument("--output", "-o", type=Path, required=True, help="result JSON")
    anchors.add_argument("--svg", type=Path, help="optional SVG diagnostic overlay")
    args = parser.parse_args()

    if args.command == "anchors":
        tokens = _load_jsonl(args.input)
        result = AnchorPipeline().run(tokens)
        args.output.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        if args.svg:
            args.svg.write_text(render_svg(tokens, result), encoding="utf-8")
