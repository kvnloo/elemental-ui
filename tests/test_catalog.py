"""Catalog and pack contract tests. GPL-3.0-only."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import elemental  # noqa: E402

KINDS = {"tileable-surface", "bounded-object", "animated-surface", "volumetric-effect"}


class TaxonomyTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((ROOT / "catalog" / "taxonomy.json").read_text(encoding="utf-8"))
        self.materials = self.doc["materials"]

    def test_ids_are_unique_and_well_formed(self):
        ids = [m["id"] for m in self.materials]
        self.assertEqual(len(ids), len(set(ids)))
        for material_id in ids:
            self.assertRegex(material_id, elemental.ID_RE)

    def test_atlas_codes_cover_all_48_reference_materials(self):
        codes = [m["atlas_code"] for m in self.materials if m["atlas_code"]]
        self.assertEqual(len(codes), 48)
        self.assertEqual(len(set(codes)), 48)

    def test_kinds_and_hierarchy(self):
        self.assertEqual(set(self.doc["kinds"]), KINDS)
        for m in self.materials:
            self.assertIn(m["kind"], KINDS, m["id"])
            self.assertTrue(m["family"] and m["class"], m["id"])

    def test_every_recipe_is_in_the_catalog(self):
        catalog = {m["id"] for m in self.materials}
        for recipe in elemental.all_recipes():
            self.assertIn(recipe["id"], catalog)


class PackTests(unittest.TestCase):
    def test_pack_is_one_period_and_hashes_verify(self):
        recipe = next(r for r in elemental.all_recipes() if r["id"] == "geo.slate.layered.v1")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            manifest = elemental.build_pack(recipe, out, 32)
            self.assertEqual(manifest["schema"], elemental.PACK_SCHEMA)
            self.assertEqual(manifest["class"], "metamorphic")
            for name, entry in manifest["maps"].items():
                data = (out / recipe["id"] / entry["file"]).read_bytes()
                self.assertEqual(elemental._hash(data), entry["sha256"], name)
                self.assertEqual((entry["width"], entry["height"]), (32, 32))
            self.assertEqual(manifest["maps"]["basecolor"]["color_space"], "srgb")
            self.assertEqual(manifest["maps"]["height"]["bit_depth"], 16)
            self.assertEqual(elemental.verify_packs(out), [])

    def test_pack_drops_the_duplicated_seam_texel(self):
        recipe = next(r for r in elemental.all_recipes() if r["id"] == "geo.basalt.vesicular.v1")
        full = elemental.generate_arrays(recipe, 33)["basecolor"]
        # The draft generator repeats texel 0 at texel 32; a pack keeps texels 0..31.
        self.assertEqual(full[0][:3], full[0][32 * 3:33 * 3])
        with tempfile.TemporaryDirectory() as tmp:
            manifest = elemental.build_pack(recipe, Path(tmp), 32)
            self.assertEqual(manifest["maps"]["basecolor"]["width"], 32)


if __name__ == "__main__":
    unittest.main()
