# Architecture

```
material recipe (schema / units / author / seed / references)
           |
           +--> deterministic Python draft maps -> basecolor, roughness, normal, height, preview
           |                                       -> manifest with hashes and seam QA
           |
           +--> Blender procedural Cycles preview -> .blend + physically inspired render
           |
           +--> web gallery / CSS components -> lightweight semantic HTML
                                      |
                                optional GLB / WebGL later
```

The Python draft generator and Blender shader have separate implementations in v0.1. Both read the same recipe, but visual parity and Blender baking are **unimplemented**. Do not substitute the procedural preview maps for physically measured values.

## Material model

- IDs: `geo.basalt.vesicular.v1` and equivalents, stable and versioned.
- Render classes: tileable surface, bounded object, animated surface, volumetric effect.
- Web texture color space: albedo is sRGB; roughness/height/normal are **non-color**.
- Normals are OpenGL-style tangent-space (+Y / green-up), with neutral (128, 128, 255).
- Height is a 16-bit unsigned PNG and requires recorded displacement scaling.
- Pixel edge continuity is explicit: opposing edge texels match, not merely a visual-looking seam.
- Blender geometry is authored in meters; the stone button is physically sized in the scene.
- 2D controls use CSS inset, raised and selected states; focus remains independent of textures.

## Quality gates

1. Reproducibility: same recipe + seed yields identical bytes and checksums.
2. Seam: first/last pixel rows and columns match for each generated map.
3. Physical plausibility: references, scale and multiple lighting rigs (manual review; pending).
4. Real UI: keyboard/screen-reader, reduced motion, mobile layout.
5. Performance: record asset bytes, render CPU/GPU costs and browser interactions per environment. Do not claim budget compliance without receipts.

## Decisions

Avoid reusing the user-supplied reference images as assets without permission. Prefer data-first recipes and cheap output formats over embedding WebGL into every button. CI verifies generator correctness; Blender artwork quality requires a configured Blender runner and visual review.
