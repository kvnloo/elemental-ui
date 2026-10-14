# Getting started

## Requirements

| Tool | Used for | Required? |
|---|---|---|
| Python 3.10+ | recipes, draft texture generator, packs, tests | yes |
| Rust (stable, 1.88+) | `elemental-pack`, `elemental-render` | for native rendering |
| Node 20+ / npm | web runtime, docs | for the web runtime and these docs |
| [naga-cli](https://crates.io/crates/naga-cli) 30.0.1 | regenerating the WebGL2 GLSL | only when the shader changes |
| Chromium + Playwright, Pillow | browser QA | for `tests/browser` |
| Blender 4.5+ or the `bpy` wheel | Blender PBR smoke renders | optional |
| `avifenc` | AVIF base color variants in packs | optional |

## Five-minute tour

```bash
git clone https://github.com/kvnloo/elemental-ui && cd elemental-ui

# 1. Recipes → runtime packs
python3 tools/elemental.py validate
python3 tools/elemental.py pack            # packs/<id>/pack.json + maps
python3 tools/elemental.py pack --verify

# 2. Native render with the shared shader
cargo build --release
./target/release/elemental-render packs/geo.basalt.vesicular.v1 basalt.png 1920 1080

# 3. Web runtime and demo
npm install && npm run build
python3 -m http.server 8080               # open http://localhost:8080/packages/web/demo/

# 4. These docs (with live swatches from your packs)
npm run docs:dev
```

## Use it on a page

```html
<script type="module" src="/elemental-ui.js"></script>

<elemental-surface material="geo.basalt.vesicular.v1" packs="/packs" light="pointer"
                   style="display:block; min-height:220px; border-radius:18px; padding:22px">
  <h2>Vesicular Basalt</h2>
  <button type="button">Explore</button>
</elemental-surface>
```

The element shows the base color tile as a CSS background at once, then
upgrades to WebGL2 or WebGPU when the browser supports one. See
[Web runtime](/runtime/web) for every attribute and event.

## Run the checks

```bash
python3 -m unittest discover -s tests -v                       # recipes, generator, packs, catalog
cargo test --release                                           # pack contract, shader, GPU render
npm run glsl:check -w @elemental-ui/web && npm run typecheck   # GLSL drift, TypeScript
ELEMENTAL_BROWSER_BIN=/usr/bin/chromium python3 -m unittest tests.browser.test_runtime -v
```

[Testing & CI](/reference/testing) lists what each suite proves and what it does not.

::: warning Draft materials
The three packs that exist today come from the dependency-free procedural
draft generator. They test the plumbing. They are not the target look. The
[image generation pipeline](/pipeline/image-generation) replaces them.
:::
