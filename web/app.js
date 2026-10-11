// elemental-ui experimental showroom. GPL-3.0-only. All controls use real HTML.
const FALLBACK = [
  { id: "geo.basalt.vesicular.v1", display_name: "Vesicular Basalt", status: "prototype" },
  { id: "geo.slate.layered.v1", display_name: "Layered Slate", status: "prototype" },
  { id: "geo.limestone.porous.v1", display_name: "Porous Limestone", status: "prototype" }
];

const byId = (id) => document.getElementById(id);
const grid = byId("material-grid");
const search = byId("material-search");
const stage = byId("lab-stage");
const choices = Array.from(document.querySelectorAll("#material-switch button"));
const explore = byId("explore-button");
const depth = byId("depth-slider");
const output = byId("depth-output");
let catalog = FALLBACK;
let current = FALLBACK[0].id;
let generated = false;

function safeId(value) {
  return typeof value === "string" && /^(geo|bot|aq|fauna|atm)\.[a-z0-9.-]+\.v[1-9][0-9]*$/.test(value);
}

function setMaterial(id) {
  if (!safeId(id)) return;
  const item = catalog.find((entry) => entry.id === id) || FALLBACK.find((entry) => entry.id === id);
  if (!item) return;
  current = item.id;
  byId("current-material").textContent = item.display_name;
  byId("current-id").textContent = id;
  explore.dataset.material = id;
  explore.style.setProperty("--el-texture", generated ? 'url("./assets/' + id + '/basecolor.png")' : "none");
  choices.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.id === id)));
  Array.from(grid.children).forEach((card) => card.setAttribute("aria-pressed", String(card.dataset.id === id)));
  byId("interaction-status").textContent = "Selected " + item.display_name + ".";
}

function createCard(item) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "el-card";
  button.dataset.id = item.id;
  button.setAttribute("aria-pressed", String(item.id === current));
  button.setAttribute("aria-label", "Select " + item.display_name);
  const surface = document.createElement("div");
  surface.className = "swatch no-image";
  surface.dataset.material = item.id;
  if (generated && safeId(item.id)) {
    const img = document.createElement("img");
    img.loading = "lazy";
    img.alt = "";
    img.src = "./assets/" + item.id + "/preview.png";
    img.addEventListener("load", () => surface.classList.remove("no-image"));
    img.addEventListener("error", () => img.remove());
    surface.append(img);
  }
  const meta = document.createElement("div");
  meta.className = "card-content";
  const name = document.createElement("span");
  name.className = "serif";
  name.textContent = item.display_name;
  const badge = document.createElement("small");
  badge.className = "prototype";
  badge.textContent = item.status;
  meta.append(name, badge);
  button.append(surface, meta);
  button.addEventListener("click", () => setMaterial(item.id));
  return button;
}

function renderGrid() {
  const phrase = search.value.trim().toLowerCase();
  const visible = catalog.filter((item) => (item.display_name + " " + item.id).toLowerCase().includes(phrase));
  grid.replaceChildren(...visible.map(createCard));
  byId("material-count").textContent = String(visible.length);
  if (!visible.length) {
    const empty = document.createElement("p");
    empty.textContent = "No materials match this search.";
    grid.append(empty);
  }
}

choices.forEach((button) => button.addEventListener("click", () => setMaterial(button.dataset.id)));
search.addEventListener("input", renderGrid);
explore.addEventListener("click", () => {
  byId("interaction-status").textContent = "Explore activated with " + byId("current-material").textContent + ".";
});
depth.addEventListener("input", () => {
  const value = Number(depth.value);
  output.value = String(value);
  explore.style.setProperty("--el-shadow", "0 " + (1 + value / 8) + "px " + (4 + value / 4) + "px rgba(0,0,0,.36)");
});

async function loadCatalog() {
  try {
    const response = await fetch("./assets/catalog.json", { cache: "no-cache" });
    if (!response.ok) throw new Error("Textures not generated");
    const data = await response.json();
    if (!Array.isArray(data) || !data.length || !data.every((item) => safeId(item.id) && typeof item.display_name === "string")) {
      throw new Error("Invalid catalog");
    }
    catalog = data;
    generated = true;
    byId("asset-status").textContent = "Generated local texture maps loaded. Physical calibration is still pending.";
  } catch {
    byId("asset-status").textContent = "Showing CSS placeholders. Run the generator to load actual maps.";
  }
  renderGrid();
  setMaterial(catalog[0].id);
}

loadCatalog();
