# Image generation

Visual targets for each catalog entry come from OpenAI image generation. They
are **references for look and morphology**, not texture maps; the maps are
derived from one source in Blender.

## Routes measured on 2026-10-13

| Route | Model | Resolution actually returned | Cost |
|---|---|---|---|
| ChatGPT Pro subscription via the Codex login (`comfyui-codex-image` node) | `gpt-image-2` | about 1.6 MP: 1254², 1536×1024 or 1448×1086. The requested size, quality and model are **ignored** | Part of the plan; 8 test images did not move the weekly window or the credit balance |
| OpenAI Images / Responses API | `gpt-image-2`, `gpt-image-2.5-sunburst`, `gpt-image-2.5-flare` | up to 3840 px on a side and 8,294,400 px total, edges in multiples of 16, aspect 1:3 to 3:1; above 2560×1440 is experimental. Square maximum: 2880² | metered |
| ComfyUI `OpenAIGPTImageNodeV2` | up to `gpt-image-2` | same as the API | Comfy.org credits |

Raw probes and findings:
`/mnt/zer0models/project-artifacts/elemental-ui/smoke-2026-10-13/` (local).

## Prompting rules

- Only `hero_macro` feeds the texture maps: one raw, full-frame, top-down
  surface with neutral diffuse light, sharp everywhere, and no text, borders,
  panels or props.
- Never ask the model for "four-panel PBR maps". Those images are
  illustrations, and the repository's own catalog says so.
- Keep the AI provenance and the @jimiplouffe credit. The atlas images are
  visual targets, not training or redistribution sources.

## Resolution strategy

The subscription's roughly 1.6 MP is enough for repeating textures. A 240 mm
tile at 1254 px is about 0.19 mm per pixel, which is finer than any phone or
wallpaper shows once the texture repeats. Hero materials that need close
inspection can use the API at 2880² or the overlapping tiled low-denoise
restoration pass in ComfyUI. Neither creates real 4K source detail, and they
must not be labelled as if they did.
