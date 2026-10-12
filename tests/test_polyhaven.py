"""Safe, offline source selection and integrity tests. GPL-3.0-only."""
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("polyhaven", ROOT / "tools" / "polyhaven.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def listing():
    out = {}
    for name in ("Diffuse", "Rough", "nor_gl", "disp"):
        out[name] = {"1k": {"png": {
            "url": f"https://dl.polyhaven.org/file/ph-assets/Textures/png/1k/{name}.png",
            "size": 5,
            "md5": hashlib.md5(b"hello", usedforsecurity=False).hexdigest()
        }}}
    return out


class RefTests(unittest.TestCase):
    def test_catalog_has_credited_distinct_sources(self):
        items = m.catalog()["assets"]
        self.assertGreaterEqual(len(items), 3)
        self.assertEqual(len(items), len({a["asset_id"] for a in items}))
        for item in items:
            self.assertTrue(item["creators"])
            self.assertEqual("CC0-1.0", item["license"])
            self.assertIn("not_equivalent_to", item)
            self.assertEqual(item["asset_id"], m.chosen_asset(item["asset_id"])["asset_id"])

    def test_select_three_mandatory_maps_and_optional_height(self):
        found = m.select_maps(listing())
        self.assertEqual(set(found), {"diffuse", "roughness", "normal_gl", "height"})
        source = listing()
        source.pop("disp")
        self.assertEqual(set(m.select_maps(source)), {"diffuse", "roughness", "normal_gl"})

    def test_missing_required_or_unsupported_resolution_fail(self):
        source = listing()
        source.pop("nor_gl")
        with self.assertRaisesRegex(m.ReferenceError, "normal_gl"):
            m.select_maps(source)
        with self.assertRaisesRegex(m.ReferenceError, "resolutions"):
            m.select_maps(listing(), "8k")

    def test_reject_unsafe_origin_and_forged_host(self):
        self.assertTrue(m.trusted_url("https://dl.polyhaven.org/file/a.png", api=False))
        for url in ("http://dl.polyhaven.org/file/a.png",
                    "https://dl.polyhaven.org.attacker.example/a.png",
                    "https://evil.example/a.png",
                    "file:///etc/passwd"):
            self.assertFalse(m.trusted_url(url, api=False), url)
        source = listing()
        source["Diffuse"]["1k"]["png"]["url"] = "https://evil.example/a.png"
        with self.assertRaisesRegex(m.ReferenceError, "unsafe"):
            m.select_maps(source)

    def test_reject_unbounded_sizes_and_incomplete_md5(self):
        source = listing()
        source["Rough"]["1k"]["png"]["size"] = m.MAX_FILE_BYTES + 1
        with self.assertRaisesRegex(m.ReferenceError, "unbounded"):
            m.select_maps(source)
        source = listing()
        source["Rough"]["1k"]["png"]["md5"] = "abc"
        with self.assertRaisesRegex(m.ReferenceError, "unsafe"):
            m.select_maps(source)

    def test_exact_stream_integrity_and_reject_corruption(self):
        class Response(io.BytesIO):
            def __init__(self, body):
                super().__init__(body)
            def geturl(self):
                return "https://dl.polyhaven.org/file/p.png"
        data = m.select_maps(listing())["diffuse"]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "diffuse.png"
            with patch.object(m, "_open", return_value=Response(b"hello")):
                receipt = m.download_map(data, target)
            self.assertEqual(target.read_bytes(), b"hello")
            self.assertEqual(receipt["sha256"], hashlib.sha256(b"hello").hexdigest())
            with patch.object(m, "_open", return_value=Response(b"world")):
                with self.assertRaisesRegex(m.ReferenceError, "MD5 mismatch"):
                    m.download_map(data, target)
            self.assertFalse(target.with_name("diffuse.png.partial").exists())
            self.assertEqual(target.read_bytes(), b"hello")  # atomic good copy retained

    def test_asset_ids_must_be_curated(self):
        for asset_id in ("../etc", "unknown_scan", "https://evil.example/x"):
            with self.assertRaises(m.ReferenceError):
                m.chosen_asset(asset_id)


if __name__ == "__main__":
    unittest.main()
