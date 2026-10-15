// Turn AI visual targets (originals kept outside Git, see VISUAL_TARGETS below)
// into docs images, plus an index with provenance. Nothing is downscaled below
// the original resolution:
//   <id>.webp        the original pixels (1536 px wide), WebP q90
//   <id>.large.avif  3072 px wide from a 4x RealESRGAN_x4plus restoration
//                    (<id>.x4.png), for full-bleed surfaces. Restored detail is
//                    model-inferred, not captured.
// Usage: node docs/.vitepress/visual-targets.mjs [SOURCE_DIR]   GPL-3.0-only.
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const VISUAL_TARGETS = process.argv[2] ?? "/mnt/zer0models/project-artifacts/elemental-ui/visual-targets-2026-10-14";
const out = join(root, "docs/public/materials");
const source = JSON.parse(readFileSync(join(VISUAL_TARGETS, "manifest.json"), "utf8"));
rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });

// Only full-bleed surfaces need the 3072 px restoration; everything else is
// shown at or below its original 1536 px. Keep this list in step with
// ElementalHome.vue.
const FULL_BLEED = new Set([
	"geo.slate.layered.v1", "geo.basalt.vesicular.v1", "geo.granite.speckled.v1", "bot.bark.oak.v1",
	"aq.water.ripple.v1", "fauna.nacre.shell.v1", "atm.ice.sheet.v1",
]);

const CONVERT = `
import sys
from PIL import Image
src, dst, width, fmt, quality = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
im = Image.open(src).convert("RGB")
if width and im.width != width:
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
if fmt == "AVIF":
    im.save(dst, "AVIF", quality=quality, speed=4)
else:
    im.save(dst, "WEBP", quality=quality, method=6)
print(im.width, im.height)
`;
const convert = (src, dst, width, fmt, quality) =>
	execFileSync("python3", ["-c", CONVERT, src, dst, String(width), fmt, String(quality)]).toString().trim().split(" ").map(Number);
const describe = (file) => {
	const bytes = readFileSync(join(out, file));
	return { file, sha256: createHash("sha256").update(bytes).digest("hex"), bytes: bytes.length };
};

const index = {
	asset_type: source.asset_type,
	source: source.source,
	large: "4x RealESRGAN_x4plus restoration of the original, resampled to 3072 px wide; detail beyond the original is model-inferred",
	images: {},
};
for (const [id, entry] of Object.entries(source.images)) {
	const [w, h] = convert(join(VISUAL_TARGETS, entry.file), join(out, `${id}.webp`), 0, "WEBP", 90);
	const record = {
		...describe(`${id}.webp`),
		width: w,
		height: h,
		original: { width: entry.width, height: entry.height, sha256: entry.sha256 },
		prompt: entry.prompt,
	};
	const x4 = join(VISUAL_TARGETS, `${id}.x4.png`);
	if (FULL_BLEED.has(id) && existsSync(x4)) {
		const [lw, lh] = convert(x4, join(out, `${id}.large.avif`), 3072, "AVIF", 72);
		record.large = { ...describe(`${id}.large.avif`), width: lw, height: lh };
	}
	index.images[id] = record;
	console.log(id, `${w}x${h}`, record.large ? `large ${record.large.width}x${record.large.height}` : "");
}
writeFileSync(join(out, "index.json"), JSON.stringify(index, null, 2) + "\n");
console.log(`docs: ${Object.keys(index.images).length} visual targets -> ${out}`);
