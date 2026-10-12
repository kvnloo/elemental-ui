"""Render a verified PBR pack under Blender Cycles (GPL-3.0-only).

Blender CLI:
  blender -b --python blender/render_pbr_pack.py -- --material geo.basalt.vesicular.v1
bpy Python 3.11 CLI:
  python blender/render_pbr_pack.py --material geo.basalt.vesicular.v1

Color/roughness/OpenGL normal maps are shared with the website's generated
assets. Verified 16-bit height is *not* double-applied on top of normal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pbr_assets import validate_maps  # noqa: E402

try:
    import bpy
    from stone_preview import build_scene, recipe_for
except ImportError as exc:
    raise SystemExit("Requires Blender 4.5+ or bpy==4.5.14 (Python 3.11). See docs/PBR_BLENDER.md") from exc


def parse_args():
    cmdline = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--material", default="geo.basalt.vesicular.v1")
    p.add_argument("--map-root", type=Path, default=ROOT / "web" / "assets")
    p.add_argument("--out", type=Path, default=ROOT / "outputs" / "blender")
    p.add_argument("--samples", type=int, default=8)
    p.add_argument("--size", type=int, default=512)
    return p.parse_args(cmdline)


def image_node(nodes, name, image_path, *, non_color):
    image = bpy.data.images.load(str(image_path), check_existing=False)
    image.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    node = nodes.new("ShaderNodeTexImage")
    node.label = name
    node.image = image
    node.extension = "REPEAT"
    node.interpolation = "Linear"
    return node


def build_pbr_material(recipe, paths, *, uv_repeat=None):
    shader = bpy.data.materials.new("Baked PBR / " + recipe["id"])
    shader.use_nodes = True
    nodes = shader.node_tree.nodes
    nodes.clear()
    wires = shader.node_tree.links

    uv = nodes.new("ShaderNodeTexCoord")
    uv.location = (-900, 50)
    uv_scale = nodes.new("ShaderNodeVectorMath")
    uv_scale.operation = "MULTIPLY"
    tile = recipe["physical_tile_mm"]
    # Optional explicit UV coverage supports licensed scans whose measured
    # physical scale is unknown; it is NOT a declaration of scan tile size.
    if uv_repeat is None:
        uv_repeat = (210.0 / tile, 85.0 / tile)
    if len(uv_repeat) != 2 or any(not 0 < value <= 16 for value in uv_repeat):
        raise ValueError("uv_repeat must be two positive values <=16")
    uv_scale.inputs[1].default_value = (uv_repeat[0], uv_repeat[1], 1.0)
    uv_scale.location = (-700, 40)
    wires.new(uv.outputs["UV"], uv_scale.inputs[0])

    albedo = image_node(nodes, "sRGB / lighting-free basecolor", paths["basecolor"], non_color=False)
    rough = image_node(nodes, "Linear / roughness", paths["roughness"], non_color=True)
    normals = image_node(nodes, "Linear / OpenGL tangent normal", paths["normal"], non_color=True)
    for node, y in ((albedo, 280), (rough, 20), (normals, -240)):
        node.location = (-450, y)
        wires.new(uv_scale.outputs["Vector"], node.inputs["Vector"])

    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.label = "OpenGL +Y tangent normal"
    normal_map.space = "TANGENT"
    normal_map.inputs["Strength"].default_value = 1.0
    normal_map.location = (-150, -210)
    wires.new(normals.outputs["Color"], normal_map.inputs["Color"])

    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (130, 100)
    principled.inputs["Metallic"].default_value = 0.0
    wires.new(albedo.outputs["Color"], principled.inputs["Base Color"])
    wires.new(rough.outputs["Color"], principled.inputs["Roughness"])
    wires.new(normal_map.outputs["Normal"], principled.inputs["Normal"])

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (480, 100)
    wires.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return shader


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    args = parse_args()
    if not 1 <= args.samples <= 1024 or not 128 <= args.size <= 4096:
        raise ValueError("samples must be 1–1024 and size 128–4096")
    recipe = recipe_for(args.material)
    if recipe["family"] != "geological":
        raise ValueError("PBR Blender preview currently supports geological materials")
    manifest, paths = validate_maps(args.map_root, recipe["id"])
    if (manifest["physical_tile_mm"] != recipe["physical_tile_mm"]
            or manifest["seed"] != recipe["seed"]):
        raise ValueError("PBR pack and recipe disagree on seed or physical tile scale")

    scene = build_scene(recipe, args.samples, args.size)
    slab = bpy.data.objects["Elemental carved stone / blank button"]
    slab.data.materials.clear()
    slab.data.materials.append(build_pbr_material(recipe, paths))
    scene.cycles.device = "CPU"
    scene.cycles.seed = 42
    scene.render.image_settings.color_mode = "RGBA"

    folder = args.out / recipe["id"]
    folder.mkdir(parents=True, exist_ok=True)
    source = folder / "pbr-preview.blend"
    image = folder / "pbr-preview.png"
    scene.render.filepath = str(image.absolute())
    bpy.ops.wm.save_as_mainfile(filepath=str(source.absolute()))
    bpy.ops.render.render(write_still=True)
    if not image.is_file():
        raise RuntimeError("Blender did not write output PNG")
    receipt = {
        "material_id": recipe["id"],
        "source_license": manifest["source_license"],
        "generator_status": manifest["status"],
        "blender": bpy.app.version_string,
        "renderer": "CYCLES / CPU",
        "studio_lighting_watts": {
            "softbox_key": bpy.data.objects["Softbox key"].data.energy,
            "rim_bounce": bpy.data.objects["Rim bounce"].data.energy,
        },
        "cycles_samples": args.samples,
        "seed": 42,
        "render_size": [scene.render.resolution_x, scene.render.resolution_y],
        "height_applied": False,
        "texture_maps": {tag: {"sha256": sha(path), "file": path.name} for tag, path in paths.items()},
        "output_png": {"file": image.name, "sha256": sha(image), "bytes": image.stat().st_size},
        "quality_limit": "Source maps are prototype/unvalidated, not measured photogrammetry."
    }
    (folder / "pbr-render-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("Rendered", recipe["id"], "with Blender", bpy.app.version_string, "at", image)


if __name__ == "__main__":
    main()
