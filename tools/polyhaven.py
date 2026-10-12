#!/usr/bin/env python3
"""Opt-in, bounded Poly Haven texture reference importer (GPL-3.0-only code).

Source imagery stays independently CC0. No downloads happen during import,
"list", or offline unit tests. The live API requires a "Powered by Poly Haven"
credit and an identifying User-Agent per the official API terms.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import ssl
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "references" / "geological.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "external" / "polyhaven"
API_BASE = "https://api.polyhaven.com/files"
USER_AGENT = "elemental-ui/0.1 (https://github.com/kvnloo/elemental-ui)"
ASSET_ID_RE = re.compile(r"^[a-z0-9_]{3,48}$")
MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")
MAP_ALIASES = {
    "diffuse": ("Diffuse", "diff", "diffuse", "basecolor", "albedo"),
    "roughness": ("Rough", "rough", "roughness"),
    "normal_gl": ("nor_gl", "Nor_gl", "Normal_GL", "normal_gl"),
    "height": ("disp", "Disp", "displacement", "Displacement"),
}
MAX_FILE_BYTES = 24 * 1024 * 1024
BLOCK = 256 * 1024


class ReferenceError(ValueError):
    pass


def catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def chosen_asset(asset_id: str) -> dict:
    if not ASSET_ID_RE.fullmatch(asset_id):
        raise ReferenceError("invalid source identifier")
    matches = [a for a in catalog()["assets"] if a["asset_id"] == asset_id]
    if len(matches) != 1:
        raise ReferenceError("source is not approved in references/geological.json")
    if matches[0].get("license") != "CC0-1.0":
        raise ReferenceError("source is not marked CC0-1.0")
    return matches[0]


def trusted_url(url: str, *, api: bool) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port:
        return False
    if api:
        return host == "api.polyhaven.com"
    return host == "dl.polyhaven.org" or host.endswith(".polyhaven.org")


def select_maps(raw: dict, resolution: str = "1k") -> dict:
    """Identify official map variants; require Diffuse, Roughness, GL normal.

    JSON map nesting is API map key -> resolution -> format -> {url,md5,size}.
    `disp` may not exist; it is explicitly optional.
    """
    if resolution not in ("1k", "2k"):
        raise ReferenceError("Only 1k and 2k source resolutions are permitted")
    if not isinstance(raw, dict):
        raise ReferenceError("invalid file listing")
    selected = {}
    for material_map, aliases in MAP_ALIASES.items():
        entry = next((raw[k] for k in aliases if isinstance(raw.get(k), dict)), None)
        if not entry:
            if material_map == "height":
                continue
            raise ReferenceError(f"required Poly Haven map missing: {material_map}")
        bucket = entry.get(resolution)
        if not isinstance(bucket, dict):
            if material_map == "height":
                continue
            raise ReferenceError(f"resolution {resolution} missing for {material_map}")
        available = next(((suffix, bucket[suffix]) for suffix in ("png", "jpg") if isinstance(bucket.get(suffix), dict)), None)
        if available is None:
            if material_map == "height":
                continue
            raise ReferenceError(f"png/jpg missing for {material_map}")
        ext, attrs = available
        url = attrs.get("url")
        md5 = attrs.get("md5")
        size = attrs.get("size")
        if (not isinstance(url, str) or not trusted_url(url, api=False)
                or not isinstance(md5, str) or not MD5_RE.fullmatch(md5)):
            raise ReferenceError(f"unsafe or unverifiable {material_map} download metadata")
        if type(size) is not int or not 0 < size <= MAX_FILE_BYTES:
            raise ReferenceError(f"unbounded or invalid {material_map} size: {size!r}")
        selected[material_map] = {
            "source_url": url,
            "source_md5": md5.lower(),
            "source_bytes": size,
            "ext": ext,
        }
    return selected


def _open(url: str, *, api: bool, timeout: int = 25):
    if not trusted_url(url, api=api):
        raise ReferenceError("refusing non-HTTPS or non-Poly-Haven URL")
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json" if api else "image/png,image/jpeg,*/*",
        "Referer": "https://github.com/kvnloo/elemental-ui",
    })
    response = urlopen(req, timeout=timeout, context=ssl.create_default_context())
    final_url = response.geturl()
    if not trusted_url(final_url, api=api):
        response.close()
        raise ReferenceError(f"unexpected redirect host: {urlparse(final_url).hostname}")
    return response


def api_file_list(asset_id: str) -> dict:
    chosen_asset(asset_id)
    with _open(f"{API_BASE}/{asset_id}", api=True) as response:
        raw = response.read(512 * 1024 + 1)
    if len(raw) > 512 * 1024:
        raise ReferenceError("metadata response exceeded 512 KiB")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ReferenceError("API did not return JSON") from exc
    if not isinstance(data, dict):
        raise ReferenceError("API returned invalid file tree")
    return data


def download_map(data: dict, target: Path) -> dict:
    """Stream one known map, validate MD5 and bytes, record independent SHA256."""
    expected_bytes = data["source_bytes"]
    expected_md5 = data["source_md5"]
    if expected_bytes > MAX_FILE_BYTES:
        raise ReferenceError("download too large")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".partial")
    sha = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    count = 0
    try:
        with _open(data["source_url"], api=False) as response, partial.open("wb") as f:
            while True:
                block = response.read(min(BLOCK, expected_bytes + 1 - count))
                if not block:
                    break
                count += len(block)
                if count > expected_bytes or count > MAX_FILE_BYTES:
                    raise ReferenceError("download exceeded advertised source size")
                sha.update(block)
                md5.update(block)
                f.write(block)
        if count != expected_bytes:
            raise ReferenceError(f"source file size mismatch ({count} != {expected_bytes})")
        if md5.hexdigest() != expected_md5:
            raise ReferenceError(f"source MD5 mismatch for {target.name}")
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)
    return {"file": target.name, "source_md5": expected_md5,
            "sha256": sha.hexdigest(), "bytes": count,
            "source_url": data["source_url"]}


def render_sheet(folder: Path, manifest: dict) -> Path:
    """Optional contact sheet with original unaltered source files kept separately."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise ReferenceError("Install Pillow for --preview") from exc
    order = [k for k in ("diffuse", "roughness", "normal_gl", "height") if k in manifest["files"]]
    cell = 320
    sheet = Image.new("RGB", (cell * len(order), 370), (29, 30, 31))
    d = ImageDraw.Draw(sheet)
    for idx, kind in enumerate(order):
        image_path = folder / manifest["files"][kind]["file"]
        with Image.open(image_path) as loaded:
            im = loaded.convert("RGB")
        im.thumbnail((300, 300))
        if im.size != (300, 300):
            im = im.resize((300, 300), Image.Resampling.LANCZOS)
        sheet.paste(im, (idx * cell + 10, 15))
        d.text((idx * cell + 10, 323), kind.upper(), fill=(233, 231, 224))
    outfile = folder / "contact-sheet.jpg"
    sheet.save(outfile, quality=86)
    return outfile


def import_reference(asset_id: str, resolution: str, out: Path, *,
                     preview: bool, probe: bool) -> dict:
    item = chosen_asset(asset_id)
    selected = select_maps(api_file_list(asset_id), resolution)
    dest = (out / asset_id / resolution).resolve()
    doc = {
        "asset_id": asset_id,
        "display_name": item["display_name"],
        "source_license": "CC0-1.0",
        "source_url": item["source_url"],
        "creators": item["creators"],
        "category": item["category"],
        "use": item["use"],
        "not_equivalent_to": item["not_equivalent_to"],
        "scale_statement": item["scale_statement"],
        "provider": "Poly Haven",
        "api_credit": "Powered by Poly Haven",
        "api_terms": "https://github.com/Poly-Haven/Public-API/blob/master/ToS.md",
        "resolution": resolution,
        "status": "unverified-physical-identity",
        "files": selected if probe else {},
    }
    if probe:
        return doc
    dest.mkdir(parents=True, exist_ok=True)
    for kind, entry in selected.items():
        doc["files"][kind] = download_map(entry, dest / f"{kind}.{entry['ext']}")
    if preview:
        render_sheet(dest, doc)
    (dest / "reference-receipt.json").write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return doc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["list", "probe", "fetch"])
    parser.add_argument("asset_id", nargs="?")
    parser.add_argument("--resolution", choices=["1k", "2k"], default="1k")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preview", action="store_true", help="render a comparison sheet (requires Pillow)")
    args = parser.parse_args(argv)
    if args.command == "list":
        for entry in catalog()["assets"]:
            print(f"{entry['asset_id']:22} {entry['display_name']} — {', '.join(entry['creators'])}")
        return 0
    if not args.asset_id:
        parser.error("asset_id is required for probe or fetch")
    try:
        result = import_reference(args.asset_id, args.resolution, args.out,
                                  preview=args.preview, probe=args.command == "probe")
    except (ReferenceError, OSError) as exc:
        print(f"Reference import failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    print("\nPowered by Poly Haven · downloaded imagery remains CC0-1.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
