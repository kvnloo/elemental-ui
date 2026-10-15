// elemental-pack/1 manifest types and loading. Mirrors crates/elemental-pack.
// GPL-3.0-only.

export const PACK_SCHEMA = "elemental-pack/1";

export interface MapVariant {
	file: string;
	mime: string;
	sha256: string;
	bytes: number;
}

export interface MapEntry {
	file: string;
	mime: string;
	width: number;
	height: number;
	bit_depth: number;
	color_space: "srgb" | "linear";
	sha256: string;
	bytes: number;
	variants: MapVariant[];
}

export interface PackManifest {
	schema: typeof PACK_SCHEMA;
	id: string;
	display_name: string;
	family: string;
	class: string | null;
	kind: string;
	license: string;
	status: string;
	physical_tile_mm: number;
	height_mm: number;
	normal_convention: "opengl-y-up";
	tiling: "repeat";
	maps: Record<"basecolor" | "normal" | "roughness" | "height", MapEntry>;
}

export interface Pack {
	manifest: PackManifest;
	/** Absolute URL of the pack directory, with a trailing slash. */
	base: string;
	url(file: string): string;
}

const cache = new Map<string, Promise<Pack>>();

/** Fetch `${packsUrl}/${id}/pack.json`; concurrent callers share one request. */
export function loadPack(packsUrl: string, id: string): Promise<Pack> {
	const base = new URL(`${id}/`, new URL(packsUrl.endsWith("/") ? packsUrl : `${packsUrl}/`, document.baseURI)).href;
	let pending = cache.get(base);
	if (!pending) {
		pending = fetch(`${base}pack.json`)
			.then((response) => {
				if (!response.ok) throw new Error(`${base}pack.json: HTTP ${response.status}`);
				return response.json() as Promise<PackManifest>;
			})
			.then((manifest) => {
				if (manifest.schema !== PACK_SCHEMA) throw new Error(`${id}: schema ${manifest.schema} is not ${PACK_SCHEMA}`);
				return { manifest, base, url: (file: string) => new URL(file, base).href };
			});
		cache.set(base, pending);
		pending.catch(() => cache.delete(base));
	}
	return pending;
}

/** CSS `background-image` for the base color: AVIF/PNG `image-set()` where supported, else plain PNG. */
export function cssBackground(pack: Pack): string {
	const map = pack.manifest.maps.basecolor;
	const options = [...map.variants, map].map((v) => `url("${pack.url(v.file)}") type("${v.mime}")`);
	const preferred = `image-set(${options.join(", ")})`;
	return CSS.supports("background-image", preferred) ? preferred : `url("${pack.url(map.file)}")`;
}

export async function fetchBitmap(pack: Pack, name: keyof PackManifest["maps"]): Promise<ImageBitmap> {
	const response = await fetch(pack.url(pack.manifest.maps[name].file));
	if (!response.ok) throw new Error(`${name}: HTTP ${response.status}`);
	return createImageBitmap(await response.blob(), { colorSpaceConversion: "none", premultiplyAlpha: "none" });
}
