// GPL-3.0-only.
import DefaultTheme from "vitepress/theme";
import type { Theme } from "vitepress";
import "@fontsource-variable/newsreader";
import ElementalHome from "./components/ElementalHome.vue";
import TaxonomyExplorer from "./components/TaxonomyExplorer.vue";
import "./custom.css";

export default {
	extends: DefaultTheme,
	enhanceApp({ app }) {
		app.component("ElementalHome", ElementalHome);
		app.component("TaxonomyExplorer", TaxonomyExplorer);
	},
} satisfies Theme;
