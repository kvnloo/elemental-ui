"""Runtime QA for @elemental-ui/web: tiers, native/web pixel parity, interaction cost.

GPL-3.0-only.

Prerequisites (from the repository root):
    python3 tools/elemental.py pack
    cargo build --release            # elemental-render, for the parity reference
    npm install && npm run build
Run:
    python3 -m unittest tests.browser.test_runtime -v
Optional: ELEMENTAL_BROWSER_BIN=/usr/bin/chromium

The WebGPU shader path is checked by rendering off-canvas and reading the pixels
back (`renderPixelsWebGPU`): headless Chromium exposes only a SwiftShader WebGPU
adapter whose canvases never present, so a screenshot of a WebGPU canvas shows
the CSS layer underneath. WebGPU canvas presentation and pointer relighting on
WebGPU must be confirmed in a real browser window. Tiers that cannot start here
are reported as skipped, never as passed.
"""
from __future__ import annotations

import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import unittest

from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports" / "generated" / "runtime"
PACKS = ROOT / "packs"
RENDER_BIN = ROOT / "target" / "release" / "elemental-render"
DIST = ROOT / "packages" / "web" / "dist" / "elemental-ui.js"
MATERIAL = "geo.basalt.vesicular.v1"
WIDTH, HEIGHT = 512, 320
FLAGS = ["--enable-unsafe-webgpu", "--ignore-gpu-blocklist", "--enable-features=Vulkan", "--use-angle=vulkan"]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


def diff_stats(a: Image.Image, b: Image.Image) -> dict:
    delta = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    raw = delta.tobytes()
    values = sorted(max(raw[i:i + 3]) for i in range(0, len(raw), 3))
    return {"mean": sum(ImageStat.Stat(delta).mean) / 3,
            "p99": values[int(len(values) * 0.99)], "max": values[-1]}


@unittest.skipUnless((PACKS / "index.json").is_file() and DIST.is_file(), "build packs and packages/web first")
class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        REPORTS.mkdir(parents=True, exist_ok=True)
        handler = functools.partial(QuietHandler, directory=str(ROOT))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.pw = sync_playwright().start()
        binary = os.environ.get("ELEMENTAL_BROWSER_BIN") or shutil.which("chromium")
        cls.browser = cls.pw.chromium.launch(executable_path=binary, args=FLAGS)
        cls.results: dict = {}

    @classmethod
    def tearDownClass(cls):
        (REPORTS / "runtime-report.json").write_text(json.dumps(cls.results, indent=2) + "\n")
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()

    def page(self, **kw):
        page = self.browser.new_page(viewport={"width": 900, "height": 700}, device_scale_factor=1, **kw)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        return page, errors

    def render_tier(self, tier: str) -> Image.Image:
        page, errors = self.page()
        mode = "&mode=pixels" if tier == "webgpu-pixels" else ""
        page.goto(f"{self.base}/packages/web/demo/parity.html?tier={tier}&w={WIDTH}&h={HEIGHT}&material={MATERIAL}{mode}")
        try:
            page.wait_for_function("document.body.dataset.ready", timeout=15000)
        except Exception:
            got = page.evaluate("document.querySelector('elemental-surface')?.dataset.tier")
            page.close()
            self.skipTest(f"{tier} tier unavailable in this browser (painting {got})")
        self.assertEqual(page.evaluate("document.body.dataset.ready"), tier)
        path = REPORTS / f"{MATERIAL}.{tier}.png"
        target = "canvas" if tier == "webgpu-pixels" else "elemental-surface"
        page.locator(target).screenshot(path=str(path))
        page.close()
        self.assertEqual(errors, [])
        return Image.open(path)

    def native_reference(self) -> Image.Image:
        if not RENDER_BIN.is_file():
            self.skipTest("cargo build --release first")
        path = REPORTS / f"{MATERIAL}.native.png"
        out = subprocess.run([str(RENDER_BIN), str(PACKS / MATERIAL), str(path), str(WIDTH), str(HEIGHT)],
                             capture_output=True, text=True)
        if out.returncode != 0:
            self.skipTest(f"no native GPU: {out.stderr.strip()}")
        self.results["native"] = out.stdout.strip()
        return Image.open(path)

    def check_parity(self, tier: str):
        native = self.native_reference()
        web = self.render_tier(tier)
        self.assertEqual(web.size, (WIDTH, HEIGHT))
        stats = diff_stats(native, web)
        self.results[f"parity_{tier}"] = stats
        # Same shader, same inputs: only filtering/rounding differences remain.
        self.assertLess(stats["mean"], 1.5, stats)
        self.assertLessEqual(stats["p99"], 8, stats)

    def test_webgl2_matches_native(self):
        self.check_parity("webgl2")

    def test_webgpu_matches_native(self):
        self.check_parity("webgpu-pixels")

    def test_css_tier_paints_base_color(self):
        img = self.render_tier("css")
        stat = ImageStat.Stat(img.convert("L"))
        self.results["css"] = {"mean": stat.mean[0], "stddev": stat.stddev[0]}
        self.assertGreater(stat.stddev[0], 3, "CSS tier is flat; texture did not load")

    def test_demo_surfaces_html_and_pointer_light(self):
        page, errors = self.page()
        # WebGL2 is the GPU tier that presents in headless Chromium (see module doc).
        page.goto(f"{self.base}/packages/web/demo/?tier=webgl2")
        page.wait_for_function(
            "[...document.querySelectorAll('elemental-surface')].length === 3 &&"
            "[...document.querySelectorAll('elemental-surface')].every(e => e.dataset.tier && e.dataset.tier !== 'css')",
            timeout=20000)
        tiers = page.evaluate("[...document.querySelectorAll('elemental-surface')].map(e => e.dataset.tier)")
        self.results["demo_tiers"] = tiers
        surface = page.locator("elemental-surface").first
        # Content stays real HTML above the material.
        button = surface.get_by_role("button", name="Explore")
        button.focus()
        self.assertTrue(page.evaluate("document.activeElement.textContent === 'Explore'"))
        box = surface.bounding_box()
        page.mouse.move(box["x"] + 10, box["y"] + 10)
        page.wait_for_timeout(100)
        before = REPORTS / "demo-light-topleft.png"
        surface.screenshot(path=str(before))
        page.mouse.move(box["x"] + box["width"] - 10, box["y"] + box["height"] - 10)
        page.wait_for_timeout(100)
        after = REPORTS / "demo-light-bottomright.png"
        surface.screenshot(path=str(after))
        moved = diff_stats(Image.open(before), Image.open(after))
        self.results["pointer_light_delta"] = moved
        self.assertGreater(moved["mean"], 2, "moving the pointer did not move the light")
        page.screenshot(path=str(REPORTS / "demo.png"), full_page=True)

        # Interaction cost: 120 pointer moves, frame intervals measured in-page.
        page.evaluate("""() => { window.__frames = []; let last = performance.now();
            const tick = (t) => { window.__frames.push(t - last); last = t; if (window.__frames.length < 400) requestAnimationFrame(tick); };
            requestAnimationFrame(tick); }""")
        for i in range(120):
            page.mouse.move(box["x"] + 10 + i * (box["width"] - 20) / 120, box["y"] + box["height"] / 2)
        page.wait_for_timeout(200)
        frames = sorted(page.evaluate("window.__frames.slice(5)"))
        p95 = frames[int(len(frames) * 0.95)] if frames else None
        self.results["pointer_frames"] = {"count": len(frames), "p95_ms": p95,
                                          "note": "headless frame pacing; not a device benchmark"}
        page.close()
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
