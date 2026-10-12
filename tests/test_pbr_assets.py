"""Contract tests for a Blender-independent verified PBR map import. GPL-3.0-only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pbr_assets", ROOT / "blender" / "pbr_assets.py")
pbr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pbr)


def chunk(label, data):
    return struct.pack(">I", len(data)) + label + data + struct.pack(">I", zlib.crc32(label + data))


def png(tile, bits, mode):
    stride = tile * (1 if mode == 0 else 3) * (bits // 8)
    header = struct.pack(">IIBBBBB", tile, tile, bits, mode, 0, 0, 0)
    return pbr.PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress((b"\0" + b"\x7f" * stride) * tile)) + chunk(b"IEND", b"")


class PackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.material = "geo.basalt.vesicular.v1"
        self.folder = self.root / self.material
        self.folder.mkdir()
        self.data = {
            "material_id": self.material,
            "size": 16,
            "source_license": "GPL-3.0-only",
            "normal_convention": "OpenGL/+Y",
            "physical_tile_mm": 240,
            "files": {},
        }
        for tag, (bits, mode) in pbr.MAP_SPEC.items():
            data = png(16, bits, mode)
            name = f"{tag}.png"
            (self.folder / name).write_bytes(data)
            self.data["files"][tag] = {
                "file": name, "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data), "width": 16, "height": 16,
                "bit_depth": bits, "color_type": mode,
            }
        self.dump()

    def tearDown(self):
        self.tmp.cleanup()

    def dump(self):
        (self.folder / "manifest.json").write_text(json.dumps(self.data), encoding="utf-8")

    def test_four_maps_verified(self):
        metadata, paths = pbr.validate_maps(self.root, self.material)
        self.assertEqual(set(pbr.MAP_SPEC), set(paths))
        self.assertEqual(self.material, metadata["material_id"])
        self.assertTrue(all(x.is_file() for x in paths.values()))

    def test_tampering_detected(self):
        (self.folder / "normal.png").write_bytes(b"tampered")
        with self.assertRaisesRegex(pbr.MaterialPackError, "checksum mismatch"):
            pbr.validate_maps(self.root, self.material)

    def test_traversal_rejected(self):
        self.data["files"]["normal"]["file"] = "../other.png"
        self.dump()
        with self.assertRaisesRegex(pbr.MaterialPackError, "invalid normal file name"):
            pbr.validate_maps(self.root, self.material)

    def test_wrong_format_rejected_even_with_valid_hash(self):
        raw = png(16, 8, 0)
        path = self.folder / "height.png"
        path.write_bytes(raw)
        self.data["files"]["height"].update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        self.dump()
        with self.assertRaisesRegex(pbr.MaterialPackError, "format mismatch"):
            pbr.validate_maps(self.root, self.material)

    def test_wrong_license_rejected(self):
        self.data["source_license"] = "unknown"
        self.dump()
        with self.assertRaisesRegex(pbr.MaterialPackError, "license"):
            pbr.validate_maps(self.root, self.material)


if __name__ == "__main__":
    unittest.main()
