# Native: Rust crates

A Cargo workspace at the repository root (edition 2024, `GPL-3.0-only`).

## `elemental-pack`

Reads and verifies `elemental-pack/1`.

```rust
use elemental_pack::Pack;

let pack = Pack::open("packs/geo.basalt.vesicular.v1")?;   // schema + required maps
pack.verify()?;                                           // SHA-256 of every map and variant
let base = pack.load_rgba8("basecolor")?;                 // RGB/gray PNG expanded to RGBA8
println!("{} {}x{}", pack.manifest.display_name, base.width, base.height);
```

## `elemental-render`

wgpu 30 renderer for the [shared shader](/runtime/shader).

```rust
use elemental_render::{Gpu, SurfaceParams, SurfaceRenderer, render_offscreen, encode_png};

let gpu = Gpu::headless()?;                                       // high-performance adapter
let rgba = render_offscreen(&gpu, &pack, &SurfaceParams::reference(1920, 1080), 1920, 1080)?;
std::fs::write("out.png", encode_png(&rgba, 1920, 1080))?;

// Or draw into your own target (a swapchain, a layer-shell surface …):
let renderer = SurfaceRenderer::new(&gpu.device, &gpu.queue, &pack, wgpu::TextureFormat::Bgra8Unorm)?;
renderer.draw(&gpu.queue, &mut encoder, &view, &params);
```

`SurfaceRenderer` works with any target format because the shader encodes
sRGB itself. Use a **non-sRGB** target.

## CLI

```bash
cargo build --release
./target/release/elemental-render PACK_DIR OUT.png [WIDTH HEIGHT]   # default 1024×640
# geo.basalt.vesicular.v1 -> basalt.png (1920x1080) on NVIDIA GeForce RTX 3080 Ti [Vulkan] in 12.7 ms
```

The pack is verified before rendering. `WGPU_BACKEND` and the other wgpu
environment variables are honoured.

## Tests

`cargo test --release` checks the pack hashes, that `SurfaceParams` is 64
bytes, that naga parses and validates the WGSL, and that an offscreen basalt
render has plausible mean and variance. The render test skips with a message
when no adapter exists, as on CI.
