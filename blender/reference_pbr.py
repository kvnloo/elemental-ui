"""Validate a curated, independently licensed CC0 reference pack before Blender use.

No network calls. Do not pass third-party scans off as a first-party GPL material.
GPL-3.0-only (source); external images retain their original CC0 terms.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references" / "geological.json"
PNG_HEADER = b"\x89PNG\r\n\x1a\n"
ID = re.compile(r"^[a-z0-9_]{3,48}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MD5 = re.compile(r"^[0-9a-f]{32}$")
MAPS = {"diffuse": "basecolor", "roughness": "roughness", "normal_gl": "normal"}
MAX_IMAGE_BYTES = 24 * 1024 * 1024


class ReferencePackError(ValueError):
    pass


def _trusted_download(url: str) -> bool:
    parsed = urlparse(url)
    return (parsed.scheme == "https" and parsed.hostname is not None
            and (parsed.hostname == "dl.polyhaven.org" or parsed.hostname.endswith(".polyhaven.org"))
            and not parsed.username and not parsed.password and parsed.port is None)


def _verified_png(raw: bytes, resolution: str, map_name: str) -> None:
    if len(raw) < 45 or not raw.startswith(PNG_HEADER) or raw[12:16] != b"IHDR":
        raise ReferencePackError(f"{map_name}: not a PNG")
    width, height, bits, channels, compression, filtering, interlace = struct.unpack(">IIBBBBB", raw[16:29])
    expected = {"1k": 1024, "2k": 2048}[resolution]
    if ((width, height) != (expected, expected) or bits not in (8, 16)
            or channels not in (0, 2, 4, 6) or compression or filtering or interlace):
        raise ReferencePackError(f"{map_name}: unexpected PNG dimensions / format")
    if map_name == "normal_gl" and channels not in (2, 6):
        raise ReferencePackError("normal_gl requires RGB/RGBA channels")


def validate_reference_pack(
    root: str | Path, asset_id: str, resolution: str = "1k"
) -> tuple[dict, dict[str, Path]]:
    """Validate source, human credits, file names, lengths and cryptographic hashes.

    Returns a receipt and normalized Blender node paths (basecolor, roughness,
    normal and optional height). Validity is not mineral identification.
    """
    if not ID.fullmatch(asset_id) or resolution not in ("1k", "2k"):
        raise ReferencePackError("invalid asset ID or resolution")
    curated = json.loads(CATALOG.read_text(encoding="utf-8"))
    candidates = [x for x in curated.get("assets", []) if x.get("asset_id") == asset_id]
    if len(candidates) != 1 or candidates[0].get("license") != "CC0-1.0":
        raise ReferencePackError("asset is not curated as independent CC0 reference")
    source = candidates[0]
    folder = (Path(root).expanduser().resolve() / asset_id / resolution).resolve()
    receipt_path = folder / "reference-receipt.json"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise ReferencePackError("missing or invalid reference receipt") from exc
    for key, expected in (
        ("asset_id", asset_id), ("source_license", "CC0-1.0"),
        ("source_url", source["source_url"]), ("creators", source["creators"]),
        ("provider", "Poly Haven"), ("resolution", resolution)
    ):
        if receipt.get(key) != expected:
            raise ReferencePackError(f"source/credit mismatch: {key}")
    if receipt.get("status") != "unverified-physical-identity":
        raise ReferencePackError("unexpected scan material identity status")
    if not isinstance(receipt.get("files"), dict):
        raise ReferencePackError("invalid file manifest")
    output = {}
    for source_key, shader_key in tuple(MAPS.items()) + (("height", "height"),):
        item = receipt["files"].get(source_key)
        if item is None and source_key == "height":
            continue
        if not isinstance(item, dict):
            raise ReferencePackError(f"missing {source_key} map")
        filename = item.get("file")
        if (not isinstance(filename, str)
                or filename not in (f"{source_key}.png", f"{source_key}.jpg")):
            raise ReferencePackError(f"unsafe {source_key} filename")
        path = (folder / filename).resolve()
        if path.parent != folder or not path.is_file():
            raise ReferencePackError(f"{source_key}: invalid file path")
        advertised = item.get("bytes")
        if type(advertised) is not int or not 0 < advertised <= MAX_IMAGE_BYTES:
            raise ReferencePackError(f"{source_key}: oversized or invalid byte count")
        sha = item.get("sha256")
        md5 = item.get("source_md5")
        if (not isinstance(sha, str) or not SHA256.fullmatch(sha)
                or not isinstance(md5, str) or not MD5.fullmatch(md5)):
            raise ReferencePackError(f"{source_key}: missing checksums")
        if not _trusted_download(item.get("source_url", "")):
            raise ReferencePackError(f"{source_key}: untrusted source host")
        if path.stat().st_size != advertised:
            raise ReferencePackError(f"{source_key}: length mismatch")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha:
            raise ReferencePackError(f"{source_key}: SHA256 mismatch")
        if hashlib.md5(raw, usedforsecurity=False).hexdigest() != md5:
            raise ReferencePackError(f"{source_key}: source MD5 mismatch")
        if filename.endswith(".png"):
            _verified_png(raw, resolution, source_key)
        else:
            # Blender may load JPEG, but reject for normal/height precision.
            if source_key in ("normal_gl", "height"):
                raise ReferencePackError(f"{source_key}: require PNG")
            if raw[:3] != b"\xff\xd8\xff":
                raise ReferencePackError(f"{source_key}: not a JPEG")
        output[shader_key] = path
    return receipt, output
