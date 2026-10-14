# Surface shader

`shaders/elemental_surface.wgsl` is the only lighting code in the project.

| Consumer | How it gets the shader |
|---|---|
| `crates/elemental-render` | `include_str!` of the file; compiled by wgpu |
| WebGPU tier | the file is bundled as text by esbuild and compiled by the browser |
| WebGL2 tier | `naga --profile es300 --keep-coordinate-space` → `packages/web/src/generated/surface-glsl.ts` |

## Bindings

| Group/binding | Resource |
|---|---|
| 0/0 | `Params` uniform (64 bytes) |
| 0/1 | sampler (repeat, linear) |
| 0/2 | `basecolor_map` (sRGB texture or sRGB view) |
| 0/3 | `normal_map` (linear, OpenGL +Y) |
| 0/4 | `roughness_map` (linear) |

## `Params`

```wgsl
struct Params {
    resolution: vec2<f32>,  // target size, physical pixels
    tile_px: f32,           // on-screen size of one tile, physical pixels
    relief: f32,            // multiplier on the tangent normal's xy
    light: vec4<f32>,       // xyz toward the light (x right, y up, z to viewer); w intensity
    light_color: vec4<f32>, // rgb; a = ambient fraction of base color
    view: vec4<f32>,        // xy offset in tiles; z exposure; w unused
};
```

The reference values used by the CLI, the demo and the parity tests are the
same in Rust (`SurfaceParams::reference`) and TypeScript (`REFERENCE`):
tile 256 px, relief 1, light (−0.45, 0.55, 0.70) × 3.2, color
(1, 0.97, 0.92), ambient 0.22, exposure 1.

## Shading model

- A full-screen triangle; `uv` (0, 0) is the top-left pixel.
- Lambert diffuse with `(1 − F)`, a GGX distribution, Smith-Schlick
  visibility and Schlick Fresnel with F0 = 0.04 (a dielectric).
- The view direction is fixed at +Z (an orthographic surface viewed head-on).
- Reinhard tone mapping, then **manual** sRGB encoding into a non-sRGB
  target. Every backend writes the same bytes because no backend applies its
  own output encoding.

## Changing the shader

```bash
$EDITOR shaders/elemental_surface.wgsl
npm run glsl -w @elemental-ui/web        # regenerate the WebGL2 GLSL (needs naga-cli 30.0.1)
cargo test --release                     # naga validation + GPU render
ELEMENTAL_BROWSER_VULKAN=1 python3 -m unittest tests.browser.test_runtime   # parity
```

CI fails if the committed GLSL no longer matches the WGSL
(`npm run glsl:check`).
