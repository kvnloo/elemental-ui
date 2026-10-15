// Bundle the web runtime. WGSL is inlined as text so the shader the browser
// compiles is byte-for-byte the file the native renderer includes.
// GPL-3.0-only.
import { build } from "esbuild";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

await build({
	entryPoints: [resolve(here, "../src/index.ts")],
	outfile: resolve(here, "../dist/elemental-ui.js"),
	bundle: true,
	format: "esm",
	target: "es2022",
	minify: true,
	sourcemap: true,
	loader: { ".wgsl": "text" },
	legalComments: "eof",
	metafile: true,
}).then((result) => {
	const out = Object.entries(result.metafile.outputs).find(([file]) => file.endsWith(".js"));
	console.log(`dist/elemental-ui.js ${out[1].bytes} bytes`);
});
