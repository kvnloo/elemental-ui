// Build-time loader: catalog/taxonomy.json plus what exists for each material today.
// GPL-3.0-only.
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

const root = resolve(__dirname, "..");

export interface CatalogMaterial {
	id: string;
	display_name: string;
	family: string;
	class: string;
	kind: string;
	atlas_code: string | null;
	origin: string;
	/** A recipe exists under materials/. */
	recipe: boolean;
	/** Recipe status, when there is one. */
	status: string | null;
	/** Site path of the AI visual target, when one has been generated. */
	image: string | null;
	prompt: string | null;
}

export interface Catalog {
	version: number;
	status: string;
	hierarchy: string;
	kinds: string[];
	render_roles: string[];
	materials: CatalogMaterial[];
	visual_targets: { asset_type: string; source: string } | null;
}

declare const data: Catalog;
export { data };

function recipes(dir: string): Map<string, string> {
	const out = new Map<string, string>();
	for (const name of readdirSync(dir)) {
		const path = join(dir, name);
		if (statSync(path).isDirectory()) for (const [k, v] of recipes(path)) out.set(k, v);
		else if (name.endsWith(".json")) {
			const recipe = JSON.parse(readFileSync(path, "utf8"));
			out.set(recipe.id, recipe.status);
		}
	}
	return out;
}

export default {
	watch: ["../catalog/taxonomy.json", "../materials/**/*.json", "./public/materials/index.json"],
	load(): Catalog {
		const doc = JSON.parse(readFileSync(join(root, "catalog/taxonomy.json"), "utf8"));
		const known = existsSync(join(root, "materials")) ? recipes(join(root, "materials")) : new Map();
		const targetsPath = join(root, "docs/public/materials/index.json");
		const targets = existsSync(targetsPath) ? JSON.parse(readFileSync(targetsPath, "utf8")) : null;
		return {
			...doc,
			visual_targets: targets && { asset_type: targets.asset_type, source: targets.source },
			materials: doc.materials.map((m: CatalogMaterial) => {
				const target = targets?.images[m.id];
				return {
					...m,
					recipe: known.has(m.id),
					status: known.get(m.id) ?? null,
					image: target ? `/materials/${target.file}` : null,
					prompt: target?.prompt ?? null,
				};
			}),
		};
	},
};
