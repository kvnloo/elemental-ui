# Tern plugin

`integrations/tern/elemental-ui` themes [Tern](https://stencil.so/tern)'s
window chrome (page background, pane headers, status line) with a material's
base color under a legibility veil. Terminal grids are left alone.

```bash
python3 tools/elemental.py pack
python3 tools/elemental.py tern                       # textures/, elemental.css, materials.luau
tern plugin link "$PWD/integrations/tern/elemental-ui"
```

| File | Tracked | Role |
|---|---|---|
| `plugin.toml` | yes | schema 1 manifest: `window = "window.luau"`, `styles = ["elemental.css"]` |
| `window.luau` | yes | palette commands `Elemental: <name>` and `Elemental: plain chrome` that swap a `tern.css("material", …)` sheet |
| `elemental.css` | generated | default material (`--default`, basalt) as the manifest sheet, which also reaches Tern's web tab |
| `materials.luau` | generated | the material list and per-material CSS |
| `textures/<id>.png` | generated | copies of each pack's base color (Tern resolves `url()` against the plugin directory) |

## How it is styled

```css
body        { background-image: linear-gradient(rgb(12 11 10 / .58), …), url(textures/<id>.png); background-size: auto, 256px 256px; }
.tn-head    { … 128px tiles under a lighter veil … }
#statusline { … 128px tiles … }
```

Tern's CSS engine supports multi-layer backgrounds, `background-size` and
`repeat`, raster `url()` up to 4096 px, `backdrop-filter` and
`mix-blend-mode`. It does **not** support custom shaders, so Tern gets the
CSS tier. Relighting stays with the web and native runtimes.

## Verified

- `tern plugin list --json` in an isolated `TERN_CONFIG_DIR` reports
  `"status": "ready"` with the generated sheet.
- Applying the sheet in `tern serve` (`tern ctl css elemental …`) paints the
  tab bar and the gutters while the terminal panes are unchanged.
  Screenshots: `reports/generated/tern/{before,after}.png`.
- **Not verified:** loading the plugin in a real Tern window. `tern shot`
  and `tern serve` do not load plugins.

The scenario `tests/tern/elemental-chrome.txt` (two panes, then a shot) is
kept for running `tern shot` once plugin loading is available there.
