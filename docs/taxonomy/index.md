---
aside: false
outline: false
---

# Material taxonomy

Everything elemental-ui plans to mass-generate, as **family › class ›
material**. The source of truth is
[`catalog/taxonomy.json`](https://github.com/kvnloo/elemental-ui/blob/main/catalog/taxonomy.json).
All 48 materials from the four reference atlases (codes like `GEO-01`) are
included. The 8 entries marked *roadmap* come from the roadmap's priority
matrix.

Materials that already have a runtime pack show a **live swatch**: move the
pointer over it to move the light. The others show their family color until
the generation pipeline produces them.

<TaxonomyExplorer />

## Notes on the hierarchy

- Rocks are grouped by **geology**, not by atlas row. Slate is metamorphic,
  while granite and volcanic tuff are igneous.
- Finish variants (`rough`, `cut`, `polished`, `wet`, `weathered`) and seeds
  sit below the material level and are not listed yet. See
  [Taxonomy format](/taxonomy/format).
- Kinds decide what gets delivered. Mist is a `volumetric-effect`, so it will
  never be a seamless tile.
