# Command line

## `tools/elemental.py`

Dependency-free (Python 3.10+). Every command validates all recipes first.

| Command | Does |
|---|---|
| `doctor` | Python version, Blender availability, recipe count |
| `list` | `id - name (status)` for each recipe |
| `validate [--out DIR]` | recipe schema checks; with `--out`, verifies generated manifests and PNG hashes |
| `generate [--material ID] [--size 16-2048, default 256] [--out web/assets]` | draft maps, 2×2 preview, `manifest.json`, `catalog.json` for the gallery |
| `pack [--material ID] [--size 16-1024, power of two] [--out packs]` | runtime packs (`elemental-pack/1`) plus `index.json` |
| `pack --verify [--out packs]` | hash check of every pack file |
| `tern [--packs packs] [--out integrations/tern/elemental-ui] [--default ID]` | Tern plugin textures, `elemental.css`, `materials.luau` |

## `tools/polyhaven.py`

| Command | Does |
|---|---|
| `list` | the curated candidates in `references/geological.json` |
| `probe ASSET` | API metadata, no download |
| `fetch ASSET [--resolution 1k\|2k] [--out DIR] [--preview]` | bounded download with HTTPS host checks, a 24 MiB per-map limit, publisher MD5 and an independent SHA-256; `--preview` writes a contact sheet (needs Pillow) |

Files go to `outputs/external/polyhaven/<asset>/<res>/`, untracked.

## Blender scripts

```bash
blender -b --python blender/stone_preview.py   -- --material ID --out outputs/blender --samples 32 --size 900
blender -b --python blender/render_pbr_pack.py -- --material ID --map-root web/assets --out outputs/blender --samples 8 --size 512
python3 blender/check_exposure.py outputs/blender/ID/pbr-preview.png [--min-luma 8] [--max-luma 180] [--report FILE]
```

## Native and desktop

```bash
./target/release/elemental-render PACK_DIR OUT.png [WIDTH HEIGHT]
integrations/hyprland/elemental-wallpaper MATERIAL_ID [--apply]
```

## npm scripts

| Script | Does |
|---|---|
| `npm run build` | build every workspace (`packages/web/dist/elemental-ui.js`) |
| `npm run typecheck` | `tsc --noEmit` in every workspace |
| `npm run glsl -w @elemental-ui/web` | regenerate the WebGL2 GLSL from the WGSL (naga-cli) |
| `npm run glsl:check -w @elemental-ui/web` | fail if the committed GLSL is stale |
| `npm run docs:dev` / `docs:build` / `docs:preview` | this site; `docs:prepare` copies packs and the bundle in for live swatches |
