<script setup lang="ts">
// Home page in the library's own language: real material imagery, carved stone
// panels and buttons, serif display type. GPL-3.0-only.
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
const img = (path: string | null) => (path ? withBase(path) : "");

const PRINCIPLES = [
	{ id: "geo.granite.speckled.v1", title: "Perception over polygons", text: "Ship the cheapest asset that holds the look: a CSS tile for most UI, a relit shader for hero surfaces, 3D almost never." },
	{ id: "bot.bark.oak.v1", title: "Inspectable materials", text: "Every pack records physical scale, seed, provenance and a SHA-256 for every map. Nothing is called calibrated until it is." },
	{ id: "aq.water.ripple.v1", title: "Controls stay HTML", text: "Textures never contain text or focus states. Material sits underneath real, accessible DOM." },
	{ id: "fauna.nacre.shell.v1", title: "One source, many outputs", text: "Maps derive from a single source; generated four-panel “PBR atlases” are illustrations, not data." },
];
const material = (id: string) => data.materials.find((m) => m.id === id);

const TARGETS = [
	{ name: "Web & phones", detail: "<elemental-surface> · WebGPU → WebGL2 → CSS", link: "/runtime/web" },
	{ name: "Native", detail: "elemental-render · wgpu on Vulkan, Metal, DX12", link: "/runtime/native" },
	{ name: "Hyprland", detail: "per-monitor wallpapers from the same shader", link: "/runtime/hyprland" },
	{ name: "Tern", detail: "terminal chrome themed from a pack", link: "/runtime/tern" },
];
</script>

<template>
	<div class="eh">
		<!-- Hero: a slab of real slate with a carved basalt component on it -->
		<section class="eh-hero" :style="{ '--hero': `url(${img('/materials/geo.slate.layered.v1.webp')})` }">
			<div class="eh-hero-inner">
				<div class="eh-copy">
					<p class="el-eyebrow eh-eyebrow">Natural materials for interfaces</p>
					<h1 class="el-display">Earth,<br />as an interface.</h1>
					<p class="eh-lede">
						Stone, bark, water, ice and shell as material packs with one shared lighting shader, painted by thin
						drivers for the web, phones, a Hyprland desktop and Tern.
					</p>
					<div class="eh-actions">
						<a class="el-btn brand" :href="withBase('/taxonomy/')">Explore the materials</a>
						<a class="el-btn alt" :href="withBase('/guide/getting-started')">Get started</a>
					</div>
				</div>

				<article class="eh-card el-stone" aria-label="Example component in basalt">
					<p class="el-eyebrow eh-card-eyebrow">GEO-01 · igneous</p>
					<h2 class="el-display">Vesicular Basalt</h2>
					<p>Charcoal lava rock with gas cavities and pale mineral inclusions. 240 mm tile, 1.8 mm relief.</p>
					<div class="eh-card-row">
						<a class="el-btn alt eh-card-btn" :href="withBase('/taxonomy/')">Explore</a>
						<span class="eh-inset">prototype</span>
					</div>
				</article>
			</div>
		</section>

		<!-- The material wall -->
		<section class="eh-section">
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
					<img :src="img(m.image)" :alt="m.display_name" loading="lazy" decoding="async" />
					<span class="eh-tile-label">
						<small>{{ m.family }}</small>
						{{ m.display_name }}
					</span>
				</a>
			</div>
			<div class="eh-center"><a class="el-btn brand" :href="withBase('/taxonomy/')">See the full taxonomy</a></div>
		</section>

		<!-- Principles, each carved from a material -->
		<section class="eh-section">
			<header class="eh-head">
				<div>
					<p class="el-eyebrow">Ethos</p>
					<h2 class="el-display">A material engine, not a folder of JPEGs</h2>
				</div>
			</header>
			<div class="eh-principles">
				<a v-for="p in PRINCIPLES" :key="p.title" class="eh-principle" :href="withBase('/guide/ethos')">
					<div class="eh-principle-img" :style="{ backgroundImage: `url(${img(material(p.id)?.image ?? null)})` }" />
					<div class="eh-principle-body">
						<h3 class="el-display">{{ p.title }}</h3>
						<p>{{ p.text }}</p>
					</div>
				</a>
			</div>
		</section>

		<!-- One shader, every target -->
		<section class="eh-section eh-split">
			<div class="eh-shader el-stone is-slate">
				<p class="el-eyebrow eh-card-eyebrow">shaders/elemental_surface.wgsl</p>
				<h2 class="el-display">One shader, every target.</h2>
				<p>
					Lighting lives in one WGSL file. Native and WebGPU compile it directly; WebGL2 runs GLSL generated from it by
					naga, byte-identical to native on the GPU.
				</p>
				<a class="el-btn alt" :href="withBase('/runtime/')">Runtime architecture</a>
			</div>
			<ul class="eh-targets">
				<li v-for="t in TARGETS" :key="t.name">
					<a :href="withBase(t.link)">
						<strong class="el-display">{{ t.name }}</strong>
						<span>{{ t.detail }}</span>
					</a>
				</li>
			</ul>
		</section>
	</div>
</template>

<style scoped>
.eh { --pad: clamp(20px, 5vw, 64px); }

/* Hero */
.eh-hero {
	position: relative;
	margin-top: calc(var(--vp-nav-height) * -1);
	padding: calc(var(--vp-nav-height) + clamp(48px, 9vw, 120px)) var(--pad) clamp(56px, 8vw, 110px);
	background:
		linear-gradient(100deg, rgb(12 13 14 / 0.9) 0%, rgb(12 13 14 / 0.62) 46%, rgb(12 13 14 / 0.15) 100%),
		linear-gradient(0deg, var(--vp-c-bg) 0, transparent 120px),
		var(--hero) center / cover,
		#1d2023;
	color: #f3eee5;
}
.eh-hero-inner {
	max-width: 1240px;
	margin: 0 auto;
	display: grid;
	grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.75fr);
	gap: clamp(32px, 6vw, 80px);
	align-items: center;
}
.eh-eyebrow { color: #cdbfa9; }
.eh-hero h1 {
	font-size: clamp(3rem, 7.2vw, 6.2rem);
	line-height: 0.98;
	margin: 14px 0 22px;
	letter-spacing: -0.02em;
	text-shadow: 0 2px 24px rgb(0 0 0 / 0.45);
}
.eh-lede { font-size: clamp(1.05rem, 1.5vw, 1.25rem); line-height: 1.6; color: #ddd3c5; max-width: 34em; margin: 0 0 32px; }
.eh-actions { display: flex; flex-wrap: wrap; gap: 14px; }

.eh-card { border-radius: 22px; padding: clamp(22px, 3vw, 34px); }
.eh-card-eyebrow { color: rgb(248 238 224 / 0.62); margin: 0 0 6px; }
.eh-card h2 { font-size: clamp(1.8rem, 2.8vw, 2.4rem); margin: 0 0 10px; line-height: 1.1; }
.eh-card p { color: rgb(248 238 224 / 0.84); line-height: 1.6; margin: 0 0 24px; }
.eh-card-row { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.eh-card-btn { min-height: 46px; }
.eh-inset {
	border-radius: 12px;
	padding: 8px 14px;
	font-size: 0.82rem;
	letter-spacing: 0.08em;
	background: rgb(0 0 0 / 0.22);
	box-shadow: inset 2px 4px 9px rgb(0 0 0 / 0.35), inset -1px -2px 3px rgb(255 255 255 / 0.1);
}

/* Sections */
.eh-section { max-width: calc(1240px + 2 * var(--pad)); margin: 0 auto; padding: clamp(48px, 7vw, 96px) var(--pad) 0; }
.eh-section:last-child { padding-bottom: clamp(64px, 8vw, 120px); }
.eh-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: 16px 40px; margin-bottom: 28px; }
.eh-head h2 { font-size: clamp(2rem, 3.4vw, 3rem); line-height: 1.08; margin: 8px 0 0; }
.eh-note { max-width: 34em; margin: 0; color: var(--vp-c-text-2); font-size: 0.95rem; line-height: 1.6; }
.eh-center { display: flex; justify-content: center; margin-top: 34px; }

/* Material wall */
.eh-wall { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 14px; }
@media (max-width: 1100px) { .eh-wall { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 560px) { .eh-wall { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.eh-tile {
	position: relative;
	display: block;
	aspect-ratio: 4 / 3;
	border-radius: 18px;
	overflow: hidden;
	background: #2a2b2c;
	box-shadow: 0 6px 14px rgb(37 28 17 / 0.2);
	text-decoration: none;
	transition: transform 0.16s ease, box-shadow 0.16s ease;
}
.eh-tile img { width: 100%; height: 100%; object-fit: cover; display: block; transform: scale(1.02); transition: transform 0.5s ease; }
.eh-tile::after {
	content: "";
	position: absolute;
	inset: 0;
	border-radius: inherit;
	box-shadow: inset 1px 2px 0 rgb(255 255 255 / 0.18), inset -2px -3px 0 rgb(0 0 0 / 0.28);
	background: linear-gradient(180deg, transparent 50%, rgb(10 10 10 / 0.72));
	pointer-events: none;
}
.eh-tile-label { position: absolute; left: 14px; bottom: 12px; z-index: 1; color: #f8eee0; font: 500 1.12rem/1.15 var(--el-serif); }
.eh-tile-label small { display: block; font: 600 0.62rem/1.4 var(--vp-font-family-base); letter-spacing: 0.2em; text-transform: uppercase; color: rgb(248 238 224 / 0.7); }
.eh-tile:hover { transform: translateY(-3px); box-shadow: 0 12px 26px rgb(37 28 17 / 0.28); }
.eh-tile:hover img { transform: scale(1.08); }

/* Principles */
.eh-principles { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
.eh-principle {
	display: flex;
	flex-direction: column;
	border-radius: 20px;
	overflow: hidden;
	background: var(--vp-c-bg-elv);
	border: 1px solid var(--vp-c-divider);
	box-shadow: inset 2px 2px rgb(255 255 255 / 0.4), 0 14px 30px rgb(26 18 10 / 0.12);
	text-decoration: none;
	color: inherit;
	transition: transform 0.14s ease;
}
.dark .eh-principle { box-shadow: inset 1px 1px rgb(255 255 255 / 0.05), 0 14px 30px rgb(0 0 0 / 0.35); }
.eh-principle:hover { transform: translateY(-3px); }
.eh-principle-img { height: 118px; background-size: cover; background-position: center; box-shadow: inset 0 -12px 18px -12px rgb(0 0 0 / 0.4); }
.eh-principle-body { padding: 18px 20px 22px; }
.eh-principle h3 { font-size: 1.35rem; margin: 0 0 8px; }
.eh-principle p { margin: 0; color: var(--vp-c-text-2); line-height: 1.6; font-size: 0.95rem; }

/* Shader split */
.eh-split { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr); gap: 20px; align-items: stretch; }
.eh-shader { border-radius: 24px; padding: clamp(26px, 4vw, 44px); }
.eh-shader h2 { font-size: clamp(2rem, 3.4vw, 2.8rem); margin: 0 0 14px; line-height: 1.05; }
.eh-shader p { color: rgb(248 238 224 / 0.86); line-height: 1.65; max-width: 32em; margin: 0 0 26px; }
.eh-targets { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; }
.eh-targets a {
	display: flex;
	flex-direction: column;
	gap: 4px;
	height: 100%;
	padding: 18px 22px;
	border-radius: 18px;
	background: var(--vp-c-bg-elv);
	border: 1px solid var(--vp-c-divider);
	box-shadow: inset 1px 3px 4px rgb(40 30 20 / 0.08);
	text-decoration: none;
	color: inherit;
}
.eh-targets a:hover { border-color: var(--vp-c-brand-2); }
.eh-targets strong { font-size: 1.3rem; font-weight: 500; }
.eh-targets span { color: var(--vp-c-text-2); font-size: 0.9rem; font-family: var(--vp-font-family-mono); }

@media (max-width: 900px) {
	.eh-hero-inner, .eh-split { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
	.eh-tile, .eh-tile img, .eh-principle { transition: none; }
}
</style>
