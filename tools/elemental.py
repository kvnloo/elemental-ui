#!/usr/bin/env python3
"""elemental-ui: deterministic, dependency-free PBR *draft* texture generator.

GPL-3.0-only. These procedural studies are not scanned, calibrated or validated
photorealistic textures. All previews and maps are generated from recipe seeds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "materials"
ID_RE = re.compile(r"^(geo|bot|aq|fauna|atm)\.[a-z0-9-]+(?:\.[a-z0-9-]+)+\.v[1-9]\d*$")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAP_NAMES = ("basecolor", "roughness", "height", "normal", "preview")


def all_recipes() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(RECIPES.glob("**/*.json"))]


def recipe_errors(recipe: dict) -> list[str]:
    errors = []
    required = ("id", "display_name", "family", "kind", "version", "author",
                "license", "seed", "physical_tile_mm", "parameters", "references", "status")
    for key in required:
        if key not in recipe:
            errors.append(f"missing {key}")
    if errors:
        return errors
    if not isinstance(recipe["id"], str) or not ID_RE.fullmatch(recipe["id"]):
        errors.append("invalid material id")
    if recipe["family"] not in ("geological", "botanical", "aquatic", "fauna", "atmospheric"):
        errors.append("invalid family")
    if recipe["kind"] not in ("tileable-surface", "bounded-object", "animated-surface", "volumetric-effect"):
        errors.append("invalid kind")
    if recipe["license"] != "GPL-3.0-only":
        errors.append("recipe license must be GPL-3.0-only in this first-party collection")
    if type(recipe["seed"]) is not int or recipe["seed"] < 0:
        errors.append("seed must be a nonnegative integer")
    if type(recipe["version"]) is not int or recipe["version"] < 1:
        errors.append("version must be a positive integer")
    if not isinstance(recipe["physical_tile_mm"], (int, float)) or recipe["physical_tile_mm"] <= 0:
        errors.append("physical_tile_mm must be positive")
    params = recipe.get("parameters", {})
    for key in ("base_color_rgb", "roughness", "height_mm", "grain", "weathering"):
        if key not in params:
            errors.append(f"missing parameters.{key}")
    if not errors:
        col = params["base_color_rgb"]
        if not isinstance(col, list) or len(col) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in col):
            errors.append("base_color_rgb must contain three 8-bit integers")
        for key in ("roughness", "weathering"):
            if not isinstance(params[key], (float, int)) or not 0 <= params[key] <= 1:
                errors.append(f"{key} must be between 0 and 1")
        if not isinstance(params["grain"], (int, float)) or params["grain"] <= 0:
            errors.append("grain must be positive")
        if not isinstance(params["height_mm"], (int, float)) or params["height_mm"] < 0:
            errors.append("height_mm must be nonnegative")
    if not isinstance(recipe["references"], list):
        errors.append("references must be a list")
    else:
        for idx, ref in enumerate(recipe["references"]):
            if not isinstance(ref, dict) or any(key not in ref for key in ("creator", "url", "license", "retrieved_at")):
                errors.append(f"reference {idx} missing provenance")
    if recipe["status"] not in ("prototype", "render-pass", "visual-review", "web-pass", "published"):
        errors.append("invalid status")
    return errors


def _hash2(x: int, y: int, seed: int) -> float:
    value = (x * 374761393 + y * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    value = ((value ^ (value >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((value ^ (value >> 16)) & 0xFFFFFFFF) / 0xFFFFFFFF


def noise(u: float, v: float, freq: int, seed: int) -> float:
    """Period-1 continuous 2D value noise. Opposing tile edges are identical."""
    a, b = u * freq, v * freq
    ix, iy = math.floor(a), math.floor(b)
    tx, ty = a - ix, b - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    x0, x1 = ix % freq, (ix + 1) % freq
    y0, y1 = iy % freq, (iy + 1) % freq
    n0 = _hash2(x0, y0, seed) * (1 - tx) + _hash2(x1, y0, seed) * tx
    n1 = _hash2(x0, y1, seed) * (1 - tx) + _hash2(x1, y1, seed) * tx
    return n0 * (1 - ty) + n1 * ty


def fbm(u: float, v: float, base: int, seed: int) -> float:
    return (0.56 * noise(u, v, base, seed)
            + 0.29 * noise(u, v, base * 2, seed + 7)
            + 0.15 * noise(u, v, base * 4, seed + 13))


def _clamp(value: float, high: int = 255) -> int:
    return max(0, min(high, int(round(value))))


def surface_point(recipe: dict, u: float, v: float) -> tuple[tuple[int, int, int], int, float]:
    p = recipe["parameters"]
    kind, seed = recipe["id"], recipe["seed"]
    grain = max(2, round(p["grain"] * 2))
    coarse = fbm(u, v, grain, seed)
    fine = noise(u, v, grain * 8, seed + 37)
    if "basalt" in kind:
        pit = max(0.0, 0.33 - noise(u, v, grain * 12, seed + 131)) * 4.0
        height = 0.52 + (coarse - 0.5) * 0.47 + (fine - 0.5) * 0.22 - pit * 0.36
        tone = 0.82 + (coarse - 0.5) * 0.52 + (fine - 0.5) * 0.19 - pit * 0.35
        rough = p["roughness"] + (fine - 0.5) * 0.14 + pit * 0.08
    elif "slate" in kind:
        strata = math.sin((v * (grain * 5) + (coarse - 0.5) * 0.12) * math.tau)
        height = 0.50 + (coarse - 0.5) * 0.24 + strata * 0.17 + (fine - 0.5) * 0.06
        tone = 0.88 + (coarse - 0.5) * 0.42 + strata * 0.07
        rough = p["roughness"] + strata * 0.05 + (fine - 0.5) * 0.10
    else:
        pores = max(0.0, 0.38 - noise(u, v, grain * 10, seed + 109)) * 2.5
        height = 0.56 + (coarse - 0.5) * 0.25 + (fine - 0.5) * 0.23 - pores * 0.31
        tone = 0.91 + (coarse - 0.5) * 0.35 + (fine - 0.5) * 0.23 - pores * 0.17
        rough = p["roughness"] + pores * 0.12 - (fine - 0.5) * 0.10
    hue = p["base_color_rgb"]
    color = tuple(_clamp(channel * tone) for channel in hue)
    return color, _clamp(rough * 255), min(1.0, max(0.0, height))


def generate_arrays(recipe: dict, size: int) -> dict[str, list[bytes]]:
    if size < 16 or size > 2048:
        raise ValueError("size must be between 16 and 2048")
    period = size - 1
    albedo_rows: list[bytes] = []
    rough_rows: list[bytes] = []
    height_values: list[list[float]] = []
    for y in range(size):
        u_y = y / period
        colors = bytearray()
        roughness = bytearray()
        heights = []
        for x in range(size):
            color, rough, h = surface_point(recipe, x / period, u_y)
            colors.extend(color)
            roughness.append(rough)
            heights.append(h)
        albedo_rows.append(bytes(colors))
        rough_rows.append(bytes(roughness))
        height_values.append(heights)
    h_rows = []
    n_rows = []
    tile_mm = recipe["physical_tile_mm"]
    relief_mm = recipe["parameters"]["height_mm"]
    step_mm = tile_mm / period
    for y in range(size):
        grays = bytearray()
        normals = bytearray()
        py = y % period
        for x in range(size):
            px = x % period
            h = height_values[y][x]
            grays.extend(struct.pack(">H", _clamp(h * 65535, 65535)))
            dx = (height_values[py][(px + 1) % period] - height_values[py][(px - 1) % period]) * relief_mm / (2 * step_mm)
            dy = (height_values[(py + 1) % period][px] - height_values[(py - 1) % period][px]) * relief_mm / (2 * step_mm)
            length = math.sqrt(dx * dx + dy * dy + 1)
            normals.extend((_clamp(127.5 * (1 - dx / length)),
                            _clamp(127.5 * (1 - dy / length)),
                            _clamp(127.5 * (1 + 1 / length))))
        h_rows.append(bytes(grays))
        n_rows.append(bytes(normals))
    # A 2x2 preview makes tile repetition and seams visible.
    preview = []
    for y in range(2 * size):
        row = albedo_rows[y % period]
        repeated = b"".join(row[x * 3:x * 3 + 3] for x in range(period))
        preview.append(repeated + repeated)
    return {"basecolor": albedo_rows, "roughness": rough_rows,
            "height": h_rows, "normal": n_rows, "preview": preview}


def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def encode_png(width: int, height: int, color_type: int, bit_depth: int, rows: list[bytes]) -> bytes:
    channels = {0: 1, 2: 3}[color_type]
    expected = width * channels * bit_depth // 8
    if len(rows) != height or any(len(row) != expected for row in rows):
        raise ValueError("PNG row dimensions mismatch")
    payload = b"".join(b"\0" + row for row in rows)
    return (PNG_MAGIC + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(payload, 9)) + _chunk(b"IEND", b""))


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate(recipe: dict, output: Path, size: int) -> dict:
    directory = output / recipe["id"]
    directory.mkdir(parents=True, exist_ok=True)
    arrays = generate_arrays(recipe, size)
    formats = {"basecolor": (2, 8, size), "roughness": (0, 8, size),
               "height": (0, 16, size), "normal": (2, 8, size), "preview": (2, 8, 2 * (size - 1))}
    artifacts = {}
    for name in MAP_NAMES:
        kind, bits, width = formats[name]
        rows = arrays[name]
        data = encode_png(width, len(rows), kind, bits, rows)
        filename = name + ".png"
        (directory / filename).write_bytes(data)
        artifacts[name] = {"file": filename, "sha256": _hash(data),
                           "bytes": len(data), "width": width, "height": len(rows),
                           "bit_depth": bits, "color_type": kind}
    manifest = {
        "material_id": recipe["id"],
        "source_license": recipe["license"],
        "seed": recipe["seed"],
        "size": size,
        "physical_tile_mm": recipe["physical_tile_mm"],
        "height_mm": recipe["parameters"]["height_mm"],
        "normal_convention": "OpenGL/+Y",
        "status": recipe["status"],
        "prototype_not_calibrated": True,
        "seam_test": "periodic-noise-opposing-edge-texels-identical",
        "files": artifacts
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def verify_outputs(path: Path) -> list[str]:
    problems = []
    manifests = sorted(path.glob("*/manifest.json")) if path.exists() else []
    if not manifests:
        return ["no generated material manifests found"]
    for file in manifests:
        manifest = json.loads(file.read_text(encoding="utf-8"))
        for name, entry in manifest.get("files", {}).items():
            artifact = file.parent / entry["file"]
            if not artifact.is_file():
                problems.append(f"{name}: missing {artifact}")
                continue
            data = artifact.read_bytes()
            if _hash(data) != entry["sha256"] or not data.startswith(PNG_MAGIC):
                problems.append(f"{name}: corrupt or mismatched {artifact}")
            elif (width := struct.unpack(">I", data[16:20])[0]) != entry["width"]:
                problems.append(f"{name}: wrong PNG dimensions {width}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    commands.add_parser("list")
    validation = commands.add_parser("validate")
    validation.add_argument("--out", type=Path, help="also validate generated output hashes")
    creation = commands.add_parser("generate")
    creation.add_argument("--material", help="material ID (default: all)")
    creation.add_argument("--size", type=int, default=256)
    creation.add_argument("--out", type=Path, default=ROOT / "web" / "assets")
    args = parser.parse_args(argv)
    recipes = all_recipes()
    errors = [f"{r.get('id', 'unknown')}: {problem}" for r in recipes for problem in recipe_errors(r)]
    ids = [r.get("id") for r in recipes]
    if len(set(ids)) != len(ids):
        errors.append("duplicate material id")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if args.command == "doctor":
        print("Python:", sys.version.split()[0])
        print("Blender:", shutil.which("blender") or "not installed (optional for texture generation)")
        print("Material recipes:", len(recipes), "| Python texture generator: ready")
        return 0
    if args.command == "list":
        for recipe in recipes:
            print(recipe["id"], "-", recipe["display_name"], f"({recipe['status']})")
        return 0
    if args.command == "validate":
        if args.out:
            errors = verify_outputs(args.out)
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 1
        print(f"Validated {len(recipes)} material recipes" + (" and generated hashes" if args.out else ""))
        return 0
    chosen = [r for r in recipes if not args.material or r["id"] == args.material]
    if not chosen:
        parser.error(f"unknown material {args.material!r}")
    if args.size < 16 or args.size > 2048:
        parser.error("--size must be between 16 and 2048")
    args.out.mkdir(parents=True, exist_ok=True)
    catalog = []
    for recipe in chosen:
        result = generate(recipe, args.out, args.size)
        catalog.append({"id": recipe["id"], "display_name": recipe["display_name"],
                        "family": recipe["family"], "status": recipe["status"],
                        "preview": f"assets/{recipe['id']}/preview.png",
                        "basecolor": f"assets/{recipe['id']}/basecolor.png"})
        print(f"{recipe['id']}: {len(result['files'])} files, {result['size']}px")
    (args.out / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
