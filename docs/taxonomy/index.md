---
aside: false
outline: false
---

# Material taxonomy

Everything elemental-ui plans to mass-generate, as **family › class ›
material**. The source of truth is
[`catalog/taxonomy.json`](https://github.com/kvnloo/elemental-ui/blob/main/catalog/taxonomy.json).
It holds 353 distinct materials:
- **48 atlas materials:** everything on the four reference atlas posters (codes like `GEO-01`).
- **8 roadmap materials:** from the roadmap's priority matrix.
- **297 expansion materials:** added to make this a list worth mass-generating, covering real rock
  types, minerals, timbers, bark, fungi, shells, plumage, sky and fire.

Finish variants (rough, cut, polished, wet, weathered) and seeds multiply each
material further when generated.

Images are **visual targets**: one hero macro per material, generated with
gpt-image-2 to set the look ([how](/pipeline/image-generation)). They are
references, not calibrated PBR maps. The texture maps are derived from a
single source in Blender. Hover the *visual target* tag to see the prompt.
Materials tagged *live pack* already have a runtime pack; see them relit on
the [web component](/runtime/web) page.

<TaxonomyExplorer />

## Notes on the hierarchy

- Rocks are grouped by **geology**, not by atlas row. Slate is metamorphic,
  while granite and volcanic tuff are igneous.
- Finish variants (`rough`, `cut`, `polished`, `wet`, `weathered`) and seeds
  sit below the material level and are not listed yet. See
  [Taxonomy format](/taxonomy/format).
- Kinds decide what gets delivered. Mist is a `volumetric-effect`, so it will
  never be a seamless tile.
