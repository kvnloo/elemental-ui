// WebGPU tier: compiles shaders/elemental_surface.wgsl unchanged.
// GPL-3.0-only.
import wgsl from "../../../shaders/elemental_surface.wgsl";
import { fetchBitmap, type Pack } from "./pack.js";
import { PARAMS_BYTES, packParams, type SurfaceParams, type SurfaceRenderer } from "./params.js";

let shared: Promise<{ device: GPUDevice; module: GPUShaderModule } | null> | undefined;

/** One device and shader module for every element on the page; null if WebGPU is unavailable. */
export function webgpuDevice() {
	shared ??= (async () => {
		if (!("gpu" in navigator)) return null;
		const adapter = await navigator.gpu.requestAdapter({ powerPreference: "low-power" });
		if (!adapter) return null;
		const device = await adapter.requestDevice();
		const module = device.createShaderModule({ label: "elemental_surface.wgsl", code: wgsl });
		const info = await module.getCompilationInfo();
		if (info.messages.some((m) => m.type === "error")) {
			throw new Error(`WGSL: ${info.messages.map((m) => m.message).join("; ")}`);
		}
		device.lost.then(() => {
			shared = undefined;
		});
		return { device, module };
	})().catch(() => null);
	return shared;
}

/**
 * Upload a map's bytes unchanged. Copying into an -srgb texture makes the
 * browser re-encode the image, which then gets decoded a second time when
 * sampled; copy into rgba8unorm and decode through an -srgb view instead.
 */
async function texture(device: GPUDevice, pack: Pack, name: "basecolor" | "normal" | "roughness", srgb: boolean) {
	const bitmap = await fetchBitmap(pack, name);
	const tex = device.createTexture({
		label: name,
		size: [bitmap.width, bitmap.height],
		format: "rgba8unorm",
		viewFormats: srgb ? ["rgba8unorm-srgb"] : [],
		usage: GPUTextureUsage.TEXTURE_BINDING | GPUTextureUsage.COPY_DST | GPUTextureUsage.RENDER_ATTACHMENT,
	});
	device.queue.copyExternalImageToTexture({ source: bitmap }, { texture: tex }, [bitmap.width, bitmap.height]);
	bitmap.close();
	return { tex, view: tex.createView(srgb ? { format: "rgba8unorm-srgb" } : {}) };
}

interface Material {
	device: GPUDevice;
	draw(encoder: GPUCommandEncoder, target: GPUTextureView, params: SurfaceParams): void;
	destroy(): void;
}

/** Upload a pack and build a pipeline that draws it into `format` targets. */
async function prepare(pack: Pack, format: GPUTextureFormat): Promise<Material | null> {
	const gpu = await webgpuDevice();
	if (!gpu) return null;
	const { device, module } = gpu;
	const [basecolor, normal, roughness] = await Promise.all([
		texture(device, pack, "basecolor", true),
		texture(device, pack, "normal", false),
		texture(device, pack, "roughness", false),
	]);
	const uniforms = device.createBuffer({ size: PARAMS_BYTES, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
	const pipeline = device.createRenderPipeline({
		label: "elemental surface",
		layout: "auto",
		vertex: { module, entryPoint: "vs_main" },
		fragment: { module, entryPoint: "fs_main", targets: [{ format }] },
	});
	const sampler = device.createSampler({ addressModeU: "repeat", addressModeV: "repeat", magFilter: "linear", minFilter: "linear" });
	const bindGroup = device.createBindGroup({
		layout: pipeline.getBindGroupLayout(0),
		entries: [
			{ binding: 0, resource: { buffer: uniforms } },
			{ binding: 1, resource: sampler },
			{ binding: 2, resource: basecolor.view },
			{ binding: 3, resource: normal.view },
			{ binding: 4, resource: roughness.view },
		],
	});
	const scratch = new Float32Array(16);
	return {
		device,
		draw(encoder, target, params) {
			device.queue.writeBuffer(uniforms, 0, packParams(params, scratch));
			const pass = encoder.beginRenderPass({
				colorAttachments: [{ view: target, loadOp: "clear", storeOp: "store", clearValue: [0, 0, 0, 1] }],
			});
			pass.setPipeline(pipeline);
			pass.setBindGroup(0, bindGroup);
			pass.draw(3);
			pass.end();
		},
		destroy() {
			for (const t of [basecolor, normal, roughness]) t.tex.destroy();
			uniforms.destroy();
		},
	};
}

export async function createWebGPURenderer(canvas: HTMLCanvasElement, pack: Pack): Promise<SurfaceRenderer | null> {
	const context = canvas.getContext("webgpu");
	if (!context) return null;
	// Non-sRGB target: the shader writes sRGB-encoded values itself, like native.
	const format = navigator.gpu.getPreferredCanvasFormat();
	const material = await prepare(pack, format);
	if (!material) return null;
	context.configure({ device: material.device, format, alphaMode: "opaque" });
	return {
		tier: "webgpu",
		render(params: SurfaceParams) {
			const encoder = material.device.createCommandEncoder();
			material.draw(encoder, context.getCurrentTexture().createView(), params);
			material.device.queue.submit([encoder.finish()]);
		},
		destroy() {
			context.unconfigure();
			material.destroy();
		},
	};
}

/**
 * Render a pack to RGBA8 pixels without a canvas (sRGB-encoded, row-major).
 * Useful for baking lit stills and for verifying the WebGPU path where a
 * canvas cannot present (headless browsers). Null if WebGPU is unavailable.
 */
export async function renderPixelsWebGPU(pack: Pack, params: SurfaceParams): Promise<Uint8Array | null> {
	const material = await prepare(pack, "rgba8unorm");
	if (!material) return null;
	const { device } = material;
	const { width, height } = params;
	const target = device.createTexture({
		size: [width, height],
		format: "rgba8unorm",
		usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.COPY_SRC,
	});
	const stride = Math.ceil((width * 4) / 256) * 256;
	const buffer = device.createBuffer({ size: stride * height, usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ });
	const encoder = device.createCommandEncoder();
	material.draw(encoder, target.createView(), params);
	encoder.copyTextureToBuffer({ texture: target }, { buffer, bytesPerRow: stride }, [width, height]);
	device.queue.submit([encoder.finish()]);
	await buffer.mapAsync(GPUMapMode.READ);
	const mapped = new Uint8Array(buffer.getMappedRange());
	const pixels = new Uint8Array(width * height * 4);
	for (let y = 0; y < height; y++) pixels.set(mapped.subarray(y * stride, y * stride + width * 4), y * width * 4);
	buffer.unmap();
	buffer.destroy();
	target.destroy();
	material.destroy();
	return pixels;
}
