<script setup lang="ts">
// Taxonomy explorer: family > class > material, with filters and live swatches
// for materials that already have a runtime pack. GPL-3.0-only.
import { computed, onMounted, ref } from "vue";
import { withBase } from "vitepress";
import { data } from "../../../taxonomy.data";

const FAMILY: Record<string, { label: string; hue: string; blurb: string }> = {
	geological: { label: "Geological", hue: "#8a7a68", blurb: "Stone, crystal and loose earth" },
	botanical: { label: "Botanical", hue: "#5f7d4a", blurb: "Foliage, bark, moss, wood and seeds" },
	aquatic: { label: "Aquatic", hue: "#3f7891", blurb: "Water surfaces, shorelines and haze" },
	atmospheric: { label: "Atmospheric", hue: "#7f8fa8", blurb: "Ice, veils and low-light glow" },
	fauna: { label: "Fauna", hue: "#9a6a4f", blurb: "Scales, plumage, iridescence and shell" },
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
const origin = ref<"all" | "atlas" | "roadmap">("all");
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
		if (origin.value === "roadmap" && m.atlas_code) return false;
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
			<div class="tx-stat"><b>{{ stats.recipes }}</b><span>with a recipe today</span></div>
			<div class="tx-stat"><b>{{ live.size }}</b><span>live packs on this page</span></div>
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
			<div class="tx-chips" role="group" aria-label="Families">
				<button v-for="(meta, family) in FAMILY" :key="family" type="button" class="chip" :style="{ '--hue': meta.hue }"
					:aria-pressed="families.has(family)" @click="toggleFamily(family)">{{ meta.label }}</button>
			</div>
			<div class="tx-chips" role="group" aria-label="Kinds">
				<button v-for="(label, kind) in KIND" :key="kind" type="button" class="chip" :aria-pressed="kinds.has(kind)" @click="toggleKind(kind)">
					{{ label }} <small>{{ stats.kind[kind] ?? 0 }}</small>
				</button>
			</div>
			<div class="tx-chips" role="radiogroup" aria-label="Origin">
				<button v-for="o in (['all', 'atlas', 'roadmap'] as const)" :key="o" type="button" class="chip" role="radio" :aria-checked="origin === o" :aria-pressed="origin === o" @click="origin = o">
					{{ o === 'all' ? 'Any origin' : o === 'atlas' ? 'In the atlases' : 'Roadmap only' }}
				</button>
			</div>
			<p class="tx-count">{{ filtered.length }} of {{ stats.total }} shown</p>
		</div>

		<section v-for="group in grouped" :key="group.family" class="tx-family" :style="{ '--hue': FAMILY[group.family].hue }">
			<h2 :id="group.family" tabindex="-1">{{ FAMILY[group.family].label }} <small>{{ group.count }} · {{ FAMILY[group.family].blurb }}</small></h2>
			<div v-for="c in group.classes" :key="c.name" class="tx-class">
				<h3>{{ pretty(c.name) }}</h3>
				<div class="tx-grid">
					<article v-for="m in c.items" :key="m.id" class="tx-card">
						<elemental-surface v-if="live.has(m.id)" class="tx-swatch" :material.attr="m.id" :packs.attr="withBase('/live/packs')" light="pointer" tile="128" :tier.attr="live_tier" />
						<div v-else class="tx-swatch tx-placeholder" aria-hidden="true" />
						<div class="tx-body">
							<div class="tx-name">{{ m.display_name }}</div>
							<code class="tx-id">{{ m.id }}</code>
							<div class="tx-tags">
								<span class="tag" :data-kind="m.kind">{{ KIND[m.kind] }}</span>
								<span v-if="m.atlas_code" class="tag tag-atlas">{{ m.atlas_code }}</span>
								<span v-else class="tag tag-roadmap">roadmap</span>
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
.tx { margin-top: 24px; }
.tx-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-bottom: 24px; }
.tx-stat { border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 12px 14px; background: var(--vp-c-bg-soft); }
.tx-stat b { display: block; font-size: 26px; line-height: 1.1; font-family: var(--vp-font-family-mono); }
.tx-stat span { font-size: 12px; color: var(--vp-c-text-2); }

.tx-tree { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-bottom: 28px; }
.tx-tree-family { border-left: 3px solid var(--hue); padding: 4px 0 4px 12px; }
.tx-tree-head { font-weight: 600; display: flex; align-items: center; gap: 6px; }
.tx-tree-head small, .tx-tree li small { color: var(--vp-c-text-3); font-family: var(--vp-font-family-mono); margin-left: auto; }
.tx-tree ul { list-style: none; padding: 0; margin: 6px 0 0; }
.tx-tree li { display: flex; gap: 8px; font-size: 13px; color: var(--vp-c-text-2); text-transform: capitalize; margin: 2px 0; }
.dot { width: 9px; height: 9px; border-radius: 50%; background: var(--hue); display: inline-block; }

.tx-controls { position: sticky; top: calc(var(--vp-nav-height) + 4px); z-index: 5; background: var(--vp-c-bg); padding: 10px 0; border-bottom: 1px solid var(--vp-c-divider); margin-bottom: 8px; }
.tx-search { width: 100%; padding: 9px 12px; border: 1px solid var(--vp-c-divider); border-radius: 10px; background: var(--vp-c-bg-soft); font-size: 14px; }
.tx-search:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 1px; }
.tx-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.chip { border: 1px solid var(--vp-c-divider); border-radius: 999px; padding: 3px 11px; font-size: 12.5px; color: var(--vp-c-text-2); background: transparent; cursor: pointer; }
.chip small { color: var(--vp-c-text-3); }
.chip[aria-pressed="true"] { background: var(--hue, var(--vp-c-brand-1)); border-color: var(--hue, var(--vp-c-brand-1)); color: #fff; }
.chip[aria-pressed="true"] small { color: rgb(255 255 255 / 0.8); }
.chip:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 2px; }
.tx-count { font-size: 12px; color: var(--vp-c-text-3); margin: 8px 0 0; }

.tx-family h2 { border-top: none; margin-top: 36px; padding-top: 0; display: flex; align-items: baseline; gap: 10px; }
.tx-family h2::before { content: ""; width: 12px; height: 12px; border-radius: 3px; background: var(--hue); align-self: center; }
.tx-family h2 small { font-size: 13px; font-weight: 400; color: var(--vp-c-text-2); }
.tx-class h3 { text-transform: capitalize; font-size: 15px; color: var(--vp-c-text-2); margin: 18px 0 10px; }
.tx-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.tx-card { border: 1px solid var(--vp-c-divider); border-radius: 14px; overflow: hidden; background: var(--vp-c-bg-soft); display: flex; flex-direction: column; }
.tx-swatch { display: block; height: 92px; }
.tx-placeholder {
	background:
		radial-gradient(circle at 30% 30%, rgb(255 255 255 / 0.18), transparent 55%),
		repeating-linear-gradient(135deg, rgb(0 0 0 / 0.06) 0 6px, transparent 6px 12px),
		var(--hue);
}
.tx-body { padding: 10px 12px 12px; }
.tx-name { font-weight: 600; }
.tx-id { font-size: 11px; color: var(--vp-c-text-2); word-break: break-all; background: none; padding: 0; }
.tx-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
.tag { font-size: 10.5px; border-radius: 6px; padding: 1px 6px; border: 1px solid var(--vp-c-divider); color: var(--vp-c-text-2); font-family: var(--vp-font-family-mono); }
.tag[data-kind="bounded-object"] { border-color: #c9a227; color: #9a7a10; }
.tag[data-kind="animated-surface"] { border-color: #3f8fb0; color: #2f7898; }
.tag[data-kind="volumetric-effect"] { border-color: #8a7fc0; color: #6f62a8; }
.tag-roadmap { border-style: dashed; }
.tag-recipe { border-color: var(--vp-c-green-2); color: var(--vp-c-green-1); }
.tag-live { background: var(--vp-c-brand-soft); border-color: var(--vp-c-brand-1); color: var(--vp-c-brand-1); }
.tx-empty { color: var(--vp-c-text-2); }
</style>
