// Surface parameters shared by the WebGPU and WebGL2 renderers. The layout is
// `struct Params` in shaders/elemental_surface.wgsl (64 bytes, std140-safe),
// and REFERENCE matches `SurfaceParams::reference` in crates/elemental-render.
// GPL-3.0-only.

export interface SurfaceParams {
	/** Target size in physical pixels. */
	width: number;
	height: number;
	/** One material tile, in physical pixels. */
	tilePx: number;
	relief: number;
	/** Direction toward the light: x right, y up, z toward the viewer. */
	light: [number, number, number];
	intensity: number;
	lightColor: [number, number, number];
	ambient: number;
	/** Texture offset in tiles. */
	offset: [number, number];
	exposure: number;
}

export const REFERENCE: Omit<SurfaceParams, "width" | "height"> = {
	tilePx: 256,
	relief: 1,
	light: [-0.45, 0.55, 0.7],
	intensity: 3.2,
	lightColor: [1, 0.97, 0.92],
	ambient: 0.22,
	offset: [0, 0],
	exposure: 1,
};

export const PARAMS_BYTES = 64;

export function packParams(p: SurfaceParams, out = new Float32Array(16)): Float32Array {
	out.set([p.width, p.height, p.tilePx, p.relief], 0);
	out.set([...p.light, p.intensity], 4);
	out.set([...p.lightColor, p.ambient], 8);
	out.set([...p.offset, p.exposure, 0], 12);
	return out;
}

/** A light that follows a point inside the surface, as a normalized direction. */
export function lightToward(x: number, y: number, width: number, height: number, elevation = 0.7): [number, number, number] {
	const dx = (x / width) * 2 - 1;
	const dy = 1 - (y / height) * 2;
	const length = Math.hypot(dx, dy, elevation);
	return [dx / length, dy / length, elevation / length];
}

export interface SurfaceRenderer {
	readonly tier: "webgpu" | "webgl2";
	render(params: SurfaceParams): void;
	destroy(): void;
}
