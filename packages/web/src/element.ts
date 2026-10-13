// <elemental-surface>: a material-backed surface with real HTML on top.
//
//   <elemental-surface material="geo.basalt.vesicular.v1" packs="/packs">
//     <button>Explore</button>
//   </elemental-surface>
//
// Tiers, chosen per element (attribute `tier`, default "auto"):
//   css     the base color tiles as a CSS background. No GPU work; first paint.
//   webgl2  relit by the shared shader, compiled from naga-generated GLSL.
//   webgpu  relit by the shared WGSL directly.
// The CSS layer always paints first and stays underneath, so a GPU tier that
// fails or loads late never leaves a blank box. GPU tiers draw on demand
// (pointer, resize, attribute change), never in a free-running loop, and stop
// while the element is off screen.
// GPL-3.0-only.
import { cssBackground, loadPack, type Pack } from "./pack.js";
import { lightToward, REFERENCE, type SurfaceParams, type SurfaceRenderer } from "./params.js";
import { createWebGL2Renderer } from "./webgl2.js";
import { createWebGPURenderer } from "./webgpu.js";

export type Tier = "css" | "webgl2" | "webgpu";

const STYLE = `
:host { display: block; position: relative; isolation: isolate; contain: paint; }
[part=base] { position: absolute; inset: 0; z-index: -2; background-color: #2a2725; background-repeat: repeat; }
canvas { position: absolute; inset: 0; width: 100%; height: 100%; z-index: -1; display: block; pointer-events: none; opacity: 0; transition: opacity 120ms linear; }
canvas.on { opacity: 1; }
@media (prefers-reduced-motion: reduce) { canvas { transition: none; } }
`;

const reducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

export interface ReadyDetail {
	tier: Tier;
	material: string;
	/** Milliseconds from connection to the first frame of this tier. */
	ms: number;
}

export class ElementalSurface extends HTMLElement {
	static observedAttributes = ["material", "packs", "tier", "light", "tile", "relief", "exposure"];

	#base = document.createElement("div");
	#canvas = document.createElement("canvas");
	#renderer: SurfaceRenderer | null = null;
	#pack: Pack | null = null;
	#generation = 0;
	#frame = 0;
	#pointer: [number, number] | null = null;
	#visible = true;
	#resize = new ResizeObserver(() => this.#schedule());
	#intersection = new IntersectionObserver((entries) => {
		this.#visible = entries.some((e) => e.isIntersecting);
		if (this.#visible) this.#schedule();
	});

	/** The tier currently painting. */
	tier: Tier = "css";

	constructor() {
		super();
		const root = this.attachShadow({ mode: "open" });
		const style = document.createElement("style");
		style.textContent = STYLE;
		this.#canvas.setAttribute("part", "canvas");
		this.#canvas.setAttribute("aria-hidden", "true");
		this.#base.setAttribute("part", "base");
		root.append(style, this.#base, this.#canvas, document.createElement("slot"));
		this.addEventListener("pointermove", (e) => {
			if (this.getAttribute("light") !== "pointer" || reducedMotion()) return;
			const box = this.getBoundingClientRect();
			this.#pointer = [e.clientX - box.left, e.clientY - box.top];
			this.#schedule();
		});
		this.addEventListener("pointerleave", () => {
			this.#pointer = null;
			this.#schedule();
		});
	}

	connectedCallback() {
		this.#resize.observe(this);
		this.#intersection.observe(this);
		void this.#load();
	}

	disconnectedCallback() {
		this.#resize.disconnect();
		this.#intersection.disconnect();
		cancelAnimationFrame(this.#frame);
		this.#renderer?.destroy();
		this.#renderer = null;
		this.#generation++;
	}

	attributeChangedCallback(name: string, previous: string | null, next: string | null) {
		if (previous === next || !this.isConnected) return;
		if (name === "material" || name === "packs" || name === "tier") void this.#load();
		else this.#schedule();
	}

	/** Current shader parameters, in physical pixels. */
	params(): SurfaceParams {
		const dpr = Math.min(devicePixelRatio || 1, 2);
		const width = Math.max(1, Math.round(this.clientWidth * dpr));
		const height = Math.max(1, Math.round(this.clientHeight * dpr));
		const tile = Number(this.getAttribute("tile") ?? REFERENCE.tilePx);
		const light = this.#pointer
			? lightToward(this.#pointer[0] * dpr, this.#pointer[1] * dpr, width, height)
			: REFERENCE.light;
		return {
			...REFERENCE,
			width,
			height,
			tilePx: tile * dpr,
			relief: Number(this.getAttribute("relief") ?? REFERENCE.relief),
			exposure: Number(this.getAttribute("exposure") ?? REFERENCE.exposure),
			light,
		};
	}

	async #load() {
		const generation = ++this.#generation;
		const started = performance.now();
		const material = this.getAttribute("material");
		if (!material) return;
		this.#renderer?.destroy();
		this.#renderer = null;
		this.#canvas.classList.remove("on");
		// A canvas keeps the context type it was first given; swap in a fresh one.
		const canvas = document.createElement("canvas");
		canvas.setAttribute("part", "canvas");
		canvas.setAttribute("aria-hidden", "true");
		this.#canvas.replaceWith(canvas);
		this.#canvas = canvas;

		try {
			this.#pack = await loadPack(this.getAttribute("packs") ?? "/packs", material);
		} catch (error) {
			this.dispatchEvent(new CustomEvent("elemental-error", { detail: { material, error } }));
			return;
		}
		if (generation !== this.#generation) return;
		const tile = Number(this.getAttribute("tile") ?? REFERENCE.tilePx);
		this.#base.style.backgroundImage = cssBackground(this.#pack);
		this.#base.style.backgroundSize = `${tile}px ${tile}px`;
		this.#setTier("css", material, started);

		const wanted = (this.getAttribute("tier") ?? "auto") as Tier | "auto";
		if (wanted === "css" || (navigator as { connection?: { saveData?: boolean } }).connection?.saveData) return;
		const order: ("webgpu" | "webgl2")[] = wanted === "webgl2" ? ["webgl2"] : wanted === "webgpu" ? ["webgpu"] : ["webgpu", "webgl2"];
		for (const tier of order) {
			try {
				const renderer = tier === "webgpu"
					? await createWebGPURenderer(this.#canvas, this.#pack)
					: await createWebGL2Renderer(this.#canvas, this.#pack);
				if (generation !== this.#generation) {
					renderer?.destroy();
					return;
				}
				if (!renderer) continue;
				this.#renderer = renderer;
				this.#draw();
				this.#canvas.classList.add("on");
				this.#setTier(tier, material, started);
				return;
			} catch (error) {
				console.warn(`elemental-surface: ${tier} failed`, error);
			}
		}
	}

	#setTier(tier: Tier, material: string, started: number) {
		this.tier = tier;
		this.dataset.tier = tier;
		this.dispatchEvent(new CustomEvent<ReadyDetail>("elemental-ready", { detail: { tier, material, ms: performance.now() - started } }));
	}

	#schedule() {
		if (!this.#renderer || !this.#visible || this.#frame) return;
		this.#frame = requestAnimationFrame(() => {
			this.#frame = 0;
			this.#draw();
		});
	}

	#draw() {
		if (!this.#renderer) return;
		const params = this.params();
		if (this.#canvas.width !== params.width || this.#canvas.height !== params.height) {
			this.#canvas.width = params.width;
			this.#canvas.height = params.height;
		}
		this.#renderer.render(params);
	}
}

if (!customElements.get("elemental-surface")) customElements.define("elemental-surface", ElementalSurface);
