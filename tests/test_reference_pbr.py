"""No-network tests for truthful reference identity and map integrity."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
s = importlib.util.spec_from_file_location("reference_pbr", ROOT / "blender" / "reference_pbr.py")
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)


def chunk(label, value):
    return struct.pack(">I", len(value)) + label + value + struct.pack(">I", zlib.crc32(label + value))


def png(mode):
    n = 1024
    # Actual valid 1K monochrome/RGB PNG, small due to zlib compression.
    channels = 3 if mode == 2 else 1
    ihdr = struct.pack(">IIBBBBB", n, n, 8, mode, 0, 0, 0)
    row = b"\0" + (b"\x83" * (n * channels))
    return m.PNG_HEADER + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(row * n, 9)) + chunk(b"IEND", b"")


class RefImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.folder = self.root / "dark_rock" / "1k"
        self.folder.mkdir(parents=True)
        source = next(x for x in json.loads(m.CATALOG.read_text())["assets"] if x["asset_id"] == "dark_rock")
        self.rec = dict(asset_id="dark_rock", source_license="CC0-1.0",
                        source_url=source["source_url"], creators=source["creators"],
                        provider="Poly Haven", resolution="1k",
                        status="unverified-physical-identity", files={})
        for key in ("diffuse", "roughness", "normal_gl", "height"):
            data = png(2 if key in ("diffuse", "normal_gl") else 0)
            path = self.folder / (key + ".png")
            path.write_bytes(data)
            self.rec["files"][key] = dict(
                file=path.name, bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
                source_md5=hashlib.md5(data, usedforsecurity=False).hexdigest(),
                source_url=f"https://dl.polyhaven.org/file/{key}.png")
        self.save()

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        (self.folder / "reference-receipt.json").write_text(json.dumps(self.rec))

    def test_all_maps_validate_and_normalize(self):
        receipt, maps = m.validate_reference_pack(self.root, "dark_rock")
        self.assertEqual("CC0-1.0", receipt["source_license"])
        self.assertEqual(set(maps), {"basecolor", "roughness", "normal", "height"})

    def test_reject_forged_credits(self):
        self.rec["creators"] = ["Unknown"]
        self.save()
        with self.assertRaisesRegex(m.ReferencePackError, "credit"):
            m.validate_reference_pack(self.root, "dark_rock")

    def test_reject_fake_basalt_identity(self):
        self.rec["status"] = "basalt"
        self.save()
        with self.assertRaisesRegex(m.ReferencePackError, "identity"):
            m.validate_reference_pack(self.root, "dark_rock")

    def test_refuse_symlink_or_traversal(self):
        self.rec["files"]["diffuse"]["file"] = "../else.png"
        self.save()
        with self.assertRaisesRegex(m.ReferencePackError, "filename"):
            m.validate_reference_pack(self.root, "dark_rock")

    def test_reject_modified_pixels(self):
        with (self.folder / "normal_gl.png").open("ab") as f:
            f.write(b"x")
        with self.assertRaisesRegex(m.ReferencePackError, "(length|SHA256)"):
            m.validate_reference_pack(self.root, "dark_rock")

    def test_source_host_must_be_trusted(self):
        self.rec["files"]["roughness"]["source_url"] = "https://dl.polyhaven.org.evil.tld/file.png"
        self.save()
        with self.assertRaisesRegex(m.ReferencePackError, "host"):
            m.validate_reference_pack(self.root, "dark_rock")

    def test_not_all_pbr_scans_are_basalt(self):
        with self.assertRaisesRegex(m.ReferencePackError, "curated"):
            m.validate_reference_pack(self.root, "basalt")

    def test_optional_height_map(self):
        self.rec["files"].pop("height")
        self.save()
        _, maps = m.validate_reference_pack(self.root, "dark_rock")
        self.assertEqual(set(maps), {"basecolor", "roughness", "normal"})


if __name__ == "__main__":
    unittest.main()
