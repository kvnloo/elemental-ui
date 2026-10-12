# Browser QA (P0 wave)

**Purpose:** Verify the actual generated-gallery experience, not mock elements. See [issue #4](https://github.com/kvnloo/elemental-ui/issues/4).

Run locally after generating the texture pack:



```bash
python3 tools/elemental.py generate --size 128 --out web/assets
python3 -m pip install playwright==1.57.0
python3 -m playwright install chromium
python3 -m unittest discover -s tests/browser -v
```

For a system Chromium install, set `ELEMENTAL_BROWSER_BIN=/usr/bin/chromium`.

The suite checks:
- Real images (not broken placeholders) and actual generated catalog contents.
- Keyboard Tab/Enter/Space and pressed states on material selectors.
- Disabled controls, status announcements, search result filtering and slider values.
- 360px, 768px and 1440px viewports with no horizontal document overflow.
- `prefers-reduced-motion` CSS response.

Receipts: `reports/generated/browser/receipt.json` and screenshots at each viewport, uploaded as `browser-qa-receipts` GitHub Actions artifact. The screenshots are for human inspection; this wave is **not** a full WCAG audit or Lighthouse/mobile-device performance proof. Next: axe checks, measured phone traces, visual baseline review and concrete latency thresholds.

All PNGs remain untracked. No copyrighted STONE design/reference images are downloaded or redistributed.
