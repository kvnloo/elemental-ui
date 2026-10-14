# Material recipes

A recipe is the source of truth for one material that exists. It lives at
`materials/<family>/<name>.json` and is validated against
`schemas/material.schema.json` by `tools/elemental.py validate`.

```json
{
  "id": "geo.basalt.vesicular.v1",
  "display_name": "Vesicular Basalt",
  "family": "geological",
  "kind": "tileable-surface",
  "version": 1,
  "author": "elemental-ui contributors",
  "license": "GPL-3.0-only",
  "seed": 84017,
  "physical_tile_mm": 240,
  "parameters": { "base_color_rgb": [40, 37, 36], "roughness": 0.88, "height_mm": 1.8, "grain": 2.7, "weathering": 0.35 },
  "references": [],
  "status": "prototype"
}
```

| Field | Rule |
|---|---|
| `id` | `^(geo\|bot\|aq\|fauna\|atm)\.[a-z0-9-]+(\.[a-z0-9-]+)+\.v[1-9][0-9]*$` |
| `family` | geological, botanical, aquatic, fauna, atmospheric |
| `kind` | tileable-surface, bounded-object, animated-surface, volumetric-effect |
| `seed` | integer; the same seed gives the same bytes |
| `physical_tile_mm` | real-world width of one tile |
| `parameters` | `base_color_rgb` (0–255 ×3), `roughness` 0–1, `height_mm` ≥ 0, `grain` > 0, `weathering` 0–1 |
| `references[]` | `creator`, `url`, `license`, `retrieved_at`, optional `sha256` ([provenance policy](/PROVENANCE)) |
| `status` | `prototype` → `render-pass` → `visual-review` → `web-pass` → `published` |

## Current recipes

| id | tile | relief | status |
|---|---|---|---|
| `geo.basalt.vesicular.v1` | 240 mm | 1.8 mm | prototype |
| `geo.slate.layered.v1` | 240 mm | 1.2 mm | prototype |
| `geo.limestone.porous.v1` | 240 mm | 1.6 mm | prototype |

## The draft generator

`tools/elemental.py generate` is a dependency-free Python generator built on
periodic value noise and fBm. It writes `basecolor`, `roughness`, `normal`
(OpenGL +Y), 16-bit `height`, a 2×2 `preview` and a `manifest.json` with
hashes. Its opposing edge texels are identical, which the seam test checks.
This is a **first-pass procedural study**; it exists to test the pipeline,
not to define the look.
