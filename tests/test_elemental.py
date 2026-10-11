"""Regression tests for material contracts and lossless periodic PNG generation."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("elemental", ROOT / "tools" / "elemental.py")
elemental = importlib.util.module_from_spec(spec)
spec.loader.exec_module(elemental)


def unpack_png_rows(content):
    """Minimal zlib PNG extractor: our generator always writes filter=0."""
    import zlib
    assert content.startswith(elemental.PNG_MAGIC)
    width, height, depth, color, _, _, _ = struct.unpack(">IIBBBBB", content[16:29])
    payload = b""
    offset = 8
    while offset < len(content):
        n = struct.unpack(">I", content[offset:offset + 4])[0]
        kind = content[offset + 4:offset + 8]
        if kind == b"IDAT":
            payload += content[offset + 8:offset + 8 + n]
        offset += 12 + n
    raw = zlib.decompress(payload)
    stride = width * (1 if color == 0 else 3) * (depth // 8)
    rows = []
    for y in range(height):
        begin = y * (stride + 1)
        assert raw[begin] == 0
        rows.append(raw[begin + 1:begin + stride + 1])
    return width, height, depth, rows


class MaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes = elemental.all_recipes()

    def test_catalog_has_three_distinct_recipes(self):
        self.assertEqual(len(self.recipes), 3)
        self.assertEqual(len({r["id"] for r in self.recipes}), 3)
        for recipe in self.recipes:
            self.assertEqual([], elemental.recipe_errors(recipe))

    def test_invalid_recipe_fails(self):
        bad = dict(self.recipes[0], license="MIT")
        self.assertIn("recipe license must be GPL-3.0-only in this first-party collection",
                      elemental.recipe_errors(bad))

    def test_seed_affects_output(self):
        recipe = self.recipes[0]
        altered = dict(recipe, seed=recipe["seed"] + 1)
        self.assertNotEqual(elemental.generate_arrays(recipe, 17)["basecolor"],
                            elemental.generate_arrays(altered, 17)["basecolor"])

    def test_determinism_seams_and_manifest(self):
        for recipe in self.recipes:
            with self.subTest(material=recipe["id"]), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                first = elemental.generate(recipe, folder, 32)
                first_data = [(folder / recipe["id"] / f"{name}.png").read_bytes()
                              for name in elemental.MAP_NAMES]
                second = elemental.generate(recipe, folder, 32)
                self.assertEqual(first, second)
                self.assertEqual(first_data, [(folder / recipe["id"] / f"{name}.png").read_bytes()
                                              for name in elemental.MAP_NAMES])
                self.assertEqual([], elemental.verify_outputs(folder))
                for name, data in zip(elemental.MAP_NAMES[:4], first_data[:4]):
                    width, height, depth, rows = unpack_png_rows(data)
                    self.assertEqual(width, height)
                    self.assertEqual(rows[0], rows[-1], f"{name} has vertical seam")
                    channels = (1 if name in ("height", "roughness") else 3)
                    step = channels * depth // 8
                    for row in rows:
                        self.assertEqual(row[:step], row[-step:], f"{name} has horizontal seam")
                preview_w, preview_h, _, _ = unpack_png_rows(first_data[4])
                self.assertEqual(preview_w, 62)
                self.assertEqual(preview_h, 64)

    def test_tampered_asset_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            elemental.generate(self.recipes[0], folder, 16)
            altered = folder / self.recipes[0]["id"] / "normal.png"
            altered.write_bytes(altered.read_bytes() + b"tampered")
            self.assertTrue(elemental.verify_outputs(folder))

    def test_cli_doctor_and_validate(self):
        self.assertEqual(0, elemental.main(["doctor"]))
        self.assertEqual(0, elemental.main(["validate"]))
        self.assertEqual(0, elemental.main(["list"]))


if __name__ == "__main__":
    unittest.main()
