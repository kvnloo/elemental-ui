# Packs (`elemental-pack/1`)

A pack is the unit every runtime consumes: one directory per material with
GPU-repeatable maps and a manifest. It is written by
`python3 tools/elemental.py pack` and read by `crates/elemental-pack` (Rust)
and `packages/web/src/pack.ts` (TypeScript).

```text
packs/
├── index.json                       { "schema": "elemental-pack/1", "packs": [{ id, display_name, family, kind, pack }] }
└── geo.basalt.vesicular.v1/
    ├── pack.json
    ├── basecolor.png  (+ basecolor.avif when avifenc is installed)
    ├── normal.png
    ├── roughness.png
    └── height.png     (16-bit)
```

## `pack.json`

```json
{
  "schema": "elemental-pack/1",
  "id": "geo.basalt.vesicular.v1",
  "display_name": "Vesicular Basalt",
  "family": "geological",
  "class": "igneous",
  "kind": "tileable-surface",
  "license": "GPL-3.0-only",
  "status": "prototype",
  "physical_tile_mm": 240,
  "height_mm": 1.8,
  "normal_convention": "opengl-y-up",
  "tiling": "repeat",
  "source": { "kind": "procedural-draft", "generator": "tools/elemental.py", "seed": 84017, "calibrated": false },
  "maps": {
    "basecolor": { "file": "basecolor.png", "mime": "image/png", "width": 512, "height": 512, "bit_depth": 8,
                   "color_space": "srgb", "sha256": "…", "bytes": 124745,
                   "variants": [{ "file": "basecolor.avif", "mime": "image/avif", "sha256": "…", "bytes": 7152 }] },
    "normal":    { "color_space": "linear", … },
    "roughness": { "color_space": "linear", … },
    "height":    { "bit_depth": 16, "color_space": "linear", … }
  }
}
```

## Rules

- **One period per map.** The draft generator duplicates texel 0 at its far
  edge for its seam test. `pack` generates `size + 1` texels and drops the
  duplicate, so `repeat` sampling has no doubled seam texel. Sizes are powers
  of two from 16 to 1024 (default 512).
- **Color spaces.** `basecolor` is sRGB and is sampled through an sRGB texture
  or view. Everything else is linear data.
- **Normals** are tangent-space with OpenGL +Y up. A flat normal is
  (128, 128, 255).
- **Integrity.** Every map and variant has a SHA-256.
  `tools/elemental.py pack --verify` and `Pack::verify()` refuse mismatches.
- **Provenance.** `source.calibrated` is `false` until a measured or
  reviewed source replaces the draft.

## Commands

```bash
python3 tools/elemental.py pack                         # all recipes, 512 px
python3 tools/elemental.py pack --material geo.slate.layered.v1 --size 1024
python3 tools/elemental.py pack --verify
```

## Not done yet

- KTX2/Basis GPU compression and mip chains. Packs are uncompressed PNG plus
  AVIF today.
- Tiled pyramids for very large hero surfaces (the Quackles RFC-003 virtual
  texture path).
