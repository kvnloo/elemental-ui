# Testing & CI

## Suites

| Suite | Command | Proves | Does not prove |
|---|---|---|---|
| Recipes and generator | `python3 -m unittest tests.test_elemental` | schema rules, deterministic bytes, seam texels, manifests | visual quality |
| Catalog and packs | `python3 -m unittest tests.test_catalog` | unique, well-formed ids; 48 atlas codes; kinds; id prefix matches family; every recipe is in the catalog; one period per map; pack hashes | that the catalog is complete (owner sign-off) |
| Blender assets | `python3 -m unittest tests.test_pbr_assets` | the map-loading contract for Blender | Cycles rendering itself (Blender smoke workflow) |
| Poly Haven importer | `python3 -m unittest tests.test_polyhaven` | host, size and hash guards (offline fixtures) | live API behavior |
| Rust | `cargo test --release` | pack contract, `Params` layout, naga validation, GPU offscreen render | browser behavior |
| Gallery QA | `python3 -m unittest tests.browser.test_gallery` | v0.1 gallery: images, keyboard, 360/768/1440 px, reduced motion | WCAG audit, device performance |
| Runtime QA | `python3 -m unittest tests.browser.test_runtime` | WebGL2 and WebGPU (readback) vs native parity, the CSS tier, HTML above the material, pointer relighting, frame pacing | WebGPU **canvas** presentation in headless browsers; device benchmarks |

Runtime QA environment:

- `ELEMENTAL_BROWSER_BIN=/usr/bin/chromium` to use a system Chromium.
- `ELEMENTAL_BROWSER_VULKAN=1` runs WebGL2 on the real GPU through
  ANGLE/Vulkan. Parity is then byte-identical; on SwiftShader it is mean 2.9,
  max 6/255.
- Results go to `reports/generated/runtime/runtime-report.json` together
  with the compared PNGs.

## Measured parity (512×320 basalt, reference parameters)

| Pair | mean | p99 | max |
|---|---|---|---|
| WebGL2 (ANGLE/Vulkan, RTX 3080 Ti) vs native | 0.00 | 0 | 0 |
| WebGL2 (SwiftShader) vs native | 2.90 | 5 | 6 |
| WebGPU readback (SwiftShader) vs native | 0.03 | 1 | 1 |
| *Bug found by this test:* WebGPU with a double sRGB decode | 11.3 | 19 | 27 |

## CI workflows

| Workflow / job | Trigger | Runs |
|---|---|---|
| `ci.yml` › tests | push to main, PRs | compile, validate recipes, unit tests, draft generation, gallery artifact |
| `ci.yml` › browser | push to main, PRs | gallery and runtime browser QA (packs and bundle built; native parity skips because `elemental-render` is built in another job) |
| `ci.yml` › runtime-packs | push to main, PRs | packs plus verify, `cargo test --locked`, naga-cli install, GLSL drift check, typecheck, web build |
| `blender-smoke.yml` | PRs touching `blender/**`, `materials/**` | Cycles render of basalt with the `bpy` wheel, exposure guard, receipts |
| `reference-smoke.yml` | PRs touching `references/**`, `tools/polyhaven.py` | Poly Haven importer integrity |
