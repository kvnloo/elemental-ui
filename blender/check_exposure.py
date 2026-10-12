"""Guard against washed-out or black PBR previews, not a photorealism metric.

GPL-3.0-only. Requires Pillow, only in optional Blender CI.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from PIL import Image, ImageStat


def inspect(image_path: Path, low: float, high: float) -> dict:
    if not 0 <= low < high <= 255:
        raise ValueError("expected 0 <= low < high <= 255")
    with Image.open(image_path) as source:
        im = source.convert("RGB")
    w, h = im.size
    # Center lies inside the stone button top in the standardized studio framing.
    cropped = im.crop((round(w * .375), round(h * .4), round(w * .625), round(h * .6)))
    stat = ImageStat.Stat(cropped)
    rgb = stat.median
    luma = rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722
    passed = low <= luma <= high
    return {
        "image": image_path.name,
        "resolution": [w, h],
        "roi_fraction": [.375, .4, .625, .6],
        "median_srgb_rgb": [round(x, 2) for x in rgb],
        "median_luminance_srgb": round(luma, 2),
        "target_bounds_srgb": [low, high],
        "passed": passed,
        "scope": "Screen-space washout smoke gate only; not BRDF or geologic fidelity validation.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--min-luma", type=float, default=8.0)
    parser.add_argument("--max-luma", type=float, default=180.0)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = inspect(args.image, args.min_luma, args.max_luma)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        parser.exit(1, "render failed exposure smoke bounds\n")


if __name__ == "__main__":
    main()
