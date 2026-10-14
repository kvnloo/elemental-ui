# Runtime overview

One pack format and one lighting shader, painted by thin drivers. The drivers
only move pixels. Lighting lives in a single file, and the drivers are
checked against each other.

| Target | Driver | Tiers | Status |
|---|---|---|---|
| Web and phones | [`<elemental-surface>`](/runtime/web) | WebGPU → WebGL2 → CSS | working; WebGPU canvas still to be confirmed in a real browser |
| Native, headless | [`elemental-render`](/runtime/native) | wgpu (Vulkan, Metal, DX12) | working |
| Hyprland desktop | [`elemental-wallpaper`](/runtime/hyprland) | static lit render per monitor | working; a live layer-shell surface is planned |
| Tern | [plugin](/runtime/tern) | CSS (Tern's engine) | stylesheet verified; plugin load to be confirmed in a real window |

## Why not GPUI, egui or Vello?

The hard part here is **textured, relit materials**, not vector UI. A raw
wgpu or WebGPU pass with one WGSL file runs everywhere, including inside the
browser. The [runtime research](/RUNTIME_RESEARCH) covers what Tern, Zed and
Linebender use. In short, Tern itself is built on its own crates over wgpu,
not on a GUI framework.

## Measured

The [architecture & verification](/RUNTIME) page has the full table. In
brief: WebGL2 on the GPU is byte-identical to native; WebGPU (software
readback) is within 1/255; native renders take 8–29 ms; the web bundle is
about 18 KB.
