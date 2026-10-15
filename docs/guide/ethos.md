# Ethos

elemental-ui is **a natural-material engine, not a folder of JPEGs**
([Roadmap §1](/ROADMAP#_1-product-definition-and-non-goals)). The rules below
come from the README, the roadmap and the provenance policy, and the code
enforces them where it can.

## Principles

1. **Perception over polygon count.** Ship the cheapest asset that gives the
   look you want. Most UI gets a CSS tile, some surfaces get a relit shader,
   and very few things get 3D.
2. **Materials must be inspectable.** Every material records its physical
   scale, seed, recipe, source credit, checksums and known limitations.
   `elemental-pack/1` keeps a SHA-256 for every file.
3. **Controls stay semantic HTML.** Textures never contain text, focus rings
   or interaction state. `<elemental-surface>` puts the material under
   ordinary DOM.
4. **No unlicensed source photos.** Visual inspiration does not grant
   permission to redistribute. The STONE studies credited to
   **@jimiplouffe** are referenced, not copied.
5. **One source, many outputs.** Every texture map comes from one common
   source. Generated four-panel "PBR atlases" are illustrations, not maps.
6. **Honest labels.** A `prototype` stays a prototype. AI-generated imagery is
   a *visual target*, not measured PBR data. `source.calibrated` stays `false`
   until calibration has actually been done.

## Four kinds of output

Not everything is a seamless tile. Every catalog entry declares one kind:

| Kind | Examples | Deliverables |
|---|---|---|
| `tileable-surface` | basalt, oak bark, fish scales | repeatable PBR maps, CSS tile, relit surface |
| `bounded-object` | broad leaf, river pebble, seed pod | geometry plus maps, cutouts, GLB later |
| `animated-surface` | rippled water, caustics, bioluminescence | normal animation or loops with a still fallback |
| `volumetric-effect` | mist, fog, light shafts | Blender volumes published as stills, loops or runtime effects |

## Performance rules for the runtime

- An idle page costs nothing: GPU tiers redraw on input, never in a loop.
- The CSS layer paints first, so a slow or missing GPU path never leaves a
  blank box.
- One shader file is the only place lighting lives. Native and web are
  checked against each other pixel for pixel.
- Device pixel ratio is capped at 2, and surfaces stop drawing while off
  screen.

These follow the Quackles performance research: decoding, uploading and
publishing a frame are budgeted separately, and the camera never waits for a
refinement.
