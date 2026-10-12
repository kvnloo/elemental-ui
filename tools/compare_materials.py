#!/usr/bin/env python3
"""Side-by-side procedural vs credited CC0 reference under matched Cycles staging.

This measures image characteristics, not photorealism or geological identity.
Requires Pillow. GPL-3.0-only code; source scan remains CC0-1.0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageStat


def image_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sample_stats(image):
    image = image.convert("RGB")
    w, h = image.size
    center = image.crop((round(w * .375), round(h * .4),
                         round(w * .625), round(h * .6)))
    gray = ImageOps.grayscale(center)
    stat = ImageStat.Stat(gray)
    edge = ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES))
    return {
        "center_mean_grayscale_srgb": round(stat.mean[0], 3),
        "center_stddev_grayscale_srgb": round(stat.stddev[0], 3),
        "center_edge_signal": round(edge.mean[0], 3),
        "note": "Simple scene-space pixel measures; higher is NOT inherently better.",
    }


def compare(procedural: Path, reference: Path, output: Path, receipt: Path, credits: str):
    with Image.open(procedural) as img:
        p = img.convert("RGB")
    with Image.open(reference) as img:
        r = img.convert("RGB")
    if p.size != r.size:
        raise ValueError("Two renders must have identical dimensions / camera resolution")
    if p.width < 128 or p.height < 80:
        raise ValueError("Comparison render too small")

    pad, title_height, foot_height = 15, 44, 36
    w, h = p.size
    canvas = Image.new("RGB", (2 * w + 3 * pad, h + title_height + foot_height + 2 * pad), "#212222")
    canvas.paste(p, (pad, title_height + pad))
    canvas.paste(r, (2 * pad + w, title_height + pad))
    text = ImageDraw.Draw(canvas)
    text.text((pad, 18), "PROCEDURAL BASALT v1 · GPL-3.0-only", fill="#f1eee8")
    text.text((w + 2 * pad, 18), "DARK ROCK · CC0 reference", fill="#f1eee8")
    text.text((pad, h + title_height + pad + 10), "Same camera, stage & Cycles seed · uncalibrated UV normalization", fill="#e5d9c8")
    text.text((pad, h + title_height + pad + 24), credits, fill="#e5d9c8")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG")
    data = {
        "procedural": {"file": procedural.name, "sha256": image_sha(procedural), "stats": sample_stats(p)},
        "reference": {"file": reference.name, "sha256": image_sha(reference), "stats": sample_stats(r)},
        "comparison_file": output.name,
        "comparison_sha256": image_sha(output),
        "reference_credit": credits,
        "labels": ["Procedural basalt (artistic)", "Dark Rock (licensed CC0 scan; mineral identity not confirmed)"],
        "matching_conditions": ["geometry", "camera", "studio lighting", "resolution", "Cycles sampling seed"],
        "not_equivalent": ["physical source scale", "material identity", "texture calibration"],
        "quality_claim": "None; numerical image descriptors are not realism scores",
    }
    receipt.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--procedural", type=Path, required=True)
    cli.add_argument("--reference", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    cli.add_argument("--receipt", type=Path, required=True)
    cli.add_argument("--credit", default="Scan: Amal Kumar / Poly Haven (CC0-1.0)")
    args = cli.parse_args()
    print(json.dumps(compare(args.procedural, args.reference, args.out, args.receipt, args.credit), indent=2))


if __name__ == "__main__":
    main()
