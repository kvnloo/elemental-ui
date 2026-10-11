# elemental-ui

**An open-source, Earth-sourced material system for the web.**

Create physically inspired materials in Blender, export deterministic PBR texture packs, and use them in fast, accessible interfaces. Geological materials are the first vertical slice; botanical, aquatic, fauna, and atmospheric families follow.

**License:** GNU GPL v3.0 **only** (\`GPL-3.0-only\`). Copyright © 2026 Kevin Rajan and contributors. See [LICENSE](LICENSE) and [asset provenance](docs/PROVENANCE.md).

## Current state

- Three **experimental procedural** geology presets: vesicular basalt, layered slate, porous limestone.
- Dependency-free Python texture generator with repeatable seeds; creates seamless base color / roughness / normal / height PNGs, a contact sheet preview, file hashes and metadata.
- Blender Python scene generator for a stone UI slab and controlled studio render. Blender is optional for generating the 2D maps.
- Accessible, dependency-free web preview and reusable CSS primitive styles.
- Material contract, full [roadmap](docs/ROADMAP.md), regression checks and GitHub CI.

**Important:** These are first-pass procedural studies, **not yet photogrammetry-quality or physically calibrated assets**. Material measurements, curated references, baking parity with Blender and perceptual QA are tracked in the roadmap. No third-party reference images are included in this repository.

## Quickstart

Python 3.10+ is sufficient for the generator and tests. No packages to install.

\`\`\`bash
python3 tools/elemental.py doctor
python3 tools/elemental.py validate
python3 tools/elemental.py generate --size 256 --out web/assets
python3 -m unittest discover -s tests -v
python3 -m http.server 8080 -d web
\`\`\`

Open **http://localhost:8080/** for the material catalog and tactile UI controls. Use \`--material geo.basalt.vesicular.v1\` to generate just basalt or \`--size 512\` for a larger texture set. Each output has a deterministic hash manifest; generated assets remain untracked.

## Blender render (optional)

Run with Blender 4.2+ (tested-version pin and render-quality verification are pending):

\`\`\`bash
blender -b --python blender/stone_preview.py -- --material geo.basalt.vesicular.v1 --out outputs/blender --samples 32
\`\`\`

The Blender route produces a procedural-stone component render and a \`.blend\` project. The CPU PNG generator is a **different draft material implementation**; the two are not assumed visually or numerically equivalent. Blender PBR texture baking and calibrated parity are follow-up work.

## Package layout

- \`materials/geological/\`: recipe source of truth and explicit licensing
- \`schemas/\`: JSON Schema contract
- \`tools/elemental.py\`: deterministic texture CLI and validation
- \`blender/stone_preview.py\`: \`bpy\` geometry, shader and studio render
- \`web/\`: static material gallery and CSS component library
- \`tests/\`: generator, seams, manifest and CLI tests
- \`docs/ROADMAP.md\`: complete phase plan and acceptance criteria

## Principles

1. **The perception matters, not polygon count:** deliver cheap 2D assets first and use WebGL selectively.
2. **Materials must be inspectable:** physical scale, seed, recipe, source credit, checksums and limitations.
3. **Controls stay semantic HTML:** textures never bake in text, focus, or interaction state.
4. **No unlicensed source photos:** visual inspiration is not redistribution permission.

Contributions: [CONTRIBUTING.md](CONTRIBUTING.md).