// Copy built packs and the web runtime into docs/public/live so the docs can
// show live <elemental-surface> swatches. Optional: without them the pages
// build normally and the swatches stay placeholders. GPL-3.0-only.
import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const out = join(root, "docs/public/live");
const packs = join(root, "packs");
const bundle = join(root, "packages/web/dist/elemental-ui.js");

rmSync(out, { recursive: true, force: true });
if (!existsSync(join(packs, "index.json")) || !existsSync(bundle)) {
	console.log("docs: no packs/ or web bundle; live swatches disabled (run `python3 tools/elemental.py pack` and `npm run build`)");
	process.exit(0);
}
mkdirSync(out, { recursive: true });
cpSync(packs, join(out, "packs"), { recursive: true });
cpSync(bundle, join(out, "elemental-ui.js"));
console.log(`docs: copied packs and elemental-ui.js into ${out}`);
