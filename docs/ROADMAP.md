# Natural Materials System — Production Roadmap

**Status:** Proposed implementation plan, 10 October 2026  
**Scope:** Reproducible natural materials (Blender) → physically credible renders and maps → optimized delivery for accessible interactive websites and WebGL.  
**Source brief:** User-pasted *Expanded Plan: Natural Photorealistic Materials Library for Websites*. The Grok conversation appeared twice in the paste; it is treated as one source.  
**Visual inspiration:** Supplied STONE interface study images show credits `@jimiplouffe`. Verify rights/permission before redistributing originals or close derivatives, and preserve human credit in the provenance record.

## 1. Product definition and non-goals

**Build a natural-material engine, not a folder of JPEGs.** Every published material must have a declared source, physical scale, deterministic generator, lighting-independent map set where applicable, quality results, and one or more web-ready outputs. Material families cover geological, botanical, aquatic, fauna, and atmospheric/ephemeral effects.

Consumers:
1. **Web designers:** downloadable tileable surfaces, hero stills, layered cutouts, short motion loops.
2. **Frontend engineers:** React/vanilla UI primitives with HTML content layered above decorative image assets.
3. **3D artists and developers:** organized `.blend` source, high/low meshes, PBR maps, optimized GLB.
4. **Researchers and community contributors:** material recipes, measured reference properties, capture conditions, provenance, licensing and repeatable QA.

Non-goals for v1: photoreal-time 3D for every button; bespoke shaders forced into glTF when baking is better; automated copying of copyrighted designs; stockpiling hundreds of unvalidated assets; full physics simulators; a general texture editor.

**A useful product distinction:** Materials are not all 2D tiles. Model four output classes — (A) tileable *surface*, (B) bounded *object* (leaf, pebble, crystalline cluster), (C) animated *surface*, and (D) *volumetric/ephemeral effect*. Define deliverables by class instead of promising seamless texture maps for fog or jellyfish.

## 2. Overall architecture

```text
Licensed real-world references / scans / measurements
                     ↓
Material recipe & manifest (JSON/YAML, versioned; units, seed, provenance)
                     ↓
Blender material + geometry generators (bpy, Geometry Nodes, shader node groups)
                     ↓
Controlled calibration/lighting → reference turntable + swatch + hero render
                     ↓
UV unwrap and bake (base color, roughness, normal, height, AO as needed)
                     ↓
Deterministic checks → visual review vs reference → license gate
                     ↓
Delivery build:
  2D tiles (AVIF/WebP + PNG/EXR masters)
  UI skins (text-free slices, CSS depth states)
  Optional GLB (optimized geometry + KTX2 maps)
  Optional motion loops / shaders
                     ↓
Web gallery, npm/CSS asset adapter, docs, sandbox, benchmark suite
```

**Golden rule:** Author in high quality once; publish tiered deliverables. The browser gets the *cheapest asset that creates the desired perception*.

### Suggested open-source stack

- **Source:** Blender + Python `bpy` scripts, Geometry Nodes, Cycles path tracing; evaluate Blender 5.x on project hardware and pin the tested version per release. Keep EEVEE previews optional, not a substitute for validation under Cycles.
- **Optional reference:** CC0 textures, scans and HDRIs from Poly Haven and ambientCG, but pin exact asset, photographer/creator, license and acquisition URL. A referenced CC0 scan is a reference/input, not proof that a newly assembled collection can be relicensed without reviewing every dependency.
- **Web:** TypeScript, Vite (or existing site framework), CSS, semantic HTML, Storybook for states; Three.js for selectively loaded GLB and shader demos.
- **Optimization:** sharp/squoosh-type image encoding where useful, `gltf-transform`, Meshoptimizer, KTX2/Basis Universal; `glTF-Validator` for interoperability.
- **QA:** Blender headless render and bake tests, image analysis with Python/OpenCV or Pillow, Playwright screenshot and keyboard tests, axe accessibility checks, Lighthouse and Web Vitals.
- **Storage:** scripts/manifests/thumbnails in Git; larger generated binaries in releases, content-addressed object storage or LFS based on practical limits. Do not commit large 4K/8K derivatives repeatedly.

## 3. Canonical material contract

Material ID: `geo.basalt.vesicular.v1`; additional examples `bot.leaf.oak.translucent.v1`, `aq.water.coastal-ripple.v1`, `fauna.beetle.elytra-iridescent.v1`, `atm.frost.window.v1`.

Every recipe declares:
- `id`, `display_name`, `family`, `kind`, `version`, `author`, `contributors`, `license`, `references[]`, `source_sha256[]`.
- `generator` identifier and version, tested Blender version, seed and generator parameters, physically meaningful scale in m or mm, calibration swatch.
- PBR parameters and baking conventions, render profiles, maps produced, supported scene types, tile policy, emissive/transmissive/SSS flags, motion policy and fallbacks.
- Quality receipts, target runtime tier, outputs with paths/hashes/sizes, and review status `draft | render_pass | visual_review | web_pass | published`.

Example manifest (illustrative, not a validated material):

```json
{
  "id": "geo.basalt.vesicular.v1",
  "family": "geological",
  "kind": "tileable-surface",
  "seed": 84017,
  "scale_mm_per_tile": 240,
  "generator": "nodes/basalt_vesicular@1.0.0",
  "license": "CC0-1.0",
  "references": ["source-reference-url-and-credit"],
  "maps": ["basecolor", "roughness", "normal", "height", "ao"],
  "web": ["css", "pbr", "glb"],
  "qa": {"seam": "pending", "lighting": "pending", "browser": "pending"}
}
```

**Color/data rules:** base color is lighting-free color texture (sRGB at delivery); roughness, metallic, height and normals are non-color/linear data; specify normal coordinate convention, including green channel direction; record displacement scale. Avoid double-applying AO in physically shaded displays. Export master height in sufficient precision to avoid banding (e.g. 16-bit), then derive cheaper web versions. A roughness map is not simply a grayscale version of the color photograph.

**Scale:** Build physically meaningful pore sizes, grains, feather lengths, leaf thicknesses, etc. at the modeled object scale. Add coarse, medium and micro frequency layers; test under grazing, overhead, neutral and warm light. Maintain a separate `reference scale` ruler for every family.

## 4. Repository layout

```text
natural-materials/
├── README.md                       # mission, quickstart, provenance
├── LICENSES/                       # code + independently licensed assets
├── docs/
│   ├── architecture.md
│   ├── material-spec.md
│   ├── shader-guidelines.md
│   ├── contribution-guide.md
│   ├── quality-gates.md
│   └── usage-recipes/
├── references/                     # metadata and permitted low-res references
├── schemas/material.schema.json
├── materials/
│   ├── geological/<material-id>/recipe.json
│   ├── botanical/<material-id>/recipe.json
│   ├── aquatic/<material-id>/recipe.json
│   ├── fauna/<material-id>/recipe.json
│   └── atmospheric/<material-id>/recipe.json
├── blender/
│   ├── templates/                  # swatch, material ball, slab, button, hero
│   ├── node_groups/                # reusable generator source/templates
│   ├── geometry/                   # modifiers & repeatable forms
│   ├── rigs/                       # calibrated HDRI/studio/grazing setups
│   └── scripts/                    # build, render, bake, validate/export
├── tools/                           # manifest validation, CLI, converters, QA
├── web/
│   ├── gallery/                     # filtering, compare, try-material
│   ├── components/                  # CSS skins and interactive primitives
│   └── examples/                    # HTML, React, Three.js, shader demos
├── tests/
│   ├── procedural/
│   ├── image-quality/
│   ├── browser/
│   └── perf/
├── outputs/                         # local/generated, ignored in Git
└── reports/                         # compact metrics, thumbnails, QA receipts
```

All commands must be rerunnable and resumable: `doctor`, `generate`, `render`, `bake`, `optimize`, `validate`, `publish-preview`. Support `--material`, `--seed`, `--profile draft|reference|web`, and `--resume`. Store compiler/version/GPU settings with outputs.

## 5. Material priority matrix

Choose by **visual reuse × physical distinctiveness × pipeline learning × ease of QA**, not just visual novelty. Separate `must ship`, `second wave`, and `experimental`.

| Family | MVP exemplars | Later explorations | Special engineering |
|---|---|---|---|
| Geological | vesicular basalt, slate, limestone | travertine, sandstone, granite, marble, obsidian, quartz, sand, soil | credible pores, strata, occlusion, chips, UVs, physical scale |
| Botanical | leaf with front/back, bark, moss | grass clusters, fern, petals, wood endgrain, lichen, seed pod | directional veins, thin-sheet transmission/SSS, leaf geometry, scattering |
| Aquatic | calm water, small ripples, wet stone | foam, caustics, tidal bioluminescence, underwater haze | IOR, transmission, depth, animated normals; foam/caustics often as separate layers |
| Fauna | fish scales, beetle iridescence, feather | reptile scales, butterfly wing, fur, organic camouflage | scale packing, anisotropy/iridescence, view-dependent response |
| Atmospheric | frost, snow, volumetric fog | leaf-filtered light, glowing fungi, firefly field, ice | volumes and animation are not seamless 2D surfaces |

**High-level limit:** A scan/photo can define correct morphology and color behavior, but physically accurate specular response requires multiple lighting observations or calibrated assumptions. Clearly label artistic approximations rather than claiming measured optical properties.

## 6. Phase plan — gated, vertical-slice first

### Phase 0. Foundation and reference audit
**Objective:** One reproducible system that can generate and inspect any material.

Tasks:
1. Pin Blender, Python, package versions and supported render settings. Device capability check, default GPU profile and CPU fallback.
2. Create source, asset, license and contributor policies. Record human credit and asset lineage (reference/scans/derivatives).
3. Build reusable **studio sphere**, **flat tile**, **carved slab**, **button**, **card**, **hero** and **turntable** scenes.
4. Calibrate HDRI exposure, white balance, camera, object scale and transform conventions; define consistent neutral/grazing/warm side lighting.
5. Define recipe schema and CLI; set up `doctor` with dependency tests.
6. Render a neutral control surface, bake a dummy texture, and verify export and browser preview end-to-end.

**Exit:** Fresh clone + one documented command reproduces a baseline thumbnail, a map, a simple mesh and a browser preview with logged hashes/settings. License manifest present. Smoke tests pass on GPU and CPU fallback.

### Phase 1. Geological **vertical slice** (first useful product)
**Objective:** Prove three physically distinct materials as usable website assets.

Materials: `basalt.vesicular`, `slate.layered`, `limestone.porous` — chosen to reproduce the core tactile contrast of the supplied references.

For each:
1. Curate multiple real references with measurable grain/pore/strata cues and usage rights.
2. Procedural shader with seed, real-world scale, roughness, pore depth, weathering and macro-to-micro controls.
3. High-poly slab/rounded-button geometry with asymmetric chips, worn edge profiles and controllable bevel sizes. Geometry separate from surface material.
4. Produce material sphere, UV tile, neutral light response, grazing-light pass, button/card state renders and side-by-side photographic reference board.
5. Bake lighting-free color, roughness, tangent normal, height; AO only if needed. Verify UV seams.
6. Create browser primitives: actual `<button>`, segmented control and card. Keep labels/icons/accessibility states in HTML/CSS, not embedded in imagery.
7. Compare delivery paths: a) WebP/AVIF assets and CSS light/shadow, b) 2.5D depth/motion, c) GLB/WebGL on demand. Measure bytes, visual difference and interaction delay.

**Exit:** Three approved materials, three usable web components, interactive gallery, reproducible CI receipts and one real mobile benchmark. A material survives changes in lighting without looking like a baked photograph.

### Phase 2. Geological core expansion
**Objective:** Expand to 10–12 distinct geological assets while solidifying shared nodes.

Order: travertine → sandstone → granite → marble → obsidian → quartz → natural sand/soil, with variations based on validation. Avoid a separate hand-authored graph per stone. Reuse noise/microfracture/edge-weathering modules; one distinct morphology module per geology.

- Build a **hardness / polish / porosity / erosion** parameter model with visual reference checks, not an arbitrary material randomizer.
- Add physically credible `rough`, `cut`, `polished`, `wet`, `weathered` variations only where geologically sensible.
- Profile output generation costs and bake times. Cache unmodified subgraphs and immutable output files.

**Exit:** At least ten documented geology materials, two distinct seeds each, screenshot comparison under 3 standardized lighting rigs, stable schema and export size reports.

### Phase 3. Botanical foundations
**Objective:** Support thin-layer subsurface appearance and organic object geometry, not just flat textures.

- `oak/maple-like broadleaf`: front vs back material, primary/secondary veins, opacity/translucency and thickness mask, believable serration/edge damage; model species as verified variants rather than names on generic leaves.
- `bark`: radial scaling, creases and fiber direction applied to curved mesh, wet/dry variants.
- `moss/lichen`: macro tufts and Geometry Nodes scatter plus lower-cost normal-map equivalent. LOD at distance.
- `wood`: longitudinal grain and endgrain; branch/ring continuity, avoid generic noise.
- Scattered grass/foliage: density masks, seeded variation, wind animation optional.

**Exit:** Four approved assets spanning tileable surface and bounded geometry, including an accurately lit backlit leaf; static CSS and GLB demos with mobile fallback.

### Phase 4. Aquatic, bioluminescent and atmospheric systems
**Objective:** Build specialized physically inspired motion and volume authoring pathways.

- Water: 1) still/refractive, 2) gently rippled animated normals, 3) foam mask separate from water, 4) caustic projection / baked loop. Physics-informed parameters (IOR near 1.333 for liquid water at visible wavelengths/room conditions as an approximate anchor), frequency and directional wind as parameters.
- Wet interfaces: contact-angle inspired edge darkening and wet roughness variation, distinct from simply increasing saturation.
- Bioluminescence: localized emission masks, attenuation, nonuniform temporal modulation, subtle response to simulated motion; keep emissive source separate from bloom postprocessing.
- Ice and frost: surface crystals, roughness scattering, frozen-edge gradients; snow has distinct subsurface behavior.
- Fog and shafts: volumes in Blender source but publish rendered background, transparent motion loop or runtime effect, never pretend volume can be encoded in one tile.

**Exit:** One interactive water component, one foam/caustic layered scene, one glow/emission study, one frost/fog study; each has a still fallback and a reduced-motion behavior.

### Phase 5. Fauna patterns and optical effects
**Objective:** Prove view-dependent effects and anisotropic structure.

- Fish and reptile scales: geometric scale layout where silhouette matters, with normal-map fallback.
- Beetle/butterfly iridescence: angle-dependent color shift via a supported glTF extension or a web shader; create a static baked fallback.
- Feather/fur: flow direction and anisotropic response, LOD representation, clear separation between fiber geometry and surface pattern.
- Avoid indiscriminate use of metalness for biological reflectivity; compare controlled turntable against real reference.

**Exit:** Four convincing variants and two view-dependent live demos; no unsupported glTF node features are silently lost. Visual behavior validated in the target viewer.

### Phase 6. Productize the library and UI system
**Objective:** Make materials searchable, composable and useful to engineers.

**Gallery:** filter by family, visual quality, supported outputs, base color, tileability, roughness, scale, motion, performance tier and license. Show material ball, flat 2D tile, optional preview on button/card/hero, before/after lighting, turntable, generated variants and a provenance panel.

**Component adapters:** CSS variables for texture URI, texture scale, border shade, overlay strength, shadow depth, pressed offset; real DOM text, hover, pressed, disabled, selected, focus-visible, keyboard and touch states. Use CSS masks / 9-slice textures for irregular edges when needed. Use 3D only where it adds experience, not merely decoration.

**Runtime:** lazy-load media, responsive image sizes, maintain contrast behind text, pause animation offscreen, use `prefers-reduced-motion`, provide image and reduced-data fallbacks, and never let effects block navigation.

**Exit:** Storybook with interactive controls across screen sizes, documented API, public static gallery, downloadable sample bundles, first third-party integration example.

### Phase 7. Automation, performance and open-source release
**Objective:** Scale through reproducible agent-driven production without quality collapse.

- Content-addressed cache by generator revision + parameters + Blender version + lighting + export profile; recompute only affected stages.
- Automated parameter exploration with 4–12 deterministic seeds but human/visual gate for visual fidelity. Keep both successes and rejected variants with reasons.
- CI runs fast headless checks for all changes and selective render validations. Nightly high-quality gallery coverage and regression comparison on a calibrated runner.
- Accept contributor packs only with source/credit/license, reproducible recipe, tests, previews, runtime budgets and photographic reference board.
- Track four operational metrics: material acceptance rate, median generation/render time, browser byte cost, and visual fidelity/UX review score. Optimization work earns priority when it improves total system value.

**Exit:** A new material can move from reviewed reference to published web pack through a documented workflow with bounded manual inspection. 100% of published assets have valid provenance and reproducible manifests.

## 7. Delivery profiles and budgets (initial targets; tune with measurements)

| Target | Master/source | Web delivery | Expected use |
|---|---|---|---|
| Thumbnail / card | 2K–4K EXR/PNG master | AVIF/WebP 256–768px, usually ≤100KB | galleries, cards |
| UI control skin | 1K–2K source | responsive small slices/tiles, initially aim ≤150KB per visible decorative skin | buttons, sidebars |
| Background/hero | 4K master | AVIF/WebP responsive, initially aim ≤500KB–1MB for hero | page visuals |
| Tiled PBR | high-precision source maps | 1K/2K presets plus 4K optional; document GPU memory cost | WebGL/Three.js |
| Optimized geometry | high-poly source mesh | GLB with LOD/geometry optimization and supported texture formats | optional 3D |
| Motion | high-fidelity frame sequence | MP4/WebM short loop or CSS/shader when cheaper; poster fallback | waves, glow, mist |

Web image delivery and GPU texture delivery have different compression constraints. AVIF/WebP can work for DOM/CSS and some runtime images; **KTX2/Basis** is often better for GPU-resident 3D maps. Prefer UASTC for normal maps or other data susceptible to artifacts; test ETC1S for less-sensitive color maps. Do not apply lossy color compression indiscriminately to vector/height data.

Performance budgets, to be tested on real mobile and desktop:
- Main experience: Lighthouse/Web Vitals targets aligned with **LCP ≤2.5s**, **INP ≤200ms**, **CLS ≤0.1** at p75 under representative real-user conditions.
- Scrolling and animations: avoid sustained main-thread work, aim for smooth frame pacing; treat 60 FPS as a device-dependent aspiration, not a CI pass claim without measurement.
- All interactive controls work without JS unless JS is essential to their behavior. No WebGL in initial route bundle by default.
- Headless render capability reports avoid assuming large VRAM; batch image baking and use CPU/render-tiling fallback on resource-constrained hosts.

## 8. Automated validation and acceptance criteria

**Structure and provenance:** schema validates, deterministic IDs, source paths and hashes exist, reference license reviewed, no missing textures, no broken GLB references. Material names and parameter controls documented.

**Render physicality:** material scale checked against known real-world size; albedo contains no baked direct shadows; normals/roughness have correct color space and handedness; basic energy response checked under neutral HDRI and raking light. Use consistent ACES/AgX-like display transforms for comparison and document transform.

**Seam testing:** render tile as a 3×3 repeating plane, test opposite-edge color and tangent-space normal continuity with tunable pixel thresholds; require reviewer sign-off on close/long-range repeats. Procedural textures can be mathematically tileable and still show obvious visual repetition — test both.

**3D:** validate glTF spec and supported extensions; inspect file size, UV/tangents, normal orientation, material conversion, bounds, and load in WebGL/WebGPU target before publish. Add an explicit unsupported-feature fallback for SSS, water volumes, complex iridescence and custom emission behavior.

**UI/accessibility:** focus visible, sensible contrast across varied material patterns, 44px-ish comfortable touch target when appropriate, semantics, keyboard and screen reader labels, `prefers-reduced-motion`, no meaningful information encoded only as texture/color, touch vs hover interaction parity.

**Perceptual QA:** evaluate multi-light response, physical feature size, reference photographic resemblance, close-range and actual CSS pixel-scale appearance. Run fixed screenshot diffs after material changes; diffs require review not automatic rejection of all improvements.

**Release artifacts:** immutable approved manifest, thumbnails, source Blender/recipe, map pack, demo, measured sizes and QA receipt.

## 9. Backlog: initial ten small, independently reviewable issues

| Priority | Issue | Acceptance |
|---|---|---|
| P0 | 01 — Monorepo scaffold and `doctor` | local/CI versions pinned, diagnostic exit codes, clean fresh clone |
| P0 | 02 — Material JSON schema + provenance | schema test, author/reference/license required, demo recipe |
| P0 | 03 — Calibrated Blender scene rig | reproducible HDRI/studio/grazing renders + measured scene scale |
| P0 | 04 — Reusable stone slab & button geometry | exposed shape/chip/bevel parameters; high/low mesh profiles |
| P0 | 05 — Vesicular basalt procedural generator | documented pore morphology, seed variation, physical scale |
| P0 | 06 — Slate layered generator | strata direction, fracture geometry, glancing-light comparison |
| P0 | 07 — Porous limestone generator | limestone differs materially from basalt, density/pore controls |
| P0 | 08 — Bake and export pack v0 | albedo, roughness, normals, height + color space/UV gates |
| P0 | 09 — Browser component proof | semantic button, segmented control, card; keyboard/mobile states |
| P0 | 10 — End-to-end benchmark & visual review | gallery, 3 material receipts, cold-load bytes and GPU/CPU cost |

After these ten issues pass, open the next ten for geological expansion; avoid starting all five families before completing the one fully validated vertical slice.

## 10. Work lanes / autonomous workflow

Parallelism is useful if it does not undermine the first vertical slice:
1. **Material science/reference:** source photos, mineral taxonomy, relevant scales, palette and licensing.
2. **Procedural Blender:** calibrated geometry and shader libraries.
3. **Baking/export:** UV generation, map conversions, GLB optimization.
4. **Web components:** CSS/HTML, TypeScript gallery and optional Three.js preview.
5. **Validation/performance:** visual baselines, testing, profiling.
6. **Docs/community:** manifests, contributor guidance, credit and review.

Each lane maintains a queue of 5+ ready, bounded issues. Keep work local/fork-only until reproducible tests and review are green. Parallelize independent families after the MVP establishes contracts. Every action writes a receipt and next actionable item; avoid speculative "pass" status.

**Human-required gates:** copyright/license provenance disputes, final aesthetics, claims of realistic physics, surprising deviations in material morphology, accessibility sign-off for complex compositions and publishing assets with non-CC0 dependencies. Automated tests cannot assert photorealism by themselves.

## 11. Risks and mitigations

- **Photoreal renders ≠ physically correct PBR maps:** separately bake clean channels and validate under multiple lights.
- **Biological/volumetric materials ≠ flat tiles:** use per-class outputs; foliage cutouts, 3D leaves, fog planes/volumes, looping lights.
- **Procedural variation ≠ realism:** check species/mineral morphology and scale against real-world reference; combine measured/scanned data with procedural details.
- **Blender → glTF mismatch:** advanced nodes/SSS, displacement and some volume effects must be baked or reimplemented in the web shader; inspect target renderer.
- **Stone UI readability:** keep labels, accessible states and overlays separate from decorative textures, manage contrast and tap targets.
- **Huge binary repository:** use content-addressed build artifacts; only compact previews and recipes live in normal Git history.
- **Realism vs mobile performance:** responsive profiles, lazy load, baked approximation first, WebGL opt-in.
- **Provenance:** supplied designs display `@jimiplouffe` credit; verify actual ownership/permission and preserve attribution; CC0 sources must be tracked individually.

## 12. Milestones / decision gates

**M0 (infrastructure):** one baseline sample builds end-to-end with hashes and tests.  
**M1 (first user value):** basalt/slate/limestone live as reusable semantic controls; measured mobile performance.  
**M2 (material system):** 10+ validated geological assets with parameter variation.  
**M3 (taxonomy proven):** leaf/bark/moss, water/glow, iridescence and frost each work through correct delivery class.  
**M4 (public ecosystem):** usable website/gallery and contribution contract; reproducible release.  
**M5 (scale):** automated generation and QA shorten time from recipe to accepted material without reducing quality.

## 13. First agent execution prompt (paste to Hermes/Codex/Claude)

> Implement **Phase 0 and only the Phase 1 basalt vertical slice** for the Natural Materials System. First inspect existing repos, environment, toolchain and any material/Blender work so we reuse it rather than duplicate it. Do not post upstream or publish without approval. Create a minimal reproducible repo scaffold with the structure and material contract in this roadmap; pin dependencies, and build a `doctor` command. Generate a Blender 5.x-compatible calibrated material swatch and reusable stone slab/button geometry; produce seeded *vesicular basalt* using physical-scale pores, layered roughness and asymmetric worn edges. Output a `.blend`/generator, master maps, 1K web pack, flat sample, sphere/slab/button renders and a provenance manifest. Build one working semantic HTML/CSS button using text-free baked textures and real DOM text/icons, with hover/press/focus/disabled states and reduced-motion fallback. Run Blender headless, bake/validate colorspace, screenshot the UI at desktop/mobile sizes, measure asset byte size, and record commands, actual pass/fail receipts and next small issues. On failure, fix and retry boundedly; do not claim photorealism automatically. Deliver a short status report with links/paths, measurements, blockers and the next exact 10 issues.

This one-material slice should precede a mass render wave; it discovers the real bottlenecks early.

## 14. Source and standards links

- Blender Cycles baking manual: https://docs.blender.org/manual/en/latest/render/cycles/baking.html
- Khronos glTF and extensions: https://www.khronos.org/gltf/
- KTX2/Basis glTF extension: https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_texture_basisu/README.md
- glTF Transform official tools: https://gltf-transform.dev/
- Poly Haven asset license: https://polyhaven.com/license
- Poly Haven API Terms (separate from asset license): https://github.com/Poly-Haven/Public-API/blob/master/ToS.md

**Note:** These links guide implementation; recheck exact documentation against the pinned Blender/Three.js/exporter versions during Phase 0.