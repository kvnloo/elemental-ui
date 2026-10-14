import { defineConfig } from "vitepress";

// elemental-ui documentation. GPL-3.0-only.
const repo = "https://github.com/kvnloo/elemental-ui";

export default defineConfig({
	title: "elemental-ui",
	description: "Earth-sourced material packs, one shared shader, and thin drivers for web, desktop and Tern.",
	cleanUrls: true,
	lastUpdated: true,
	// Generated build output and the runtime copy live outside the page tree.
	srcExclude: ["public/live/**"],
	head: [
		["meta", { name: "theme-color", content: "#2a2622" }],
		["link", { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" }],
	],
	markdown: { theme: { light: "github-light", dark: "github-dark" } },
	vue: { template: { compilerOptions: { isCustomElement: (tag) => tag === "elemental-surface" } } },
	themeConfig: {
		logo: { light: "/mark.svg", dark: "/mark.svg", alt: "" },
		nav: [
			{ text: "Guide", link: "/guide/getting-started" },
			{ text: "Taxonomy", link: "/taxonomy/" },
			{ text: "Pipeline", link: "/pipeline/" },
			{ text: "Runtime", link: "/runtime/" },
			{ text: "Reference", link: "/reference/cli" },
			{ text: "Project", link: "/ROADMAP" },
		],
		sidebar: [
			{
				text: "Guide",
				items: [
					{ text: "Getting started", link: "/guide/getting-started" },
					{ text: "Ethos", link: "/guide/ethos" },
					{ text: "Repository tour", link: "/guide/repository" },
				],
			},
			{
				text: "Taxonomy",
				items: [
					{ text: "Explorer", link: "/taxonomy/" },
					{ text: "Taxonomy format", link: "/taxonomy/format" },
				],
			},
			{
				text: "Asset pipeline",
				items: [
					{ text: "Overview", link: "/pipeline/" },
					{ text: "Material recipes", link: "/pipeline/recipes" },
					{ text: "Packs (elemental-pack/1)", link: "/pipeline/packs" },
					{ text: "Image generation", link: "/pipeline/image-generation" },
					{ text: "Blender PBR smoke", link: "/PBR_BLENDER" },
					{ text: "Reference scans", link: "/REFERENCES" },
				],
			},
			{
				text: "Runtime",
				items: [
					{ text: "Overview", link: "/runtime/" },
					{ text: "Architecture & verification", link: "/RUNTIME" },
					{ text: "Surface shader", link: "/runtime/shader" },
					{ text: "Web component", link: "/runtime/web" },
					{ text: "Native: Rust crates", link: "/runtime/native" },
					{ text: "Hyprland wallpapers", link: "/runtime/hyprland" },
					{ text: "Tern plugin", link: "/runtime/tern" },
					{ text: "CSS components (gallery)", link: "/COMPONENTS" },
				],
			},
			{
				text: "Reference",
				items: [
					{ text: "Command line", link: "/reference/cli" },
					{ text: "Testing & CI", link: "/reference/testing" },
					{ text: "Browser QA (gallery)", link: "/QA_BROWSER" },
				],
			},
			{
				text: "Project",
				items: [
					{ text: "Roadmap", link: "/ROADMAP" },
					{ text: "Architecture (v0.1)", link: "/ARCHITECTURE" },
					{ text: "Runtime research", link: "/RUNTIME_RESEARCH" },
					{ text: "License & provenance", link: "/PROVENANCE" },
					{ text: "Contributing", link: "/project/contributing" },
				],
			},
		],
		socialLinks: [{ icon: "github", link: repo }],
		editLink: { pattern: `${repo}/edit/main/docs/:path`, text: "Edit this page" },
		search: { provider: "local" },
		outline: { level: [2, 3] },
		footer: { message: "GPL-3.0-only. Generated imagery is not measured PBR data.", copyright: "© 2026 Kevin Rajan and contributors" },
	},
});
