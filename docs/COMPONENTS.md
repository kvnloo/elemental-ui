# Web components

Import the dependency-free \`web/elemental.css\` stylesheet. The styles work with native HTML \`button\` elements and keep labels, focus, hover and pressed state out of the texture images.

\`\`\`html
<link rel="stylesheet" href="elemental.css">
<button class="el-surface el-button" type="button"
        data-material="geo.basalt.vesicular.v1"
        style="--el-texture: url('assets/geo.basalt.vesicular.v1/basecolor.png')">
  Explore <span aria-hidden="true">→</span>
</button>
\`\`\`

Modifiers: \`.el-surface\`, \`.el-button\`, \`.el-panel\`, \`.el-inset\`, \`.el-segmented\`, \`.el-choice\`, \`.el-range\`.

- Raised button: default CSS box and inset highlights.
- Pressed: native \`:active\` or semantic \`aria-pressed="true"\` (toggle buttons).
- Disabled: native \`disabled\` attribute, no fake clickable wrappers.
- Keyboard: \`:focus-visible\` outline, Tab/Enter/Space.
- Reduced motion: transitions/transforms disabled under \`prefers-reduced-motion\`.
- Image absent: CSS fallback gradients; no network font or mandatory WebGL.

Sample gallery: \`python3 tools/elemental.py generate --size 256 --out web/assets\`, then \`python3 -m http.server -d web 8080\`.

**Caution:** the generated maps are first-pass procedural studies; they are not scanned PBR materials. Real-world physical measurements, Blender shader/bake parity and mobile browser performance tests are pending.
