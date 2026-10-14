// Turn AI visual targets (PNG originals kept outside Git, see VISUAL_TARGETS below)
// into small WebP derivatives for the docs, plus an index with provenance.
// Usage: node docs/.vitepress/visual-targets.mjs [SOURCE_DIR]   GPL-3.0-only.
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const VISUAL_TARGETS = process.argv[2] ?? "/mnt/zer0models/project-artifacts/elemental-ui/visual-targets-2026-10-14";
const out = join(root, "docs/public/materials");
const source = JSON.parse(readFileSync(join(VISUAL_TARGETS, "manifest.json"), "utf8"));
mkdirSync(out, { recursive: true });

const index = { asset_type: source.asset_type, source: source.source, images: {} };
for (const [id, entry] of Object.entries(source.images)) {
	const file = `${id}.webp`;
	// 1024 px wide WebP: sharp on cards and the hero, ~100-250 KB each.
	execFileSync("python3", ["-c", `
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
w = 1024
im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(sys.argv[2], "WEBP", quality=82, method=6)
`, join(VISUAL_TARGETS, entry.file), join(out, file)]);
	const bytes = readFileSync(join(out, file));
	index.images[id] = {
		file,
		sha256: createHash("sha256").update(bytes).digest("hex"),
		bytes: bytes.length,
		original: { width: entry.width, height: entry.height, sha256: entry.sha256 },
		prompt: entry.prompt,
	};
}
writeFileSync(join(out, "index.json"), JSON.stringify(index, null, 2) + "\n");
console.log(`docs: ${Object.keys(index.images).length} visual targets -> ${out}`);
