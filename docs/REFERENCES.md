# Geological reference acquisition

**Status:** curated candidates, not mineral identification or completed calibration. Tracking [#3](https://github.com/kvnloo/elemental-ui/issues/3).

**Human source credits / original assets** (2026-10-12):
- [Dark Rock](https://polyhaven.com/a/dark_rock) — **Amal Kumar**. Natural charcoal-toned *layered rock*. Visual analogue for dark fractures; **not** confirmed basalt/slate.
- [Volcanic Rock Tiles](https://polyhaven.com/a/volcanic_rock_tiles) — **Charlotte Baglioni**. Pitted basalt-like *masonry* containing tile edges/grout. Use porosity reference only, not a raw seamless rock sample.
- [Slate Floor](https://polyhaven.com/a/slate_floor) — **Dimitrios Savva**. Polished/coated slate flooring with grout, not a naturally fractured slate edge.
- [Coral Ground 02](https://polyhaven.com/a/coral_ground_02) — **Rob Tuytel**. Porous coral-ground carbonate sand + gravel and coastal debris, not pure quarried limestone.

The files are **CC0-1.0** under their publishers' terms. They do *not* become GPL material assets because elemental-ui's code is GPL. Source credit is preserved deliberately even though CC0 does not mandate it.

Live API usage must honor [Poly Haven API ToS](https://github.com/Poly-Haven/Public-API/blob/master/ToS.md), including a unique identifying User-Agent/Referer and visible **“Powered by Poly Haven”** when live data surfaces in software. The optional importer identifies itself; keep user-facing credit in any later integrated browser asset chooser. Do not imply Poly Haven endorsement.

## Usage — nothing downloads automatically

```bash
python3 tools/polyhaven.py list
python3 tools/polyhaven.py probe dark_rock
python3 tools/polyhaven.py fetch dark_rock --resolution 1k
python3 -m pip install Pillow
python3 tools/polyhaven.py fetch dark_rock --resolution 1k --preview
```

All raw downloaded files and receipts are placed under `outputs/external/polyhaven/<asset>/<1k|2k>/` and excluded from git. The importer enforces HTTPS/Poly Haven host origins, 24 MiB per map bounds, publisher-provided MD5, independent SHA256, 1K/2K resolution, safe asset IDs, and explicit provenance. Missing maps fail except for optional displacement. This *records a reference*, not a physical material replacement and not an official publisher integration.

## Next tasks

1. Capture reproducible actual 1K map import and format checks from live source for one representative geological scan.
2. Compare generated and scanned base color, normals, height, pores, layer direction and macro/meso/micro detail under *identical* lighting/camera.
3. Distinguish real capture scale from artistic tile UV: never infer length from resolution alone.
4. Add a first-class external scanned-material schema and sampling transform (including map color-space and gamma handling) before using CC0 scans in the Blender and web gallery.
5. Use direct geometric bevel/damage modeling for button form; photogrammetry textures alone cannot simulate chipped 3D edges.
