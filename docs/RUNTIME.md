# Runtime architecture

One material pack format and one lighting shader, painted by thin drivers on
every target. The idea is the one Stencil's slab uses: a single core decides
the result and the drivers only put pixels on screen, and the drivers are
checked against each other.

```text
catalog/taxonomy.json            what we want to generate (family > class > material)
materials/<family>/*.json        recipes for materials that exist today
        │  tools/elemental.py pack
        ▼
packs/<id>/pack.json             elemental-pack/1: maps + hashes + provenance
packs/<id>/{basecolor,normal,roughness,height}.png (+ basecolor.avif)
        │
        │  shaders/elemental_surface.wgsl   ← the only lighting source
        ├──────────────► native   crates/elemental-render (wgpu: Vulkan/Metal/DX12)
        │                          └─ integrations/hyprland/elemental-wallpaper
        ├──────────────► web      packages/web <elemental-surface>
        │                          ├─ webgpu  (the WGSL as-is)
        │                          ├─ webgl2  (GLSL ES 3.00 generated from the WGSL by naga)
        │                          └─ css     (base color tile, no GPU work)
        └──────────────► Tern     integrations/tern/elemental-ui (CSS tier in Tern's engine)
```

## Pack contract (`elemental-pack/1`)

- Maps are GPU-repeatable: the image is exactly one period (power of two), so
  `repeat` sampling has no duplicated seam texel.
- `basecolor` is sRGB; `normal` (OpenGL, +Y up), `roughness` and `height`
  (16-bit) are linear data.
- Every file and variant carries a SHA-256; `tools/elemental.py pack --verify`
  and `elemental_pack::Pack::verify` check them.
- `source.calibrated` is `false` for every pack today. The packs are draft
  procedural studies until the image-generation and Blender map pipeline
  replaces them.

## Shader contract

`struct Params` is 64 bytes (`resolution`, `tile_px`, `relief`, `light`,
`light_color`, `view`). The shader writes sRGB-encoded output into a non-sRGB
target, so every backend produces the same bytes. Lighting: Lambert diffuse,
GGX distribution, Smith-Schlick visibility, Schlick Fresnel for a dielectric,
Reinhard tone mapping.

## Performance rules

- GPU tiers draw on demand (pointer, resize, attribute change, coming back on
  screen). There is no free-running animation loop, so an idle page costs
  nothing.
- The CSS layer paints first and stays underneath. A GPU tier that is
  unavailable or still loading never leaves a blank box.
- One `GPUDevice` and shader module serve every element on the page.
- Device pixel ratio is capped at 2.
- Not done yet: mipmaps and KTX2/Basis GPU compression (`toktx` is not
  installed here), and texture streaming for very large surfaces (the Quackles
  RFC-003 virtual texture path).

## Verification (2026-10-13, this host)

| Check | Result |
|---|---|
| `cargo test` (pack hashes, Params layout, naga validation of the WGSL, offscreen render on GPU) | pass, RTX 3080 Ti via Vulkan |
| Native render, 1024×640 | 8–25 ms per material, including upload |
| WebGL2 vs native, 512×320 basalt | mean 0.0, max 0 (byte-identical) |
| WebGPU (off-canvas readback, SwiftShader) vs native | mean 0.03, max 1/255 |
| CSS tier | paints the textured base color |
| Pointer relighting (WebGL2) | moves the light; headless rAF p95 16.8 ms |
| Bundle | `dist/elemental-ui.js` ≈ 18 KB minified |
| Tern plugin | `tern plugin list` reports `ready` in an isolated config; its sheet applied in `tern serve` paints the window chrome |
| Hyprland wallpaper | renders 1920×1080 per monitor (DP-1, DP-2) in 13–29 ms; `--apply` not run |

Gaps that need a real window:

- A WebGPU **canvas** cannot present in headless Chromium here (the adapter is
  SwiftShader). WebGPU canvas output and pointer relighting on WebGPU must be
  checked in Chrome on the desktop.
- `tern shot` and `tern serve` do not load plugins. Loading the plugin in a
  real Tern window needs `tern plugin link` on the desktop.

Rerun everything:

```sh
python3 tools/elemental.py pack && python3 tools/elemental.py pack --verify
cargo test --release && cargo build --release
npm install && npm run glsl:check -w @elemental-ui/web && npm run build
ELEMENTAL_BROWSER_BIN=/usr/bin/chromium python3 -m unittest tests.browser.test_runtime -v
```
