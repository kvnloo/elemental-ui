"""Validate deterministic PBR map packs before assigning them in Blender.

Only Python standard-library dependencies. GPL-3.0-only.
A validated map pack is NOT proof of physically accurate or photorealistic appearance.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MATERIAL_ID = re.compile(r"^(geo|bot|aq|fauna|atm)\.[a-z0-9-]+(?:\.[a-z0-9-]+)+\.v[1-9][0-9]*$")
MAP_SPEC = {
    "basecolor": (8, 2),     # sRGB RGB8
    "roughness": (8, 0),     # linear grayscale8
    "normal": (8, 2),        # linear RGB8, tangent +Y
    "height": (16, 0),       # linear grayscale16
}


class MaterialPackError(ValueError):
    """Missing or invalid rendered material asset."""


def validate_maps(map_root: str | Path, material_id: str) -> tuple[dict, dict[str, Path]]:
    """Return manifest and audited absolute paths to the four mandatory PBR maps.

    Refuse traversal, incorrect channels/depth, tampering, scale mismatch and
    incorrect material identity. A path must be a filename, not a subdirectory.
    """
    if not MATERIAL_ID.fullmatch(material_id):
        raise MaterialPackError("invalid material ID")
    folder = Path(map_root).expanduser().resolve() / material_id
    source = folder / "manifest.json"
    if not source.is_file():
        raise MaterialPackError(f"missing manifest: {source}")
    try:
        manifest = json.loads(source.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MaterialPackError(f"invalid JSON manifest: {source}") from exc
    if manifest.get("material_id") != material_id:
        raise MaterialPackError("material identity mismatch")
    if manifest.get("source_license") != "GPL-3.0-only":
        raise MaterialPackError("first-party material map license missing")
    if manifest.get("normal_convention") != "OpenGL/+Y":
        raise MaterialPackError("expected OpenGL/+Y normal map")
    if (not isinstance(manifest.get("physical_tile_mm"), (int, float))
            or manifest["physical_tile_mm"] <= 0):
        raise MaterialPackError("physical tile scale missing")
    size = manifest.get("size")
    if type(size) is not int or not 16 <= size <= 2048:
        raise MaterialPackError("invalid tile size")

    output: dict[str, Path] = {}
    for tag, (bits, color_type) in MAP_SPEC.items():
        item = manifest.get("files", {}).get(tag)
        if not isinstance(item, dict):
            raise MaterialPackError(f"missing {tag} metadata")
        name = item.get("file")
        if not isinstance(name, str) or not name.endswith(".png") or Path(name).name != name:
            raise MaterialPackError(f"invalid {tag} file name")
        candidate = (folder / name).resolve()
        if candidate.parent != folder.resolve() or not candidate.is_file():
            raise MaterialPackError(f"missing or unsafe {tag} path: {name}")
        raw = candidate.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item.get("sha256"):
            raise MaterialPackError(f"{tag} checksum mismatch")
        if len(raw) < 33 or not raw.startswith(PNG_SIGNATURE) or raw[12:16] != b"IHDR":
            raise MaterialPackError(f"{tag} is not a PNG")
        width, height, depth, channels, compression, filtering, interlace = struct.unpack(
            ">IIBBBBB", raw[16:29]
        )
        if (width != size or height != size or depth != bits or channels != color_type
                or compression != 0 or filtering != 0 or interlace != 0):
            raise MaterialPackError(f"{tag} dimensions/format mismatch")
        if (item.get("width") != width or item.get("height") != height
                or item.get("bit_depth") != bits or item.get("color_type") != channels
                or item.get("bytes") != len(raw)):
            raise MaterialPackError(f"{tag} metadata mismatch")
        output[tag] = candidate
    return manifest, output
