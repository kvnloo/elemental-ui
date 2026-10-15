<script setup lang="ts">
// Taxonomy explorer: family > class > material, with filters and live swatches
// for materials that already have a runtime pack. GPL-3.0-only.
import { computed, onMounted, ref } from "vue";
import { withBase } from "vitepress";
import { data } from "../../../taxonomy.data";

const FAMILY: Record<string, { label: string; hue: string; blurb: string }> = {
	geological: { label: "Geological", hue: "#8a7a68", blurb: "Rock, minerals, lapidary stone, loose earth and weathering" },
	botanical: { label: "Botanical", hue: "#5f7d4a", blurb: "Foliage, bark, moss, fungi, timber, fibers and seeds" },
	aquatic: { label: "Aquatic", hue: "#3f7891", blurb: "Water surfaces, shorelines and haze" },
	atmospheric: { label: "Atmospheric", hue: "#7f8fa8", blurb: "Ice, condensation, veils, sky, glow and fire" },
	fauna: { label: "Fauna", hue: "#9a6a4f", blurb: "Scales, plumage, iridescence, shell, pattern and biogenic structures" },
};
const KIND: Record<string, string> = {
	"tileable-surface": "Tileable surface",
	"bounded-object": "Bounded object",
	"animated-surface": "Animated surface",
	"volumetric-effect": "Volumetric effect",
};

const query = ref("");
const families = ref<Set<string>>(new Set());
const kinds = ref<Set<string>>(new Set());
const origin = ref<"all" | "atlas" | "roadmap" | "expansion">("all");
const live = ref<Set<string>>(new Set());

const live_tier = ref("auto");

function toggled(set: Set<string>, value: string): Set<string> {
	const next = new Set(set);
	next.has(value) ? next.delete(value) : next.add(value);
	return next;
}
const toggleFamily = (value: string) => (families.value = toggled(families.value, value));
const toggleKind = (value: string) => (kinds.value = toggled(kinds.value, value));

const filtered = computed(() => {
	const q = query.value.trim().toLowerCase();
	return data.materials.filter((m) => {
		if (families.value.size && !families.value.has(m.family)) return false;
		if (kinds.value.size && !kinds.value.has(m.kind)) return false;
		if (origin.value === "atlas" && !m.atlas_code) return false;
		if (origin.value === "roadmap" && m.origin !== "roadmap") return false;
		if (origin.value === "expansion" && !m.origin.startsWith("expansion")) return false;
		if (!q) return true;
		return [m.display_name, m.id, m.class, m.atlas_code ?? "", m.family].some((s) => s.toLowerCase().includes(q));
	});
});

const grouped = computed(() => {
	const out: { family: string; classes: { name: string; items: typeof data.materials }[]; count: number }[] = [];
	for (const family of Object.keys(FAMILY)) {
		const inFamily = filtered.value.filter((m) => m.family === family);
		if (!inFamily.length) continue;
		const classes = [...new Set(inFamily.map((m) => m.class))].map((name) => ({ name, items: inFamily.filter((m) => m.class === name) }));
		out.push({ family, classes, count: inFamily.length });
	}
	return out;
});

const stats = computed(() => {
	const by = (key: "family" | "kind") =>
		data.materials.reduce<Record<string, number>>((acc, m) => ((acc[m[key]] = (acc[m[key]] ?? 0) + 1), acc), {});
	return {
		total: data.materials.length,
		atlas: data.materials.filter((m) => m.atlas_code).length,
		recipes: data.materials.filter((m) => m.recipe).length,
		imaged: data.materials.filter((m) => m.image).length,
		classes: new Set(data.materials.map((m) => `${m.family}/${m.class}`)).size,
		family: by("family"),
		kind: by("kind"),
	};
});

const pretty = (s: string) => s.replace(/-/g, " ");

onMounted(async () => {
	// ?tier=css|webgl2|webgpu forces a runtime tier on the live swatches (testing aid).
	const forced = new URLSearchParams(location.search).get("tier");
	if (forced && ["css", "webgl2", "webgpu"].includes(forced)) live_tier.value = forced;
	try {
		const response = await fetch(withBase("/live/packs/index.json"));
		if (!response.ok) return;
		const index = await response.json();
		await import(/* @vite-ignore */ withBase("/live/elemental-ui.js"));
		live.value = new Set(index.packs.map((p: { id: string }) => p.id));
	} catch {
		// No runtime copy in this build: cards keep their placeholder swatches.
	}
});
</script>

<template>
	<div class="tx">
		<div class="tx-stats">
			<div class="tx-stat"><b>{{ stats.total }}</b><span>materials</span></div>
			<div class="tx-stat"><b>{{ Object.keys(stats.family).length }}</b><span>families</span></div>
			<div class="tx-stat"><b>{{ stats.classes }}</b><span>classes</span></div>
			<div class="tx-stat"><b>{{ stats.atlas }}</b><span>from the reference atlases</span></div>
			<div class="tx-stat"><b>{{ stats.imaged }}</b><span>visual targets generated</span></div>
			<div class="tx-stat"><b>{{ stats.recipes }}</b><span>with a recipe today</span></div>
		</div>

		<div class="tx-tree" aria-label="Hierarchy overview">
			<div v-for="(meta, family) in FAMILY" :key="family" class="tx-tree-family" :style="{ '--hue': meta.hue }">
				<div class="tx-tree-head"><span class="dot" />{{ meta.label }} <small>{{ stats.family[family] ?? 0 }}</small></div>
				<ul>
					<li v-for="c in [...new Set(data.materials.filter((m) => m.family === family).map((m) => m.class))]" :key="c">
						{{ pretty(c) }}
						<small>{{ data.materials.filter((m) => m.family === family && m.class === c).length }}</small>
					</li>
				</ul>
			</div>
		</div>

		<div class="tx-controls">
			<input v-model="query" class="tx-search" type="search" placeholder="Search names, ids, classes, atlas codes…" aria-label="Search materials" />
			<div class="tx-chips el-seg" role="group" aria-label="Families">
				<button v-for="(meta, family) in FAMILY" :key="family" type="button" class="chip" :style="{ '--hue': meta.hue }"
					:aria-pressed="families.has(family)" @click="toggleFamily(family)">{{ meta.label }}</button>
			</div>
			<div class="tx-chips el-seg" role="group" aria-label="Kinds">
				<button v-for="(label, kind) in KIND" :key="kind" type="button" class="chip" :aria-pressed="kinds.has(kind)" @click="toggleKind(kind)">
					{{ label }} <small>{{ stats.kind[kind] ?? 0 }}</small>
				</button>
			</div>
			<div class="tx-chips el-seg" role="radiogroup" aria-label="Origin">
				<button v-for="o in (['all', 'atlas', 'roadmap', 'expansion'] as const)" :key="o" type="button" class="chip" role="radio" :aria-checked="origin === o" :aria-pressed="origin === o" @click="origin = o">
					{{ { all: 'Any origin', atlas: 'In the atlases', roadmap: 'Roadmap', expansion: 'Expansion' }[o] }}
				</button>
			</div>
			<p class="tx-count">{{ filtered.length }} of {{ stats.total }} shown</p>
		</div>

		<section v-for="group in grouped" :key="group.family" class="tx-family" :style="{ '--hue': FAMILY[group.family].hue }">
			<h2 :id="group.family" tabindex="-1">{{ FAMILY[group.family].label }} <small>{{ group.count }} · {{ FAMILY[group.family].blurb }}</small></h2>
			<div v-for="c in group.classes" :key="c.name" class="tx-class">
				<h3>{{ pretty(c.name) }}</h3>
				<div class="tx-grid">
					<article v-for="m in c.items" :key="m.id" class="tx-card" :class="{ 'has-image': m.image }">
						<div class="tx-media">
							<img v-if="m.image" :src="withBase(m.image)" :alt="m.display_name" loading="lazy" decoding="async" />
							<div v-else class="tx-placeholder" aria-hidden="true"><span>not generated yet</span></div>
						</div>
						<div class="tx-body el-glass">
							<div class="tx-name">{{ m.display_name }}</div>
							<code class="tx-id">{{ m.id }}</code>
							<div class="tx-tags">
								<span class="tag" :data-kind="m.kind">{{ KIND[m.kind] }}</span>
								<span v-if="m.atlas_code" class="tag">{{ m.atlas_code }}</span>
								<span v-else class="tag tag-roadmap">roadmap</span>
								<span v-if="m.image" class="tag tag-ai" :title="m.prompt ?? ''">visual target</span>
								<span v-if="m.recipe" class="tag tag-recipe">recipe · {{ m.status }}</span>
								<span v-if="live.has(m.id)" class="tag tag-live">live pack</span>
							</div>
						</div>
					</article>
				</div>
			</div>
		</section>
		<p v-if="!grouped.length" class="tx-empty">No materials match these filters.</p>
	</div>
</template>

<style scoped>
.tx { margin-top: 28px; }
.tx-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-bottom: 28px; }
.tx-stat {
	border-radius: 16px; padding: 14px 16px;
	background: rgb(80 62 40 / 0.07);
	box-shadow: inset 2px 3px 7px rgb(40 30 20 / 0.14), inset -1px -2px 2px rgb(255 255 255 / 0.4);
}
.dark .tx-stat { background: rgb(0 0 0 / 0.25); box-shadow: inset 2px 3px 7px rgb(0 0 0 / 0.5), inset -1px -1px 1px rgb(255 255 255 / 0.05); }
.tx-stat b { display: block; font: 450 2.1rem/1 var(--el-serif); }
.tx-stat span { font-size: 0.78rem; color: var(--vp-c-text-2); }

.tx-tree { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; margin-bottom: 30px; }
.tx-tree-family { border-left: 2px solid var(--hue); padding: 2px 0 2px 14px; }
.tx-tree-head { font: 500 1.15rem var(--el-serif); display: flex; align-items: center; gap: 8px; }
.tx-tree-head small, .tx-tree li small { color: var(--vp-c-text-3); font: 0.75rem var(--vp-font-family-mono); margin-left: auto; }
.tx-tree ul { list-style: none; padding: 0; margin: 6px 0 0; }
.tx-tree li { display: flex; gap: 8px; font-size: 0.84rem; color: var(--vp-c-text-2); text-transform: capitalize; margin: 3px 0; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--hue); display: inline-block; }

.tx-controls { padding: 0 0 6px; margin-bottom: 6px; border-bottom: 1px solid var(--vp-c-divider); }
.tx-search {
	width: 100%; min-height: 46px; padding: 0 16px; border-radius: 14px;
	border: 1px solid rgb(80 62 40 / 0.3); background: var(--vp-c-bg-elv);
	box-shadow: inset 1px 3px 4px rgb(40 30 20 / 0.11); font-size: 0.95rem;
}
.tx-chips { display: inline-flex; flex-wrap: wrap; gap: 4px; margin: 10px 8px 0 0; }
.el-seg { padding: 5px; border-radius: 16px; background: rgb(80 62 40 / 0.09); box-shadow: inset 2px 4px 7px rgb(40 30 20 / 0.14); }
.dark .el-seg { background: rgb(0 0 0 / 0.3); box-shadow: inset 2px 4px 7px rgb(0 0 0 / 0.5); }
.chip {
	border: 0; border-radius: 11px; padding: 7px 13px; min-height: 34px;
	font: 500 0.95rem var(--el-serif); color: var(--vp-c-text-2); background: transparent; cursor: pointer;
}
.chip small { font: 0.72rem var(--vp-font-family-mono); color: var(--vp-c-text-3); }
.chip:hover { color: var(--vp-c-text-1); }
.chip[aria-pressed="true"] {
	color: #f3eee5; background: #242627;
	box-shadow: inset 1px 2px 4px rgb(0 0 0 / 0.6), 0 1px 1px rgb(255 255 255 / 0.3);
}
.chip[aria-pressed="true"] small { color: rgb(243 238 229 / 0.7); }
.tx-count { font-size: 0.78rem; color: var(--vp-c-text-3); margin: 10px 0 0; letter-spacing: 0.04em; }

.tx-family h2 { border-top: none; margin-top: 44px; padding-top: 0; display: flex; align-items: baseline; gap: 12px; font-size: 2rem; }
.tx-family h2::before { content: ""; width: 10px; height: 10px; border-radius: 50%; background: var(--hue); align-self: center; }
.tx-family h2 small { font: 400 0.85rem var(--vp-font-family-base); color: var(--vp-c-text-2); }
.tx-class h3 { text-transform: uppercase; font: 600 0.72rem var(--vp-font-family-base); letter-spacing: 0.2em; color: var(--vp-c-text-3); margin: 22px 0 12px; }
.tx-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(215px, 1fr)); gap: 14px; }

.tx-card {
	position: relative; display: flex; flex-direction: column; justify-content: flex-end;
	aspect-ratio: 4 / 5; padding: 8px; overflow: hidden; border-radius: 22px;
	background: #2a2b2c; color: #fff;
	box-shadow: 0 10px 24px rgb(37 28 17 / 0.22); transition: transform 0.16s ease;
}
.tx-card:hover { transform: translateY(-3px); }
.tx-media { position: absolute; inset: 0; }
.tx-media img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.6s ease; }
.tx-card:hover .tx-media img { transform: scale(1.05); }
.tx-placeholder {
	position: absolute; inset: 0; display: grid; place-items: start center; padding-top: 22%;
	background:
		radial-gradient(circle at 30% 20%, rgb(255 255 255 / 0.22), transparent 55%),
		linear-gradient(160deg, color-mix(in srgb, var(--hue) 75%, #eee), color-mix(in srgb, var(--hue) 55%, #0c0c0c));
}
.tx-placeholder span { font: 600 0.6rem var(--vp-font-family-base); letter-spacing: 0.22em; text-transform: uppercase; color: rgb(255 255 255 / 0.75); }
.tx-body { position: relative; border-radius: 16px; padding: 12px 14px 13px; }
.tx-name { font: 500 1.22rem/1.15 var(--el-serif); }
.tx-id { font-size: 0.66rem; color: rgb(255 255 255 / 0.75); word-break: break-all; background: none !important; padding: 0 !important; }
.tx-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
.tag {
	font: 0.62rem var(--vp-font-family-mono); border-radius: 100px; padding: 2px 8px;
	color: #fff; background: rgb(255 255 255 / 0.12); border: 1px solid rgb(255 255 255 / 0.3);
	text-shadow: none;
}
.tag[data-kind="bounded-object"] { border-color: rgb(255 214 120 / 0.8); }
.tag[data-kind="animated-surface"] { border-color: rgb(130 205 240 / 0.85); }
.tag[data-kind="volumetric-effect"] { border-color: rgb(196 182 255 / 0.85); }
.tag-roadmap { border-style: dashed; }
.tag-ai { background: rgb(255 255 255 / 0.24); }
.tag-recipe { border-color: rgb(170 220 140 / 0.85); }
.tag-live { background: rgb(255 255 255 / 0.85); color: #1b1a18; border-color: transparent; }
.tx-empty { color: var(--vp-c-text-2); }
@media (prefers-reduced-motion: reduce) { .tx-card { transition: none; } }
</style>
