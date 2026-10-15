# elemental-ui for Tern

Paints Tern's page, pane headers and status line with an elemental-ui material
pack. The default material comes from the manifest `styles`, so it also reaches
Tern's web tab; palette commands (`Elemental: …`) switch materials per window.

```sh
python3 tools/elemental.py pack                 # build packs/
python3 tools/elemental.py tern                 # copy textures, write elemental.css + materials.luau
tern plugin link integrations/tern/elemental-ui
```

Tern resolves `url()` against the plugin directory, so the build copies each
pack's base color into `textures/`. Those files, `elemental.css` and
`materials.luau` are generated and not tracked. This is the CSS tier (static
base color under a legibility veil); Tern's sheets have no custom shaders, so
live relighting stays with the web and native runtimes.
