# Repository tour

```text
elemental-ui/
├── catalog/taxonomy.json        the 353 materials to generate (family › class › material)
├── materials/<family>/*.json    recipes for materials that exist today (schema: schemas/material.schema.json)
├── schemas/material.schema.json JSON Schema for recipes
├── tools/
│   ├── elemental.py             CLI: doctor, list, validate, generate, pack, tern
│   └── polyhaven.py             bounded, verified importer for credited CC0 scans
├── shaders/elemental_surface.wgsl   the one lighting shader
├── crates/                      Rust workspace (Cargo.toml at the root)
│   ├── elemental-pack/          read and verify elemental-pack/1
│   └── elemental-render/        wgpu renderer + `elemental-render` CLI
├── packages/web/                @elemental-ui/web: <elemental-surface>
│   ├── src/                     element, WebGPU and WebGL2 renderers, pack loader, params
│   ├── src/generated/           GLSL ES 3.00 generated from the WGSL by naga (committed)
│   ├── scripts/                 build.mjs (esbuild), build-glsl.mjs (naga + drift check)
│   └── demo/                    index.html (gallery), parity.html (test fixture)
├── integrations/
│   ├── hyprland/elemental-wallpaper   per-monitor wallpapers via hyprctl + swaybg
│   └── tern/elemental-ui/       Tern plugin (manifest, window.luau; textures generated)
├── blender/                     Cycles preview scene, PBR pack render, exposure guard
├── web/                         v0.1 static gallery and CSS component library
├── references/
│   ├── geological.json          curated CC0 scan candidates (Poly Haven)
│   └── dream-loop/              AI visual-target catalog and prompt templates
├── tests/                       unittest suites; tests/browser (Playwright); tests/tern (scenario)
├── docs/                        this site (VitePress) and the long-form project docs
└── .github/workflows/           CI: core, browser QA, runtime packs, Blender smoke, reference smoke
```

## What is generated and what is tracked

| Path | Tracked? | Produced by |
|---|---|---|
| `packs/` | no | `tools/elemental.py pack` |
| `web/assets/`, `outputs/` | no | `tools/elemental.py generate`, Blender scripts |
| `target/` | no | `cargo build` |
| `packages/web/dist/` | no | `npm run build` |
| `packages/web/src/generated/surface-glsl.ts` | **yes** | `npm run glsl -w @elemental-ui/web` (CI checks it is current) |
| `integrations/tern/elemental-ui/{textures,elemental.css,materials.luau}` | no | `tools/elemental.py tern` |
| `reports/generated/` | no | test runs (receipts, screenshots, parity images) |
| `docs/public/live/` | no | `npm run docs:prepare` |

## Branches and history

- `main`: recipes, the draft generator, the v0.1 gallery, Blender smoke and
  the reference importer (PRs #12–#14).
- `feat/runtime-scaffold` (PR #15): the catalog, packs, shared shader, the
  native, web, Hyprland and Tern drivers, and these docs.
- `feat/scan-vs-procedural-cycles`: unmerged. It stages a credited CC0 scan
  against procedural basalt under a matched Cycles setup.
