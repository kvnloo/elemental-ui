# Web: `<elemental-surface>`

`@elemental-ui/web` is a dependency-free custom element of about 18 KB
minified. It works in plain HTML, React, Vue or anything else that renders
DOM.

```html
<script type="module" src="/elemental-ui.js"></script>
<elemental-surface material="geo.basalt.vesicular.v1" packs="/packs" light="pointer" tile="256">
  <h2>Vesicular Basalt</h2>
  <button type="button">Explore</button>
</elemental-surface>
```

<script setup>
import { onMounted } from "vue";
import { withBase } from "vitepress";
onMounted(() => import(/* @vite-ignore */ withBase("/live/elemental-ui.js")).catch(() => {}));
</script>

## Live

These are the three **draft procedural packs** relit by the shared shader in
your browser. Move the pointer across them. The AI-derived packs will replace
them once the Blender stage exists.

<div class="live-demo">
  <elemental-surface v-for="m in ['geo.basalt.vesicular.v1', 'geo.slate.layered.v1', 'geo.limestone.porous.v1']" :key="m" :material.attr="m" :packs.attr="withBase('/live/packs')" light="pointer" tile="192" class="live-card">
    <span class="live-label">{{ m }}</span>
  </elemental-surface>
</div>

<style>
.live-demo { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin: 18px 0 8px; }
.live-card { min-height: 190px; border-radius: 18px; overflow: hidden; box-shadow: inset 1px 2px 0 rgb(255 255 255 / 0.16), 0 6px 14px rgb(37 28 17 / 0.2); }
.live-label { position: absolute; left: 12px; bottom: 10px; font: 0.7rem var(--vp-font-family-mono); color: #f3eee5; text-shadow: 0 1px 2px #000; }
</style>

## Attributes

| Attribute | Default | Meaning |
|---|---|---|
| `material` | (required) | pack id |
| `packs` | `/packs` | URL of the packs directory |
| `tier` | `auto` | `auto` (WebGPU, then WebGL2), `webgpu`, `webgl2` or `css` |
| `light` | static | `pointer` makes the light follow the pointer; ignored under reduced motion |
| `tile` | `256` | CSS pixels per tile |
| `relief` | `1` | normal strength |
| `exposure` | `1` | exposure multiplier |

`material`, `packs` and `tier` reload the surface. The others redraw it.

## Events and state

| | |
|---|---|
| `elemental-ready` | `detail: { tier, material, ms }`. Fires for the CSS tier first and again when a GPU tier takes over. |
| `elemental-error` | `detail: { material, error }` when the pack cannot load |
| `element.tier`, `data-tier` | the tier painting now |
| `element.params()` | current shader parameters in physical pixels |

## Tiers

1. **CSS:** the base color tiled with `image-set()` (AVIF with a PNG
   fallback). It paints immediately and stays underneath as the fallback.
   Chosen when `tier="css"`, when `saveData` is on, or when no GPU tier
   starts.
2. **WebGL2:** naga-generated GLSL ES 3.00 and an sRGB8_ALPHA8 base color.
3. **WebGPU:** the WGSL itself. The base color is uploaded as `rgba8unorm`
   and sampled through an `rgba8unorm-srgb` view. Copying straight into an
   sRGB texture made the browser re-encode it and darkened the result (mean
   error 11/255).

## Performance behavior

- Draws happen only on pointer moves, resizes, attribute changes, and when
  the element comes back on screen (`IntersectionObserver`).
- One `GPUDevice` and shader module are shared by all elements. Pack fetches
  are deduplicated.
- Device pixel ratio is capped at 2. The canvas sits under the slotted
  content (`z-index: -1` in an isolated stacking context), so text stays
  sharp DOM text.

## Other exports

```ts
import { loadPack, cssBackground, renderPixelsWebGPU, REFERENCE, packParams, lightToward } from "@elemental-ui/web";

const pack = await loadPack("/packs", "geo.slate.layered.v1");
const rgba = await renderPixelsWebGPU(pack, { ...REFERENCE, width: 512, height: 320 }); // bake a lit still
```

## Demo and fixtures

- `packages/web/demo/index.html`: all packs with a tier switcher. Serve the
  repository root and open `/packages/web/demo/`.
- `packages/web/demo/parity.html`: a fixed-size reference render used by the
  tests (`?mode=pixels` uses the off-canvas WebGPU readback).

::: info Headless browsers
In headless Chromium on Linux the WebGPU adapter is SwiftShader, and its
canvases never present. A screenshot then shows the CSS layer underneath.
The WebGPU path is verified by off-canvas readback; WebGPU **canvas** output
still has to be checked in a real browser window.
:::
