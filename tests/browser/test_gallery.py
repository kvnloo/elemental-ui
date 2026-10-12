"""Browser QA: run after generating web/assets; GPL-3.0-only.

Install: pip install playwright==1.57.0
         python -m playwright install --with-deps chromium
Run:     python -m unittest discover -s tests/browser -v
Optional: ELEMENTAL_BROWSER_BIN=/usr/bin/chromium
"""
from __future__ import annotations

import functools
import http.server
import json
import os
from pathlib import Path
import threading
import unittest

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
REPORTS = ROOT / "reports" / "generated" / "browser"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


class GalleryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (WEB / "assets" / "catalog.json").is_file():
            raise RuntimeError("First run: python tools/elemental.py generate --size 128 --out web/assets")
        handler = functools.partial(QuietHandler, directory=str(WEB))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/"
        cls.playwright = sync_playwright().start()
        binary = os.environ.get("ELEMENTAL_BROWSER_BIN")
        cls.browser = cls.playwright.chromium.launch(
            headless=True, **({"executable_path": binary} if binary else {})
        )
        REPORTS.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=3)

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={"width": 1440, "height": 900}, device_scale_factor=1
        )
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda err: self.errors.append(str(err)))
        self.page.goto(self.url, wait_until="networkidle")
        expect(self.page.locator("#material-grid button.el-card")).to_have_count(3)

    def tearDown(self):
        self.assertEqual([], self.errors, "Browser JavaScript errors")
        self.context.close()

    def test_generated_materials_and_images(self):
        self.assertEqual(1, self.page.locator("#material-grid button[aria-pressed=true]").count())
        expect(self.page.locator("#asset-status")).to_contain_text("Generated local texture")
        images = self.page.locator("#material-grid img")
        self.assertEqual(3, images.count())
        for img in images.all():
            img.scroll_into_view_if_needed()
            expect(img).to_have_js_property("complete", True)
            self.assertTrue(img.evaluate("node => node.naturalWidth > 0"), img.get_attribute("src"))
            self.assertEqual("", img.get_attribute("alt"))

    def test_keyboard_and_semantic_states(self):
        choices = self.page.locator("#material-switch button")
        choices.nth(0).focus()
        self.page.keyboard.press("Tab")
        self.assertTrue(choices.nth(1).evaluate("node => document.activeElement === node"))
        self.page.keyboard.press("Enter")
        expect(choices.nth(1)).to_have_attribute("aria-pressed", "true")
        expect(self.page.locator("#current-id")).to_have_text("geo.slate.layered.v1")
        self.page.keyboard.press("Tab")
        self.page.keyboard.press("Space")
        expect(choices.nth(2)).to_have_attribute("aria-pressed", "true")
        self.assertEqual(1, self.page.locator("#material-switch button[aria-pressed=true]").count())
        expect(self.page.locator("#current-material")).to_have_text("Porous Limestone")
        self.assertTrue(self.page.get_by_role("button", name="Disabled state").is_disabled())
        self.page.get_by_role("button", name="Explore").click()
        expect(self.page.locator("#interaction-status")).to_contain_text("Explore activated with Porous Limestone")

    def test_search_filter_slider(self):
        search = self.page.get_by_role("searchbox", name="Search materials")
        search.fill("slate")
        expect(self.page.locator("#material-grid button.el-card")).to_have_count(1)
        expect(self.page.locator("#material-count")).to_have_text("1")
        search.fill("nonexistent-type")
        expect(self.page.locator("#material-grid button.el-card")).to_have_count(0)
        expect(self.page.locator("#material-grid")).to_contain_text("No materials match")
        search.fill("")
        expect(self.page.locator("#material-grid button.el-card")).to_have_count(3)
        slider = self.page.get_by_role("slider", name="Visual depth:")
        slider.focus()
        slider.press("Home")
        expect(self.page.locator("#depth-output")).to_have_text("0")
        slider.press("End")
        expect(self.page.locator("#depth-output")).to_have_text("100")

    def test_mobile_width_and_reduced_motion(self):
        viewports = []
        for width, height in ((360, 780), (768, 1024), (1440, 900)):
            self.page.set_viewport_size({"width": width, "height": height})
            self.page.evaluate("window.scrollTo(0, 0)")
            metrics = self.page.evaluate("""() => ({
                width: innerWidth,
                scrollWidth: document.documentElement.scrollWidth,
                scrollHeight: document.documentElement.scrollHeight,
                cardCount: document.querySelectorAll('#material-grid button.el-card').length
            })""")
            self.assertLessEqual(metrics["scrollWidth"], width + 1, f"Horizontal overflow: {metrics}")
            self.assertEqual(3, metrics["cardCount"])
            filename = f"gallery-{width}.png"
            self.page.screenshot(path=str(REPORTS / filename), full_page=True, animations="disabled")
            metrics["screenshot"] = filename
            viewports.append(metrics)
        self.page.emulate_media(reduced_motion="reduce")
        duration = self.page.locator("#explore-button").evaluate(
            "node => getComputedStyle(node).transitionDuration"
        )
        self.assertEqual("0s", duration)
        maps = list((WEB / "assets").rglob("*.png"))
        self.assertEqual(15, len(maps), "expected 5 generated PNGs per material")
        receipt = {
            "asset_bytes": sum(p.stat().st_size for p in maps),
            "map_count": len(maps),
            "viewports": viewports,
            "reduced_motion_transition": duration,
            "limitations": "Local-browser functional smoke tests, not Lighthouse or real-phone benchmarks.",
        }
        (REPORTS / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
