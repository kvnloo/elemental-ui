---
layout: home

hero:
  name: elemental-ui
  text: Earth, as an interface
  tagline: Natural material packs with one shared lighting shader, painted by thin drivers for the web, phones, a Hyprland desktop and Tern.
  image:
    src: /mark.svg
    alt: elemental-ui
  actions:
    - theme: brand
      text: Explore the taxonomy
      link: /taxonomy/
    - theme: alt
      text: Getting started
      link: /guide/getting-started
    - theme: alt
      text: Runtime architecture
      link: /runtime/

features:
  - icon: 🪨
    title: 56 materials, 5 families
    details: Geological, botanical, aquatic, atmospheric and fauna materials organised as family › class › material, each tagged with what it is (tile, object, animated surface or volume).
    link: /taxonomy/
  - icon: 📦
    title: Inspectable packs
    details: elemental-pack/1 keeps GPU-repeatable maps, color spaces, physical scale, provenance and a SHA-256 for every file. Nothing is labelled calibrated until it is.
    link: /pipeline/packs
  - icon: ✨
    title: One shader, every target
    details: shaders/elemental_surface.wgsl lights the native wgpu renderer and WebGPU directly. WebGL2 runs naga-generated GLSL from that same file, and its output is byte-identical to native on the GPU.
    link: /runtime/shader
  - icon: 🌐
    title: Cheapest tier that looks right
    details: &lt;elemental-surface&gt; paints a CSS tile first, then upgrades to WebGL2 or WebGPU. It draws only when something changes, and text and controls stay real HTML.
    link: /runtime/web
  - icon: 🖥️
    title: Desktop and dotfiles
    details: Per-monitor Hyprland wallpapers from the native renderer, and a Tern plugin that themes the terminal's chrome.
    link: /runtime/hyprland
  - icon: 🧾
    title: Evidence, not adjectives
    details: Every claim carries a receipt. Parity diffs, hashes and render timings are in the repo, and the gaps are listed alongside them.
    link: /RUNTIME
---
