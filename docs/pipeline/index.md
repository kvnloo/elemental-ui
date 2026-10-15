# Asset pipeline

How a catalog entry becomes something a browser, a desktop or Tern can draw.
Each stage is a file contract, so any stage can be redone without touching the
others.

```text
catalog/taxonomy.json  ──►  prompt templates (references/dream-loop)
        │                         │  ChatGPT gpt-image-2 (subscription) / API for hero masters
        │                         ▼
        │                   hero_macro visual target (one full-frame texture)      [next]
        │                         │  make seamless → Blender: derive base color / normal / roughness / height
        ▼                         ▼
materials/<family>/*.json ─► tools/elemental.py pack ─► packs/<id>/  (elemental-pack/1)
  (recipe: seed, scale)        (today: procedural draft)        │
                                                                ├─► web  <elemental-surface>
                                                                ├─► native elemental-render / Hyprland
                                                                └─► Tern plugin
```

| Stage | Status | Page |
|---|---|---|
| Taxonomy of what to generate | **done**, 353 materials (48 atlas + 8 roadmap + 297 expansion), awaiting owner sign-off | [Taxonomy](/taxonomy/) |
| Recipes (seed, scale, parameters) | 3 geological recipes | [Recipes](/pipeline/recipes) |
| Visual targets from image generation | smoke-tested, about 1.6 MP per image on the subscription | [Image generation](/pipeline/image-generation) |
| Seamless + Blender map derivation | **next** | [Blender PBR smoke](/PBR_BLENDER) |
| Packs | **done** (draft maps today) | [Packs](/pipeline/packs) |
| Credited CC0 scan references | importer done; 4 candidates curated | [Reference scans](/REFERENCES) |

## Quality gates (from the roadmap)

1. **Reproducibility:** the same recipe and seed give identical bytes and
   checksums.
2. **Seams:** maps repeat without a visible edge. Packs store exactly one
   period.
3. **Physical plausibility:** references, scale and several lighting rigs
   (manual review, pending).
4. **Real UI:** keyboard, screen reader, reduced motion, mobile layout.
5. **Performance:** bytes, render cost and interaction timing recorded per
   environment.
