"""Render one independently credited Poly Haven scan in the same Cycles stage.

GPL-3.0-only code. Original scanned textures are CC0-1.0.
Raw scan contents remain outside git. The output is a reference comparison,
NOT a verified basalt match nor physical calibration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from reference_pbr import validate_reference_pack
try:
    import bpy
    from stone_preview import build_scene, recipe_for
    from render_pbr_pack import build_pbr_material
except ImportError as exc:
    raise SystemExit("Blender 4.5.14 / Python 3.11 is required to render a reference") from exc


def args_parser():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", default="dark_rock")
    parser.add_argument("--resolution", choices=("1k", "2k"), default="1k")
    parser.add_argument("--source-root", type=Path, default=ROOT / "outputs/external/polyhaven")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs/comparisons")
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--size", type=int, default=256)
    return parser.parse_args(args)


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    args = args_parser()
    if not 1 <= args.samples <= 1024 or not 128 <= args.size <= 4096:
        raise ValueError("Invalid sample count or output size")
    provenance, paths = validate_reference_pack(args.source_root, args.asset, args.resolution)

    # Reuse the exact same model, viewpoint, lights, renderer and Cycles seed
    # as the procedural basalt baseline. Do not infer scan physical identity
    # from the geometry template or the source's page description.
    geometry = recipe_for("geo.basalt.vesicular.v1")
    scene = build_scene(geometry, args.samples, args.size)
    slab = bpy.data.objects["Elemental carved stone / blank button"]
    slab.data.materials.clear()

    # Normalize UV coverage to basalt's 240 mm artistic tile for an informative
    # screen-space comparison, NOT actual scan scale (published scan is much larger).
    uv = (210.0 / geometry["physical_tile_mm"], 85.0 / geometry["physical_tile_mm"])
    material = build_pbr_material(
        {"id": "CC0 reference / " + args.asset, "physical_tile_mm": 240},
        paths, uv_repeat=uv)
    material["source_license"] = "CC0-1.0"
    material["scan_asset"] = args.asset
    material["source_author"] = ", ".join(provenance["creators"])
    slab.data.materials.append(material)
    scene.cycles.device = "CPU"
    scene.cycles.seed = 42
    scene.render.image_settings.color_mode = "RGBA"

    folder = args.out / args.asset
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / "reference-preview.png"
    blend = folder / "reference-preview.blend"
    scene.render.filepath = str(output.resolve())
    bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()))
    bpy.ops.render.render(write_still=True)
    if not output.is_file():
        raise RuntimeError("Expected Blender reference render missing")
    receipt = {
        "asset_id": args.asset,
        "source_license": provenance["source_license"],
        "provider": provenance["provider"],
        "creators": provenance["creators"],
        "source_url": provenance["source_url"],
        "not_equivalent_to": provenance["not_equivalent_to"],
        "status": provenance["status"],
        "original_scale_statement": provenance["scale_statement"],
        "physical_scale_calibrated": False,
        "uv_repeat_normalized": list(uv),
        "uv_note": "Normalized artwork comparison, not measured tile scale",
        "height_applied": False,
        "render_size": [scene.render.resolution_x, scene.render.resolution_y],
        "samples": args.samples,
        "cycles_seed": 42,
        "blender": bpy.app.version_string,
        "device": "CYCLES / CPU",
        "map_hashes": {k: checksum(v) for k, v in paths.items()},
        "output_png": {"file": output.name, "sha256": checksum(output), "bytes": output.stat().st_size},
    }
    (folder / "reference-render-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("Rendered CC0", args.asset, "by", provenance["creators"], "->", output)


if __name__ == "__main__":
    main()
