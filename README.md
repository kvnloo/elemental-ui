# elemental-ui

**An open-source, Earth-sourced material system for the web.**

Create physically inspired materials in Blender, export deterministic PBR texture packs, and use them in fast, accessible interfaces. Geological materials are the first vertical slice; botanical, aquatic, fauna, and atmospheric families follow.

**License:** GNU GPL v3.0 **only** (`GPL-3.0-only`). Copyright © 2026 Kevin Rajan and contributors. See [LICENSE](LICENSE) and [asset provenance](docs/PROVENANCE.md).

## Current state

- Three **experimental procedural** geology presets: vesicular basalt, layered slate, porous limestone.
- Dependency-free Python texture generator with repeatable seeds; creates seamless base color / roughness / normal / height PNGs, a contact sheet preview, file hashes and metadata.
- Blender Python scene generator for a stone UI slab and controlled studio render. Blender is optional for generating the 2D maps.
- Accessible, dependency-free web preview and reusable CSS primitive styles.
- Material contract, full [roadmap](docs/ROADMAP.md), regression checks and GitHub CI.

**Important:** These are first-pass procedural studies, **not yet photogrammetry-quality or physically calibrated assets**. Material measurements, curated references, baking parity with Blender and perceptual QA are tracked in the roadmap. No third-party reference images are included in this repository.

## Quickstart

Python 3.10+ is sufficient for the generator and tests. No packages to install.

```bash
python3 tools/elemental.py doctor
python3 tools/elemental.py validate
python3 tools/elemental.py generate --size 256 --out web/assets
python3 -m unittest discover -s tests -v
python3 -m http.server 8080 -d web
```

Open **http://localhost:8080/** for the material catalog and tactile UI controls. Use `--material geo.basalt.vesicular.v1` to generate just basalt or `--size 512` for a larger texture set. Each output has a deterministic hash manifest; generated assets remain untracked.

## Blender render (optional)

Run with Blender 4.2+ (tested-version pin and render-quality verification are pending):

```bash
blender -b --python blender/stone_preview.py -- --material geo.basalt.vesicular.v1 --out outputs/blender --samples 32
```

The Blender route produces a procedural-stone component render and a `.blend` project. The CPU PNG generator is a **different draft material implementation**; the two are not assumed visually or numerically equivalent. Blender PBR texture baking and calibrated parity are follow-up work.

## Runtime (web, native, desktop, Tern)

Packs (`elemental-pack/1`) are relit by one shader, `shaders/elemental_surface.wgsl`, on every target:

```bash
python3 tools/elemental.py pack                  # packs/<id>/ (GPU-repeatable maps + manifest)
cargo build --release                            # native wgpu renderer
./target/release/elemental-render packs/geo.basalt.vesicular.v1 basalt.png 1920 1080
npm install && npm run build                     # @elemental-ui/web → packages/web/dist/
python3 -m http.server 8080                      # open /packages/web/demo/
```

```html
<script type="module" src="/packages/web/dist/elemental-ui.js"></script>
<elemental-surface material="geo.basalt.vesicular.v1" packs="/packs" light="pointer">
  <button>Explore</button>
</elemental-surface>
```

The element picks WebGPU, then WebGL2 (GLSL generated from the same WGSL by naga), then a CSS tile. It draws only when something changes. Desktop: `integrations/hyprland/elemental-wallpaper` renders per-monitor wallpapers. Tern: `integrations/tern/elemental-ui`. Architecture, measured parity and known gaps: [docs/RUNTIME.md](docs/RUNTIME.md); background research: [docs/RUNTIME_RESEARCH.md](docs/RUNTIME_RESEARCH.md). The material hierarchy to generate (56 materials, 5 families) is `catalog/taxonomy.json`.

## Package layout

- `materials/geological/`: recipe source of truth and explicit licensing
- `schemas/`: JSON Schema contract
- `tools/elemental.py`: deterministic texture CLI and validation
- `blender/stone_preview.py`: `bpy` geometry, shader and studio render
- `web/`: static material gallery and CSS component library
- `tests/`: generator, seams, manifest and CLI tests
- `docs/ROADMAP.md`: complete phase plan and acceptance criteria
- `catalog/taxonomy.json`: material hierarchy to mass-generate
- `shaders/`: the shared WGSL lighting shader
- `crates/`: `elemental-pack` (pack reader) and `elemental-render` (native wgpu renderer + CLI)
- `packages/web/`: `<elemental-surface>` web runtime
- `integrations/`: Hyprland wallpaper and Tern plugin

## Principles

1. **The perception matters, not polygon count:** deliver cheap 2D assets first and use WebGL selectively.
2. **Materials must be inspectable:** physical scale, seed, recipe, source credit, checksums and limitations.
3. **Controls stay semantic HTML:** textures never bake in text, focus, or interaction state.
4. **No unlicensed source photos:** visual inspiration is not redistribution permission.

Contributions: [CONTRIBUTING.md](CONTRIBUTING.md).