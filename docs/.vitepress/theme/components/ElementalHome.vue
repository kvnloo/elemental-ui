<script setup lang="ts">
// Home page: full-bleed materials with frosted-glass UI over them, so the
// material is always the surface and never hidden behind grey panels.
// GPL-3.0-only.
import { computed } from "vue";
import { withBase } from "vitepress";
import { data } from "../../../taxonomy.data";

const FAMILY_ORDER = ["geological", "botanical", "aquatic", "atmospheric", "fauna"];
const shown = computed(() =>
	data.materials
		.filter((m) => m.image)
		.sort((a, b) => FAMILY_ORDER.indexOf(a.family) - FAMILY_ORDER.indexOf(b.family)),
);
const counts = computed(() => ({
	total: data.materials.length,
	families: new Set(data.materials.map((m) => m.family)).size,
	imaged: shown.value.length,
}));
const byId = (id: string) => data.materials.find((m) => m.id === id);
/** Largest available image for full-bleed use. */
const large = (id: string) => {
	const m = byId(id);
	return withBase(m?.image_large ?? m?.image ?? "");
};
const bg = (id: string) => `url(${large(id)})`;

const PRINCIPLES = [
	{ id: "geo.granite.speckled.v1", title: "Perception over polygons", text: "Ship the cheapest asset that holds the look: a CSS tile for most UI, a relit shader for hero surfaces, 3D almost never." },
	{ id: "bot.bark.oak.v1", title: "Inspectable materials", text: "Every pack records physical scale, seed, provenance and a SHA-256 for every map. Nothing is called calibrated until it is." },
	{ id: "aq.water.ripple.v1", title: "Controls stay HTML", text: "Textures never contain text or focus states. Material sits underneath real, accessible DOM." },
	{ id: "fauna.nacre.shell.v1", title: "One source, many outputs", text: "Maps derive from a single source; generated four-panel “PBR atlases” are illustrations, not data." },
];

const TARGETS = [
	{ name: "Web & phones", detail: "<elemental-surface> · WebGPU → WebGL2 → CSS", link: "/runtime/web" },
	{ name: "Native", detail: "elemental-render · wgpu on Vulkan, Metal, DX12", link: "/runtime/native" },
	{ name: "Hyprland", detail: "per-monitor wallpapers from the same shader", link: "/runtime/hyprland" },
	{ name: "Tern", detail: "terminal chrome themed from a pack", link: "/runtime/tern" },
];
</script>

<template>
	<div class="eh">
		<!-- Hero: full-bleed slate, glass UI floating on it -->
		<section class="eh-hero eh-bleed" :style="{ '--bg': bg('geo.slate.layered.v1') }">
			<div class="eh-inner eh-hero-grid">
				<div class="eh-copy">
					<p class="el-eyebrow eh-light">Natural materials for interfaces</p>
					<h1 class="el-display">Earth,<br />as an interface.</h1>
					<p class="eh-lede">
						Stone, bark, water, ice and shell as material packs with one shared lighting shader, painted by thin
						drivers for the web, phones, a Hyprland desktop and Tern.
					</p>
					<div class="eh-actions">
						<a class="el-glass-btn is-solid" :href="withBase('/taxonomy/')">Explore the materials</a>
						<a class="el-glass-btn" :href="withBase('/guide/getting-started')">Get started</a>
					</div>
				</div>

				<article class="eh-card el-glass" aria-label="Example component">
					<div class="eh-card-media" :style="{ backgroundImage: bg('geo.basalt.vesicular.v1') }">
						<span class="el-glass-pill">GEO-01 · igneous</span>
					</div>
					<h2 class="el-display">Vesicular Basalt</h2>
					<p>Charcoal lava rock with gas cavities and pale mineral inclusions. 240 mm tile, 1.8 mm relief.</p>
					<div class="eh-card-row">
						<a class="el-glass-btn is-solid" :href="withBase('/taxonomy/#geological')">Explore</a>
						<span class="el-glass-pill">prototype</span>
					</div>
				</article>
			</div>
		</section>

		<!-- The material wall: materials edge to edge, glass labels -->
		<section class="eh-section">
			<div class="eh-inner">
				<header class="eh-head">
					<div>
						<p class="el-eyebrow">The library so far</p>
						<h2 class="el-display">{{ counts.total }} materials across {{ counts.families }} families</h2>
					</div>
					<p class="eh-note">
						Shown: {{ counts.imaged }} hero macros generated with gpt-image-2 as visual targets. They set the look;
						texture maps are derived from one source in Blender.
					</p>
				</header>
				<div class="eh-wall">
					<a v-for="m in shown" :key="m.id" class="eh-tile" :href="withBase('/taxonomy/#' + m.family)">
						<img :src="withBase(m.image!)" :alt="m.display_name" loading="lazy" decoding="async" />
						<span class="eh-tile-label el-glass">
							<small>{{ m.family }}</small>
							{{ m.display_name }}
						</span>
					</a>
				</div>
			</div>
		</section>

		<!-- Ethos: each principle is a slab of its material with glass copy -->
		<section class="eh-section">
			<div class="eh-inner">
				<header class="eh-head">
					<div>
						<p class="el-eyebrow">Ethos</p>
						<h2 class="el-display">A material engine, not a folder of JPEGs</h2>
					</div>
					<a class="eh-link" :href="withBase('/guide/ethos')">Read the ethos →</a>
				</header>
				<div class="eh-principles">
					<a v-for="p in PRINCIPLES" :key="p.title" class="eh-principle" :href="withBase('/guide/ethos')" :style="{ backgroundImage: bg(p.id) }">
						<div class="eh-principle-body el-glass">
							<p class="eh-principle-tag">{{ byId(p.id)?.display_name }}</p>
							<h3 class="el-display">{{ p.title }}</h3>
							<p>{{ p.text }}</p>
						</div>
					</a>
				</div>
			</div>
		</section>

		<!-- One shader, every target: full-bleed ice, all glass -->
		<section class="eh-bleed eh-shader-band" :style="{ '--bg': bg('atm.ice.sheet.v1') }">
			<div class="eh-inner eh-split">
				<div class="eh-shader el-glass">
					<p class="el-eyebrow eh-light">shaders/elemental_surface.wgsl</p>
					<h2 class="el-display">One shader, every target.</h2>
					<p>
						Lighting lives in one WGSL file. Native and WebGPU compile it directly; WebGL2 runs GLSL generated from it
						by naga, byte-identical to native on the GPU.
					</p>
					<a class="el-glass-btn is-solid" :href="withBase('/runtime/')">Runtime architecture</a>
				</div>
				<ul class="eh-targets">
					<li v-for="t in TARGETS" :key="t.name">
						<a class="el-glass" :href="withBase(t.link)">
							<strong class="el-display">{{ t.name }}</strong>
							<span>{{ t.detail }}</span>
						</a>
					</li>
				</ul>
			</div>
		</section>
	</div>
</template>

<style scoped>
.eh { --pad: clamp(20px, 5vw, 64px); }
.eh-inner { max-width: 1240px; margin: 0 auto; }
.eh-light { color: rgb(255 255 255 / 0.78); }

/* Full-bleed material bands: the material is the page */
.eh-bleed {
	position: relative;
	padding: clamp(56px, 8vw, 110px) var(--pad);
	background: var(--bg) center / cover no-repeat, #1d2023;
	color: #fff;
}

/* Hero */
.eh-hero {
	margin-top: calc(var(--vp-nav-height) * -1);
	padding-top: calc(var(--vp-nav-height) + clamp(56px, 9vw, 128px));
	padding-bottom: clamp(64px, 9vw, 128px);
	/* Only a soft shade behind the headline; the slate stays visible. */
	background:
		linear-gradient(95deg, rgb(8 9 10 / 0.62) 0%, rgb(8 9 10 / 0.25) 45%, transparent 75%),
		var(--bg) center / cover no-repeat,
		#1d2023;
}
.eh-hero-grid { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(300px, 0.8fr); gap: clamp(32px, 6vw, 88px); align-items: center; }
.eh-hero h1 {
	font-size: clamp(3rem, 7.2vw, 6.4rem);
	line-height: 0.97;
	margin: 14px 0 22px;
	letter-spacing: -0.02em;
	text-shadow: 0 2px 30px rgb(0 0 0 / 0.5);
}
.eh-lede { font-size: clamp(1.05rem, 1.5vw, 1.25rem); line-height: 1.6; color: rgb(255 255 255 / 0.9); max-width: 34em; margin: 0 0 32px; text-shadow: 0 1px 12px rgb(0 0 0 / 0.5); }
.eh-actions { display: flex; flex-wrap: wrap; gap: 12px; }

.eh-card { border-radius: 28px; padding: 14px 14px 24px; }
.eh-card-media {
	position: relative;
	aspect-ratio: 16 / 9;
	border-radius: 18px;
	background-size: cover;
	background-position: center;
	margin-bottom: 20px;
	box-shadow: inset 0 0 0 1px rgb(255 255 255 / 0.18);
}
.eh-card-media .el-glass-pill { position: absolute; left: 12px; top: 12px; }
.eh-card h2 { font-size: clamp(1.8rem, 2.8vw, 2.3rem); margin: 0 12px 8px; line-height: 1.1; }
.eh-card p { margin: 0 12px 22px; line-height: 1.6; color: rgb(255 255 255 / 0.86); }
.eh-card-row { display: flex; align-items: center; gap: 12px; margin: 0 12px; }

/* Sections on the page ground */
.eh-section { padding: clamp(56px, 7vw, 100px) var(--pad) 0; }
.eh-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 16px 40px; margin-bottom: 28px; }
.eh-head h2 { font-size: clamp(2rem, 3.4vw, 3rem); line-height: 1.08; margin: 8px 0 0; }
.eh-note { max-width: 34em; margin: 0; color: var(--vp-c-text-2); font-size: 0.95rem; line-height: 1.6; }
.eh-link { font: 500 1.1rem var(--el-serif); color: var(--vp-c-brand-1); text-decoration: none; }

/* Wall */
.eh-wall { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; }
.eh-tile {
	position: relative;
	display: block;
	aspect-ratio: 1;
	border-radius: 20px;
	overflow: hidden;
	background: #2a2b2c;
	box-shadow: 0 8px 20px rgb(37 28 17 / 0.22);
	text-decoration: none;
	transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.eh-tile img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.6s ease; }
.eh-tile-label {
	position: absolute;
	left: 8px; right: 8px; bottom: 8px;
	padding: 8px 12px;
	border-radius: 14px;
	font: 500 1.02rem/1.15 var(--el-serif);
}
.eh-tile-label small { display: block; font: 600 0.58rem/1.5 var(--vp-font-family-base); letter-spacing: 0.2em; text-transform: uppercase; opacity: 0.75; }
.eh-tile:hover { transform: translateY(-3px); box-shadow: 0 14px 30px rgb(37 28 17 / 0.3); }
.eh-tile:hover img { transform: scale(1.06); }

/* Principles: material slabs */
.eh-principles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
.eh-principle {
	position: relative;
	display: flex;
	align-items: flex-end;
	min-height: 360px;
	padding: 10px;
	border-radius: 26px;
	background-size: cover;
	background-position: center;
	text-decoration: none;
	color: #fff;
	box-shadow: 0 12px 30px rgb(26 18 10 / 0.25);
	transition: transform 0.18s ease;
}
.eh-principle:hover { transform: translateY(-4px); }
.eh-principle-body { border-radius: 18px; padding: 16px 18px 18px; }
.eh-principle-tag { margin: 0 0 4px; font: 600 0.6rem var(--vp-font-family-base); letter-spacing: 0.2em; text-transform: uppercase; opacity: 0.75; }
.eh-principle h3 { font-size: 1.35rem; margin: 0 0 6px; line-height: 1.15; }
.eh-principle p { margin: 0; line-height: 1.55; font-size: 0.92rem; color: rgb(255 255 255 / 0.9); }

/* Shader band */
.eh-shader-band { margin-top: clamp(56px, 7vw, 100px); }
.eh-split { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr); gap: 16px; align-items: stretch; }
.eh-shader { border-radius: 28px; padding: clamp(26px, 4vw, 44px); }
.eh-shader h2 { font-size: clamp(2rem, 3.4vw, 2.8rem); margin: 6px 0 14px; line-height: 1.05; }
.eh-shader p { color: rgb(255 255 255 / 0.9); line-height: 1.65; max-width: 32em; margin: 0 0 26px; }
.eh-targets { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; }
.eh-targets a { display: flex; flex-direction: column; gap: 4px; height: 100%; padding: 18px 22px; border-radius: 20px; text-decoration: none; }
.eh-targets a:hover { background-color: rgb(255 255 255 / 0.2); }
.eh-targets strong { font-size: 1.3rem; font-weight: 500; }
.eh-targets span { color: rgb(255 255 255 / 0.82); font-size: 0.86rem; font-family: var(--vp-font-family-mono); }

@media (max-width: 1100px) {
	.eh-wall { grid-template-columns: repeat(3, minmax(0, 1fr)); }
	.eh-principles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 900px) { .eh-hero-grid, .eh-split { grid-template-columns: 1fr; } }
@media (max-width: 560px) {
	.eh-wall { grid-template-columns: repeat(2, minmax(0, 1fr)); }
	.eh-principles { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
	.eh-tile, .eh-tile img, .eh-principle { transition: none; }
}
</style>
