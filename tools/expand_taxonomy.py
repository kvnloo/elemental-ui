"""Expand catalog/taxonomy.json from the 56 poster/roadmap entries to a
generation-scale catalog. Existing ids, atlas codes and origins are kept;
classes are refined; new entries get origin "expansion-2026-10-14".
Run once; the JSON stays the source of truth. GPL-3.0-only."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "catalog" / "taxonomy.json"
KIND = {"T": "tileable-surface", "O": "bounded-object", "A": "animated-surface", "V": "volumetric-effect"}
PREFIX = {"geological": "geo", "botanical": "bot", "aquatic": "aq", "atmospheric": "atm", "fauna": "fauna"}

# family -> class -> "slug|Display name|kind". Existing slugs are listed in
# their (possibly new) class so they move; their other fields are kept.
CATALOG = {
 "geological": {
  "volcanic": """basalt.vesicular|Basalt|T; basalt.columnar|Columnar Basalt|T; obsidian.conchoidal|Obsidian|T;
   obsidian.snowflake|Snowflake Obsidian|T; obsidian.mahogany|Mahogany Obsidian|T; pumice.frothy|Pumice|T;
   scoria.red|Red Scoria|T; tuff.volcanic|Volcanic Tuff|T; tuff.welded|Welded Tuff|T; rhyolite.flow-banded|Flow-banded Rhyolite|T;
   andesite.porphyritic|Andesite|T; dacite.grey|Dacite|T; ignimbrite.welded|Ignimbrite|T; lava.pahoehoe|Pahoehoe Lava|T;
   lava.aa|ʻAʻā Lava|T; lava.molten|Molten Lava|A""",
  "plutonic": """granite.speckled|Granite|T; granite.pink|Pink Granite|T; granite.porphyritic|Porphyritic Granite|T;
   larvikite.labradorescent|Larvikite|T; diorite.salt-pepper|Diorite|T; gabbro.dark|Gabbro|T; syenite.feldspar|Syenite|T;
   pegmatite.coarse|Pegmatite|T; peridotite.olivine|Peridotite|T; anorthosite.pale|Anorthosite|T; porphyry.red|Red Porphyry|T""",
  "clastic-sedimentary": """sandstone.granular|Sandstone|T; sandstone.red|Red Sandstone|T; sandstone.cross-bedded|Cross-bedded Sandstone|T;
   sandstone.wave|Wave Sandstone|T; conglomerate.pebbly|Conglomerate|T; breccia.angular|Breccia|T; shale.fissile|Shale|T;
   mudstone.mottled|Mudstone|T; siltstone.laminated|Siltstone|T; greywacke.dark|Greywacke|T; arkose.feldspathic|Arkose|T""",
  "chemical-biogenic-sedimentary": """limestone.porous|Limestone|T; limestone.fossiliferous|Fossiliferous Limestone|T; limestone.oolitic|Oolitic Limestone|T;
   travertine.banded|Travertine|T; chalk.white|Chalk|T; coquina.shell|Coquina|T; dolostone.sugary|Dolostone|T;
   chert.nodular|Chert|T; flint.knapped|Flint|T; tufa.spongy|Tufa|T; coral-stone.coralline|Coral Stone|T;
   halite.rock-salt|Rock Salt|T; onyx.banded-calcite|Banded Onyx|T; stromatolite.layered|Stromatolite|T;
   coal.anthracite|Anthracite|T; jet.lignite|Jet|T""",
  "metamorphic": """slate.layered|Slate|T; slate.green|Green Slate|T; marble.veined|Marble|T; marble.calacatta|Calacatta Marble|T;
   marble.nero-marquina|Nero Marquina Marble|T; marble.verde|Verde Marble|T; quartzite.interlocking|Quartzite|T;
   schist.mica|Mica Schist|T; schist.garnet|Garnet Schist|T; gneiss.banded|Banded Gneiss|T; gneiss.augen|Augen Gneiss|T;
   phyllite.sheen|Phyllite|T; hornfels.dense|Hornfels|T; serpentinite.green|Serpentinite|T; soapstone.talc|Soapstone|T;
   migmatite.swirled|Migmatite|T; amphibolite.dark|Amphibolite|T""",
  "crystalline": """quartz.crystal|Quartz crystal|O; amethyst.geode|Amethyst Geode|O; citrine.cluster|Citrine Cluster|O;
   quartz.smoky|Smoky Quartz|O; quartz.rose|Rose Quartz|T; geode.druzy|Druzy Geode|O; calcite.rhomb|Calcite Rhomb|O;
   selenite.blade|Selenite|O; celestite.geode|Celestite Geode|O; fluorite.cubic|Fluorite|O; pyrite.cubic|Pyrite|O;
   galena.cubic|Galena|O; tourmaline.black|Black Tourmaline|O; mica.book|Muscovite Mica|O; sulfur.crystal|Sulfur|O;
   gypsum.desert-rose|Desert Rose|O; hematite.botryoidal|Botryoidal Hematite|O""",
  "lapidary": """agate.banded|Banded Agate|T; jasper.red|Red Jasper|T; jasper.ocean|Ocean Jasper|T; malachite.banded|Malachite|T;
   azurite.nodular|Azurite|T; lapis.lazuli|Lapis Lazuli|T; turquoise.matrix|Turquoise|T; labradorite.flash|Labradorite|T;
   moonstone.adularescent|Moonstone|T; opal.play-of-color|Opal|T; rhodochrosite.banded|Rhodochrosite|T;
   tigereye.chatoyant|Tiger's Eye|T; jade.nephrite|Nephrite Jade|T; amber.inclusions|Amber|T""",
  "loose-earth": """pebble.river|River Pebble|O; soil.clay|Clay Soil|T; sand.natural|Natural Sand|T; sand.black-volcanic|Black Volcanic Sand|T;
   sand.pink-coral|Pink Coral Sand|T; sand.dune-ripple|Dune Ripples|T; gravel.pea|Pea Gravel|T; gravel.crushed|Crushed Gravel|T;
   scree.talus|Talus Scree|T; cobble.beach|Beach Cobbles|T; soil.loam|Loam|T; soil.peat|Peat|T; soil.laterite|Laterite|T;
   mud.cracked|Cracked Mud|T; salt-flat.polygon|Salt Flat|T; desert.pavement|Desert Pavement|T; ash.volcanic|Volcanic Ash|T""",
  "weathering": """varnish.desert|Desert Varnish|T; rock.honeycomb-weathered|Tafoni Weathering|T; rock.lichen-patina|Lichen Patina|T;
   rock.iron-stained|Iron-stained Rock|T; rock.water-worn|Water-worn Rock|T; rock.frost-shattered|Frost-shattered Rock|T""",
 },
 "botanical": {
  "foliage": """leaf.broad|Broad Leaf|O; frond.fern|Fern Frond|O; leaf.eucalyptus|Eucalyptus Leaf|O; grass.cluster|Grass clusters|O;
   leaf.oak|Oak Leaf|O; leaf.maple|Maple Leaf|O; leaf.ginkgo|Ginkgo Leaf|O; leaf.monstera|Monstera Leaf|O; leaf.banana|Banana Leaf|O;
   leaf.lotus|Lotus Leaf|O; leaf.palm|Palm Frond|O; leaf.holly|Holly Leaf|O; leaf.ivy|Ivy Leaf|O; leaf.lambs-ear|Lamb's Ear Leaf|O;
   leaf.skeleton|Leaf Skeleton|O; litter.autumn|Autumn Leaf Litter|T; litter.pine-needle|Pine Needle Litter|T; lawn.turf|Lawn Turf|T""",
  "succulents-cacti": """cactus.ribbed|Ribbed Cactus|T; succulent.echeveria|Echeveria Rosette|O; aloe.leaf|Aloe Leaf|O; agave.leaf|Agave Leaf|O""",
  "bark": """bark.oak|Oak Bark|T; bark.birch|Birch Bark|T; bark.pine|Pine Bark|T; bark.redwood|Redwood Bark|T; bark.cork-oak|Cork Oak Bark|T;
   bark.plane|Plane Tree Bark|T; bark.rainbow-eucalyptus|Rainbow Eucalyptus Bark|T; bark.cherry|Cherry Bark|T; bark.beech|Beech Bark|T;
   bark.palm-trunk|Palm Trunk|T; bark.paperbark|Paperbark|T; bark.olive|Olive Bark|T; bark.baobab|Baobab Bark|T; bark.cedar|Cedar Bark|T""",
  "bryophytes-lichens": """moss.cushion|Moss Cushion|T; lichen.crust|Lichen Crust|T; moss.sheet|Sheet Moss|T; moss.sphagnum|Sphagnum Moss|T;
   lichen.foliose|Foliose Lichen|T; lichen.beard|Beard Lichen|O; liverwort.thallose|Liverwort|T""",
  "fungi": """fungi.bracket|Bracket Fungus|O; fungi.gills|Mushroom Gills|T; fungi.mycelium|Mycelium Mat|T; fungi.morel|Morel|O;
   fungi.puffball|Puffball|O""",
  "wood-timber": """wood.walnut|Walnut Wood Grain|T; wood.endgrain|Wood endgrain|T; wood.oak-quartersawn|Quartersawn Oak|T;
   wood.maple-birdseye|Bird's-eye Maple|T; wood.cherry|Cherry Wood|T; wood.ash|Ash Wood|T; wood.teak|Teak|T; wood.ebony|Ebony|T;
   wood.zebrawood|Zebrawood|T; wood.burl|Burl Wood|T; wood.spalted|Spalted Wood|T; wood.driftwood|Driftwood|T;
   wood.charred|Charred Wood (Yakisugi)|T; wood.olive|Olive Wood|T; wood.cedar|Cedar|T; wood.pine-knotty|Knotty Pine|T;
   wood.mahogany|Mahogany|T; wood.wenge|Wenge|T""",
  "plant-fibers": """bamboo.fiber|Bamboo Fiber|T; cork.granulated|Granulated Cork|T; rattan.woven|Woven Rattan|T; fiber.coir|Coir|T;
   fiber.sisal|Sisal|T; fiber.flax|Flax Linen|T; fiber.papyrus|Papyrus|T; fiber.raffia|Raffia|T; straw.thatch|Thatch|T;
   reed.woven|Woven Reed|T; fiber.cotton-boll|Cotton Boll|O""",
  "reproductive": """seedpod.ribbed|Seed Pod|O; petal.flower|Flower Petal|O; pinecone.scales|Pine Cone|O; seedhead.sunflower|Sunflower Seed Head|T;
   seedpod.lotus|Lotus Seed Pod|O; peel.citrus|Citrus Peel|T; husk.coconut|Coconut Husk|T; acorn.cap|Acorn Cap|O; petal.rose|Rose Petal|O;
   petal.orchid|Orchid Petal|O; silk.milkweed|Milkweed Silk|O; burr.chestnut|Chestnut Burr|O; seedhead.dandelion|Dandelion Clock|O""",
  "aquatic-plants": """seaweed.kelp|Kelp|O; seaweed.bladderwrack|Bladderwrack|O; algae.mat|Algal Mat|T; lilypad.pond|Lily Pad|O;
   duckweed.carpet|Duckweed Carpet|T""",
 },
 "aquatic": {
  "water-surfaces": """water.still|Still Water|A; water.ripple|Rippled Water|A; foam.sea|Sea Foam|A; caustic.light|Caustic Light|A;
   water.rain-ripples|Rain on Water|A; water.waterfall|Waterfall Sheet|A; water.rapids|Whitewater Rapids|A;
   water.ocean-swell|Ocean Swell|A; water.tide-pool|Tide Pool|A; water.glacial-milk|Glacial Meltwater|A""",
  "shore-wet": """sand.wet|Wet Sand|T; rock.wet|Wet Rock|T; pebble.wet|Wet Pebbles|T; mud.tidal-flat|Tidal Mudflat|T;
   rock.algae-slick|Algae-slick Rock|T; seaglass.frosted|Sea Glass|O; sand.swash-marks|Swash Marks|T""",
  "underwater": """haze.underwater|Underwater haze|V; seafloor.sand-ripples|Seafloor Ripples|T; seagrass.meadow|Seagrass Meadow|A;
   kelp.forest|Kelp Forest|V; bubbles.rising|Rising Bubbles|A; light.underwater-rays|Underwater Light Rays|V""",
 },
 "atmospheric": {
  "frozen": """ice.sheet|Ice Sheet|T; frost.crystal|Frost Crystals|T; snow.crust|Snow Crust|T; ice.black|Black Ice|T;
   ice.glacier|Glacier Ice|T; ice.cracked|Cracked Ice|T; ice.bubbles|Ice with Trapped Bubbles|T; icicle.cluster|Icicles|O;
   snow.powder|Powder Snow|T; snow.sastrugi|Sastrugi|T; hoarfrost.feathery|Hoarfrost|T; rime.ice|Rime Ice|T;
   frost.window|Window Frost|T""",
  "condensation": """dew.droplets|Dew Droplets|T; condensation.glass|Condensation on Glass|T; rain.on-glass|Rain on Glass|A""",
  "veils": """mist.diffuse|Mist|V; fog.layer|Fog Layer|V; light.shafts|Leaf-filtered light shafts|V; steam.rising|Rising Steam|V;
   haze.heat-shimmer|Heat Shimmer|A; smoke.wisps|Smoke Wisps|V; dust.motes|Dust Motes|V; rain.curtain|Rain Curtain|A""",
  "sky": """cloud.cumulus|Cumulus Clouds|V; cloud.stratus|Stratus Clouds|V; cloud.mammatus|Mammatus Clouds|V;
   sky.dusk-gradient|Dusk Sky|T; aurora.curtain|Aurora|A; sky.night-stars|Night Sky|T""",
  "low-light": """biolum.wateredge|Bioluminescent Water Edge|A; fungi.glowing|Glowing fungi|O; firefly.field|Firefly field|V;
   glowworm.ceiling|Glowworm Cave Ceiling|A""",
  "fire-heat": """ember.bed|Ember Bed|A; flame.candle|Candle Flame|A; ash.smoldering|Smoldering Ash|A; charcoal.glowing|Glowing Charcoal|A""",
 },
 "fauna": {
  "scales-skin": """scales.fish|Fish Scales|T; scales.snake|Snake Scales|T; hide.reptile|Reptile Hide|T; scales.koi|Koi Scales|T;
   scales.pangolin|Pangolin Scales|T; hide.crocodile|Crocodile Osteoderms|T; skin.gecko|Gecko Skin|T; skin.chameleon|Chameleon Skin|T;
   skin.shark|Shark Denticles|T; skin.frog|Frog Skin|T; skin.toad|Toad Skin|T; hide.elephant|Elephant Hide|T; skin.rhino|Rhino Skin|T""",
  "fibers-plumage": """feather.barbs|Feather Barbs|T; fur.soft|Soft Fur|T; wing.butterfly|Butterfly Wing|T; fur.wool|Sheep Wool|T;
   fur.alpaca|Alpaca Fleece|T; quills.hedgehog|Hedgehog Quills|T; feather.down|Down Feathers|T; feather.owl|Owl Plumage|T;
   feather.pheasant|Pheasant Contour Feathers|T; wing.moth|Moth Wing|T; wing.dragonfly|Dragonfly Wing|O; wing.cicada|Cicada Wing|O""",
  "iridescence": """elytra.beetle|Beetle Shell|T; feather.peacock|Peacock Feather|O; skin.cuttlefish|Cuttlefish Skin|A;
   feather.hummingbird|Hummingbird Gorget|T; feather.starling|Starling Plumage|T; wing.morpho|Morpho Wing Scales|T;
   beetle.jewel|Jewel Beetle|T; skin.mackerel|Mackerel Skin|T""",
  "marine": """coral.skeleton|Coral Skeleton|T; nacre.shell|Shell Mother-of-Pearl|T; shell.abalone|Abalone Shell|T;
   shell.cowrie|Cowrie Shell|O; shell.scallop|Scallop Shell|O; shell.conch|Conch Shell|O; shell.nautilus|Nautilus Shell|O;
   urchin.test|Sea Urchin Test|O; sanddollar.test|Sand Dollar|O; starfish.skin|Starfish Skin|T; sponge.sea|Sea Sponge|T;
   barnacle.cluster|Barnacle Cluster|T; coral.brain|Brain Coral|T; coral.staghorn|Staghorn Coral|O; pearl.lustre|Pearl|O;
   jellyfish.bell|Jellyfish|A; skin.octopus|Octopus Skin|A""",
  "pattern-fields": """pattern.camouflage|Camouflage Patterning|T; pattern.leopard|Leopard Rosettes|T; pattern.tiger|Tiger Stripes|T;
   pattern.zebra|Zebra Stripes|T; pattern.giraffe|Giraffe Reticulation|T; pattern.cheetah|Cheetah Spots|T;
   pattern.pufferfish|Pufferfish Maze|T; pattern.boxfish|Boxfish Hexagons|T; pattern.ladybird|Ladybird Spots|T;
   pattern.poison-frog|Poison Dart Frog|T""",
  "biogenic-structures": """honeycomb.wax|Honeycomb|T; nest.wasp-paper|Wasp Nest Paper|T; nest.bird|Bird's Nest|O;
   silk.spiderweb|Spider Web|O; silk.cocoon|Silk Cocoon|O; eggshell.speckled|Speckled Eggshell|T; eggshell.ostrich|Ostrich Eggshell|T;
   bone.cancellous|Cancellous Bone|T; horn.keratin|Horn|T; antler.velvet|Antler Velvet|T; carapace.turtle|Turtle Carapace|T;
   eye.compound|Compound Eye|T""",
 },
}


def main():
    doc = json.loads(PATH.read_text())
    old = {m["id"]: m for m in doc["materials"]}
    out, seen = [], set()
    for family, classes in CATALOG.items():
        for cls, block in classes.items():
            for raw in block.split(";"):
                slug, name, kind = (x.strip() for x in raw.split("|"))
                mid = f"{PREFIX[family]}.{slug}.v1"
                assert mid not in seen, mid
                seen.add(mid)
                entry = old.get(mid) or {"id": mid, "display_name": name, "family": family, "kind": KIND[kind],
                                         "atlas_code": None, "origin": "expansion-2026-10-14"}
                entry = {**entry, "class": cls}
                assert entry["kind"] == KIND[kind], (mid, entry["kind"], kind)
                out.append({k: entry[k] for k in ("id", "display_name", "family", "class", "kind", "atlas_code", "origin")})
    missing = set(old) - seen
    assert not missing, f"existing ids dropped: {sorted(missing)}"
    doc["materials"] = out
    PATH.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print(len(out), "materials", dict(Counter(m["family"] for m in out)))
    print(dict(Counter(m["origin"] for m in out)))
    print(dict(Counter(m["kind"] for m in out)))
    print(len({(m["family"], m["class"]) for m in out}), "classes")


if __name__ == "__main__":
    main()
