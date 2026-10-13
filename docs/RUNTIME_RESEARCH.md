# Runtime research notes (2026-10-13)

Why the runtime looks the way it does. Sources are linked; anything not seen
first-hand is marked as reported.

## Tern (Stencil) as the reference design

Tern 0.8.3 is closed source. What follows comes from the installed binary, the
public SDK and docs, and its founder's posts.

- **Built on:** Rust, plus Stencil's own `stencil_*` crates. `stencil_gfx` is a
  layer and backdrop compositor that prepares content on worker threads.
- **Rendering:** wgpu (v30 per stencil.so/tern), Vulkan on Linux, WGSL shaders.
- **Not built on:** GPUI, egui, iced, Slint or Vello. None of them appear in the
  binary.
- **Libraries in the binary:** resvg/usvg (SVG), rav1d (AVIF), fontconfig,
  Servo's CSS selector matching, mlua with Luau (plugins), WPE WebKit (browser
  panes only), gix (git) and merman (Mermaid diagrams in Rust).
- **Other targets:** the same code compiles to WebAssembly for a WebGPU
  browser client, and there is an iOS app.
- **Styling:** a real CSS engine with Stencil extensions. `url()` images are
  resolved against the plugin directory. `backdrop-filter`, `mix-blend-mode`
  and a `ripple()` filter are supported; `image-set()` and `conic-gradient()`
  are not.
- **Tern Surface Protocol:** programs send UI trees and later only prop deltas,
  and Tern lays out and draws them. The founder (@_can1357, 2026-09-28) says
  this avoids "viewport diff'ing, text measurement, tree/box drawing, handling
  styles cell by cell".
- **Effects as shaders:** he argues for fragment shaders for glass and blur
  (2026-10-03: "20 lines of code" against "a chain of 17 SVG filter steps") and
  notes that on the web a WebGL canvas cannot sample what is behind it.
- **xutf:** the founder's SIMD UTF-8/16/32 transcoding crate
  (github.com/can1357/xutf). Reported to be used by Tern; it is not visible in
  the binary.

### Related repositories

- **stencil-hq/slab**, "a design language for agents" (pre-alpha):
  - one Rust kernel for layout, animation and input;
  - drivers for wgpu, the web, the terminal and SVG/PNG;
  - pixel-identical comparisons against byte-identical reference images.
- **can1357/fxe**: the C++ predecessor of the idea. Dawn/WebGPU, V8 running
  TypeScript, Yoga layout, FreeType/HarfBuzz text. A clone is in
  `~/zer0/oss/fxe`.

## Rust GUI field (mid/late 2026, reported)

- **Shared plumbing is converging:** winit, wgpu, HarfRust, Parley, AccessKit.
  Zed moved GPUI's Linux renderer to wgpu (Feb 2026). Source:
  goldstrikearch.github.io/rust-gui-desktop-ecosystem-state.
- **GPUI:** the crates.io release is stuck at 0.2.2, so people use mirrors;
  gpui-component supplies the widgets.
- **Vello:** the original GPU renderer is still alpha. Vello Hybrid (sparse
  strips) is "roughly beta" and runs on WebGL2-class GPUs.
- **Blitz/Dioxus Native:** pre-alpha.
- **Choice for this project:** none of these are needed. The hard part here is
  textured lit materials, not vector UI, so the runtime is raw wgpu/WebGPU plus
  CSS.

## Web platform

- **WebGPU:** ships in Chrome/Edge, Safari 26 (including iOS) and Firefox on
  Windows and Apple Silicon Macs. Firefox on Linux and Android still does not
  have it, so the WebGL2 fallback is required.
- **Three.js:** recommends WebGPURenderer with TSL. Use it for later 3D/GLB
  pieces. The 2D surface element stays on raw WebGPU/WebGL2 so it can run the
  shared WGSL and keep the bundle around 18 KB.

## Image generation (for the pack pipeline)

- **ChatGPT subscription (Codex OAuth):** `gpt-image-2`. It ignores the
  requested size and quality and returns about 1.6 MP (1254² or 1536×1024).
  Measured: `/mnt/zer0models/project-artifacts/elemental-ui/smoke-2026-10-13/FINDINGS.txt`.
- **API:** `gpt-image-2.5-sunburst` and `gpt-image-2.5-flare` add `xhigh` and
  `max` quality settings. Edges must be multiples of 16 and at most 3840 px,
  with 655,360 to 8,294,400 pixels in total; sizes above 2560×1440 are
  experimental.
