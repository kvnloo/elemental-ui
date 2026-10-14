# Taxonomy format

`catalog/taxonomy.json` (status `draft-pending-owner-validation`) is the plan.
`materials/**.json` recipes are what exists. Each recipe must appear in the
catalog; `tests/test_catalog.py` enforces that.

## Document

```json
{
  "version": 1,
  "status": "draft-pending-owner-validation",
  "hierarchy": "family > class > material > finish variant > seed",
  "kinds": ["tileable-surface", "bounded-object", "animated-surface", "volumetric-effect"],
  "render_roles": ["hero_macro", "material_ball", "ui_component", "variation_sweep", "scan_match"],
  "materials": [ … ]
}
```

## Material entry

| Field | Example | Meaning |
|---|---|---|
| `id` | `geo.basalt.vesicular.v1` | Stable, versioned id. Pattern: `(geo\|bot\|aq\|fauna\|atm).<name>.<variant>.v<N>` |
| `display_name` | `Basalt` | Label from the atlas or roadmap |
| `family` | `geological` | One of five families |
| `class` | `igneous` | Grouping within the family |
| `kind` | `tileable-surface` | Output class; decides what gets delivered |
| `atlas_code` | `GEO-01` | Index in the reference atlas, or `null` for roadmap-only entries |
| `origin` | `atlas-2026-10-12` / `roadmap` | Where the entry came from |

## Families and id prefixes

| Family | Prefix | Classes |
|---|---|---|
| geological | `geo` | igneous, sedimentary, metamorphic, crystalline, loose-earth |
| botanical | `bot` | foliage, bark, bryophytes-lichens, wood-fibers, reproductive |
| aquatic | `aq` | water-surfaces, shore-wet, underwater |
| atmospheric | `atm` | frozen, veils, low-light |
| fauna | `fauna` | scales, fibers-plumage, iridescence, marine, pattern-fields |

## Render roles

The prompt catalog in `references/dream-loop/` defines one prompt template per
role:

- `hero_macro`: one full-frame, top-down, text-free texture. This is the
  **only** role that feeds texture maps.
- `material_ball`, `ui_component`: look-development references.
- `variation_sweep`: one morphological parameter changed per panel.
- `scan_match`: comparison against a licensed scan.

## Adding a material

1. Add the entry to `catalog/taxonomy.json` with a new id and the correct
   `kind`.
2. When it gets a recipe, add `materials/<family>/<name>.json` that validates
   against `schemas/material.schema.json`.
3. Run `python3 -m unittest tests.test_catalog` and
   `python3 tools/elemental.py validate`.
