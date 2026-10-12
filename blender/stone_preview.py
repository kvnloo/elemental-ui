"""Blender procedural stone preview: GPL-3.0-only.

Run: blender -b --python blender/stone_preview.py -- --material geo.basalt.vesicular.v1 --out outputs/blender
Requires Blender 4.2+; UI preview is not a calibrated scan nor a baked PBR export.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

try:
    import bpy
    from mathutils import Vector
except ImportError as exc:
    raise SystemExit("Run this script with Blender's Python: blender -b --python blender/stone_preview.py -- ...") from exc

ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--material", default="geo.basalt.vesicular.v1")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs" / "blender")
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--size", type=int, default=900)
    return parser.parse_args(raw)


def recipe_for(material_id):
    for path in (ROOT / "materials").glob("**/*.json"):
        recipe = json.loads(path.read_text(encoding="utf-8"))
        if recipe["id"] == material_id:
            return recipe
    raise ValueError("Unknown material: " + material_id)


def srgb_linear(channel):
    value = channel / 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def stone_material(recipe):
    settings = recipe["parameters"]
    material = bpy.data.materials.new(name=recipe["id"])
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    links = material.node_tree.links
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (700, 120)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (440, 120)
    color = nodes.new("ShaderNodeValToRGB")
    color.location = (170, 210)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-330, 210)
    noise.inputs["Scale"].default_value = 110.0 if "basalt" in recipe["id"] else 48.0
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.72
    noise.inputs["Distortion"].default_value = 0.18
    color_values = [srgb_linear(c) for c in settings["base_color_rgb"]]
    color.color_ramp.elements[0].position = 0.21
    color.color_ramp.elements[0].color = tuple(v * 0.47 for v in color_values) + (1,)
    color.color_ramp.elements[1].position = 0.83
    color.color_ramp.elements[1].color = tuple(min(1.0, v * 1.45) for v in color_values) + (1,)
    links.new(noise.outputs["Fac"], color.inputs["Fac"])
    links.new(color.outputs["Color"], shader.inputs["Base Color"])

    variation = nodes.new("ShaderNodeTexNoise")
    variation.location = (-330, -90)
    variation.inputs["Scale"].default_value = 23.0
    variation.inputs["Detail"].default_value = 4.0
    variation.inputs["Roughness"].default_value = 0.75
    links.new(variation.outputs["Fac"], shader.inputs["Roughness"])
    # Blend nominal measured-looking roughness with procedural variation.
    mix = nodes.new("ShaderNodeMapRange")
    mix.location = (170, -90)
    mix.inputs["To Min"].default_value = max(0.02, settings["roughness"] - 0.14)
    mix.inputs["To Max"].default_value = min(1.0, settings["roughness"] + 0.09)
    links.new(variation.outputs["Fac"], mix.inputs["Value"])
    links.new(mix.outputs["Result"], shader.inputs["Roughness"])

    bump = nodes.new("ShaderNodeBump")
    bump.location = (200, -275)
    bump.inputs["Strength"].default_value = 0.32
    bump.inputs["Distance"].default_value = settings["height_mm"] / 1000.0
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])

    if "slate" in recipe["id"]:
        bands = nodes.new("ShaderNodeTexWave")
        bands.location = (-350, 460)
        bands.wave_type = "BANDS"
        bands.bands_direction = "Y"
        bands.inputs["Scale"].default_value = 52.0
        bands.inputs["Distortion"].default_value = 1.7
        add = nodes.new("ShaderNodeMixRGB")
        add.location = (-80, 240)
        add.blend_type = "MULTIPLY"
        add.inputs[0].default_value = 0.22
        links.new(noise.outputs["Fac"], add.inputs[1])
        links.new(bands.outputs["Fac"], add.inputs[2])
        links.new(add.outputs[0], color.inputs["Fac"])

    if "limestone" in recipe["id"]:
        pores = nodes.new("ShaderNodeTexVoronoi")
        pores.location = (-340, -325)
        pores.inputs["Scale"].default_value = 85.0
        # Pores create cavities; curve follows distance to nearest cell center.
        links.new(pores.outputs["Distance"], bump.inputs["Height"])

    links.new(shader.outputs["BSDF"], out.inputs["Surface"])
    return material


def look_at(obj, point):
    direction = Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def area_light(name, position, energy, size, target=(0, 0, 0)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    look_at(obj, target)
    return obj


def build_scene(recipe, samples, size):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = max(1, samples)
    scene.render.resolution_x = size
    scene.render.resolution_y = round(size * 0.68)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if scene.world is None:
        # Empty factory settings have no World datablock in bpy module/headless mode.
        scene.world = bpy.data.worlds.new("Neutral studio world")
    scene.world.color = (0.07, 0.07, 0.07)
    try:
        scene.view_settings.view_transform = "AgX"
    except TypeError:
        pass

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.035))
    slab = bpy.context.object
    slab.name = "Elemental carved stone / blank button"
    slab.dimensions = (0.21, 0.085, 0.025)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = slab.modifiers.new("Worn softened edges", "BEVEL")
    bevel.width = 0.008
    bevel.segments = 7
    if hasattr(bevel, "affect"):
        bevel.affect = "EDGES"
    slab.data.materials.append(stone_material(recipe))
    bpy.ops.object.shade_smooth()

    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "Neutral studio floor"
    ground.scale = (0.6, 0.6, 1)
    floor_mat = bpy.data.materials.new("Neutral graphite floor")
    floor_mat.diffuse_color = (0.045, 0.044, 0.043, 1)
    floor_mat.use_nodes = True
    floor_mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.045, 0.044, 0.043, 1)
    ground.data.materials.append(floor_mat)

    # The geometry is ~21cm wide and lights are ~30cm away: the original
    # 100/50 W rig clipped dark stone into a nearly white render.
    area_light("Softbox key", (0.03, -0.16, 0.27), 3, 0.24)
    area_light("Rim bounce", (-0.18, 0.05, 0.14), 1.5, 0.20)

    camera_data = bpy.data.cameras.new("Product orthographic")
    camera = bpy.data.objects.new("Product orthographic", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (0.21, -0.20, 0.22)
    look_at(camera, (0, 0, 0.038))
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 0.32
    scene.camera = camera
    return scene


def main():
    args = parse_args()
    if args.size < 128 or args.size > 4096:
        raise ValueError("--size must be between 128 and 4096")
    recipe = recipe_for(args.material)
    if recipe["family"] != "geological":
        raise ValueError("Blender draft preview currently supports geological materials only")
    args.out.mkdir(parents=True, exist_ok=True)
    scene = build_scene(recipe, args.samples, args.size)
    target = args.out / recipe["id"]
    target.mkdir(parents=True, exist_ok=True)
    blend = target / "stone-preview.blend"
    scene.render.filepath = str(target / "stone-preview.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.render.render(write_still=True)
    print("Wrote", scene.render.filepath, "and", blend)


if __name__ == "__main__":
    main()
