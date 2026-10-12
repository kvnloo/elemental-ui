# Shared PBR maps → Blender Cycles smoke pipeline

This is a **narrow fidelity bridge**: the existing Python generator produces the same source maps used by the web, while Blender Cycles renders those actual maps instead of a different Blender-only procedural shader. It does not yet bake a physically calibrated Blender shader, or prove parity to real photography. Tracking: [#2](https://github.com/kvnloo/elemental-ui/issues/2).

## From a fresh checkout

Run \`python3 tools/elemental.py generate --size 128 --out web/assets\`, then either use Blender 4.5+ CLI or the official Blender Python wheel for Python 3.11:

\`\`\`bash
python3.11 -m pip install bpy==4.5.14
python3.11 blender/render_pbr_pack.py --material geo.basalt.vesicular.v1 \
  --map-root web/assets --out outputs/blender --samples 8 --size 512
\`\`\`

With Blender installed: \`blender -b --python blender/render_pbr_pack.py -- --material geo.basalt.vesicular.v1 --samples 8 --size 512\`.

Outputs: \`outputs/blender/geo.basalt.vesicular.v1/pbr-preview.png\`, \`pbr-preview.blend\`, \`pbr-render-receipt.json\` (Blender version, CPU samples, map hashes, PNG hash). Source code and manifest remain small; source/outputs are not committed.

## Correctness model

- **Base color:** sRGB (lighting-free), not a photograph with baked highlights.
- **Roughness, normal:** Non-Color image nodes. OpenGL +Y tangent normal. Normal is not also used as a height bump.
- **Height:** 16-bit grayscale, **verified but not applied** while a tangent normal is active (avoids double depth).
- **Scale:** UI slab is 210 x 85mm and UV scale is derived from the manifest's physical tile width; this geometry mapping is still an artistic approximation.
- **Integrity:** refuse file traversal, manifest or SHA mismatches, invalid image formats, stale recipe seeds, and wrong nominal scale.
- **Preview:** CPU Cycles, controlled studio rig and explicit render seed. A render passing this workflow does **not** establish geological, BRDF or photogrammetric accuracy.

## CI

Separate \`Blender PBR smoke\` workflow runs on changes to Blender/material pipeline and by manual dispatch. It installs the **Blender Foundation** Python 3.11 \`bpy==4.5.14\` wheel and renders basalt at 256px; **no GPU hardware claim**. Build receipts and the PNG are attached on success. Lower the frequency if upstream binary dependency downloads become disproportionate.

## Next quality gate

1. UV distortion and normal orientation inspection under grazing, neutral and warm light.
2. True Blender Cycles shader baking with calibrated source and target mesh.
3. Actual basalt/slate/limestone photographic reference boards, artist/source attribution.
4. Screen-space visual quality/bytes comparison against the cheap CSS version.
