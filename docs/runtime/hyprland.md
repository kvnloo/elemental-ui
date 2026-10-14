# Hyprland wallpapers

`integrations/hyprland/elemental-wallpaper` renders a lit pack at each
monitor's native resolution with the native renderer, then optionally hands
the files to `swaybg`. After the render it uses no GPU at runtime.

```bash
cargo build --release && python3 tools/elemental.py pack
integrations/hyprland/elemental-wallpaper geo.basalt.vesicular.v1           # render only
integrations/hyprland/elemental-wallpaper geo.basalt.vesicular.v1 --apply   # replace running swaybg
```

- Monitors come from `hyprctl monitors -j` (name, width, height).
- Files go to `${XDG_CACHE_HOME:-~/.cache}/elemental-ui/wallpapers/<id>.<output>.<W>x<H>.png`.
- `--apply` runs `pkill -x swaybg`, then
  `swaybg -o <output> -i <file> -m fill …` (detached).

Measured on this host: DP-1 and DP-2 at 1920×1080 rendered in 29 ms and
13 ms. `--apply` has not been run here.

## Planned: live surface

`SurfaceRenderer` can already draw into any wgpu target. The next step is a
small Wayland layer-shell client (smithay-client-toolkit with wgpu) that
redraws only when something changes: a time-of-day light angle, the cursor
position from Hyprland IPC, or a material switch from the dotfiles. It would
give the same pixels as the static render when nothing moves.
