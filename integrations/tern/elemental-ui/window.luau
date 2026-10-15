--!strict
-- elemental-ui for Tern (window half). GPL-3.0-only.
--
-- `elemental.css` (manifest styles) paints the default material. Each palette
-- command here swaps in another installed material by replacing one tern.css
-- sheet; `materials.luau` and `textures/` are written by
-- `python3 tools/elemental.py tern`.
local materials = require("./materials")

local function sheet(id: string): string
	return materials.css(id)
end

for _, m in materials.list do
	tern.command({
		id = "material-" .. m.slug,
		title = "Elemental: " .. m.name,
		run = function(_cx)
			tern.css("material", sheet(m.id))
		end,
	})
end

tern.command({
	id = "material-off",
	title = "Elemental: plain chrome",
	run = function(_cx)
		tern.css("material", materials.off)
	end,
})
