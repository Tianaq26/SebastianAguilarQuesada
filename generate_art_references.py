"""
Eteria — Game Art Reference Generator
Generates DALL-E 3 reference images organized by region and category.

Categories:
  consumables  — items, plants, ingredients  (flat gray bg, front view)
  recipes      — cooked dishes               (flat gray bg, front view)
  architecture — houses and key locations    (exterior/environment view)
  npcs         — village character designs   (full body, front view, character sheet)

Usage:
    export OPENAI_API_KEY="sk-..."
    python generate_art_references.py

    # Only one region:
    python generate_art_references.py --region VALKAR

    # Only one category:
    python generate_art_references.py --only npcs

    # Dry run (print prompts, no API calls):
    python generate_art_references.py --dry-run
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
    from openai import OpenAI
except ImportError:
    print("Missing dependencies. Run: pip install openai requests")
    sys.exit(1)


# ---------------------------------------------------------------------------
# REGION DATA
# ---------------------------------------------------------------------------

REGIONS = {
    "VALKAR": {
        "aesthetic": (
            "Carpathian medieval fantasy, dark pine forest, snow-capped mountains, "
            "stone castles, cold northern atmosphere, candlelight, carved wood, "
            "Romanian Maramures folk art details"
        ),
        "consumables": [
            {
                "name": "Ajo Negro de Valkar",
                "desc": "jet-black fermented garlic bulb with dark glossy cloves, wrapped in dried vine leaves",
                "type": "spice",
            },
            {
                "name": "Miel de Bosque Cárpático",
                "desc": "golden amber wild forest honey in a small clay pot sealed with beeswax",
                "type": "ingredient",
            },
            {
                "name": "Hongo de Pino Oscuro",
                "desc": "dark indigo mushroom with bioluminescent spots, growing from pine bark",
                "type": "mushroom",
            },
            {
                "name": "Baya de Enebro",
                "desc": "cluster of blue-violet juniper berries with a frosted dusting, on a twig",
                "type": "berry",
            },
            {
                "name": "Raíz de Mandrágora",
                "desc": "twisted pale humanoid-shaped mandrake root with thin tendrils and small purple flowers",
                "type": "rare root",
            },
            {
                "name": "Baya Roja Cárpática",
                "desc": "bright red glossy berries in a small cluster, translucent skin with seeds visible inside",
                "type": "fruit",
            },
            {
                "name": "Cera de Abejas Silvestres",
                "desc": "chunk of rough golden-yellow wild beeswax with honeycomb texture",
                "type": "ingredient",
            },
            {
                "name": "Ámbar Fósil",
                "desc": "polished amber gemstone with a tiny ancient insect trapped inside, warm orange glow",
                "type": "mineral amulet",
            },
        ],
        "recipes": [
            {
                "name": "Mămăligă con Queso",
                "desc": (
                    "golden cornmeal porridge in a rustic clay bowl topped with melted "
                    "mountain sheep cheese, steam rising"
                ),
            },
            {
                "name": "Sarmale Real",
                "desc": (
                    "stuffed white cabbage rolls with smoked venison and wild rice, "
                    "arranged on a carved wooden plate, dried herbs garnish"
                ),
            },
            {
                "name": "Tochitura del Guardia Real",
                "desc": (
                    "hearty Carpathian stew of salted pork, eagle egg, aged cheese and "
                    "black garlic in a deep iron pot"
                ),
            },
            {
                "name": "Cozonac de Festividad",
                "desc": (
                    "braided celebration bread with rye flour, forest honey and Carpathian walnuts, "
                    "golden-brown crust dusted with powdered sugar"
                ),
            },
            {
                "name": "Ciorbă del Santuario",
                "desc": (
                    "sacred sanctuary broth with bear bone, white turnip and glacier water "
                    "in a stone bowl, wisps of herbal steam"
                ),
            },
        ],
        "architecture": [
            {
                "name": "Iglesia_Madera_Maramures",
                "desc": (
                    "Maramures-style wooden church with an extremely tall pointed steeple rising 20 meters, "
                    "built entirely from dark oak without nails, roof shingles carved to imitate dragon scales, "
                    "door lintel covered in serpent and leaf carvings, surrounded by snow-covered pine trees, "
                    "Carpathian fantasy medieval village"
                ),
            },
            {
                "name": "Castillo_de_Valkar",
                "desc": (
                    "medieval Carpathian stone castle with square towers and double perimeter walls, "
                    "inner courtyard with a stone well, princess garden visible over the walls, "
                    "flags with dragon crests in the cold wind, mountains and pine forest in the background, "
                    "gray stone, snow on the battlements"
                ),
            },
            {
                "name": "Aldea_Troncos_Valkar",
                "desc": (
                    "cozy Carpathian log cabin village house with a thick thatched roof, "
                    "carved wooden door with a family dragon symbol, small windows with warm candlelight inside, "
                    "snow on the ground, pine forest behind, smoke from chimney, "
                    "compact and warm-looking despite the cold"
                ),
            },
            {
                "name": "El_Santuario_de_Valkar",
                "desc": (
                    "ancient hidden sanctuary in a mountain clearing, older and more mystical than anything else in Valkar, "
                    "stone arches covered in moss and carved runes, glowing faintly, "
                    "two young dragons resting near the entrance, forgotten by time, "
                    "filtered light through ancient trees, ethereal atmosphere"
                ),
            },
            {
                "name": "Fortaleza_Amurallada",
                "desc": (
                    "small fortified Carpathian market town enclosed by double stone walls with watchtowers, "
                    "busy market stalls inside near the gate, guild signs hanging from buildings, "
                    "cobblestone streets, medieval fantasy atmosphere, mountain background"
                ),
            },
        ],
        "npcs": [
            {
                "name": "Aldeano_Hombre_Valkar",
                "desc": (
                    "male Carpathian medieval fantasy villager, full body front view character reference sheet, "
                    "wearing undyed linen shirt with embroidered collar, leather vest with brass buttons, "
                    "thick wool trousers, fur-lined leather boots, wool cap, "
                    "stocky build, dark brown hair, weathered face, friendly expression, "
                    "Romanian folk art clothing patterns"
                ),
            },
            {
                "name": "Aldeana_Mujer_Valkar",
                "desc": (
                    "female Carpathian medieval fantasy villager, full body front view character reference sheet, "
                    "wearing white embroidered blouse with red and black folk patterns, dark wool skirt, "
                    "colorful woven apron, white head kerchief with embroidered edge, leather sandals, "
                    "warm smile, dark braided hair, Romanian folk art style clothing"
                ),
            },
            {
                "name": "Guardia_Soldado_Valkar",
                "desc": (
                    "male Valkar royal guard soldier, full body front view character reference sheet, "
                    "wearing chainmail hauberk, dark tabard with a red dragon emblem on the chest, "
                    "iron pauldrons, leather bracers, knee-high boots, longsword at hip, "
                    "short beard, stoic expression, Carpathian medieval fantasy style"
                ),
            },
            {
                "name": "Comerciante_Valkar",
                "desc": (
                    "middle-aged male merchant from Valkar, full body front view character reference sheet, "
                    "wearing a thick fur-collared traveling coat over layered wool clothes, "
                    "wide-brimmed hat, carrying a leather satchel, belt with coin purse, "
                    "calculating expression, prosperous but practical look, Carpathian medieval fantasy"
                ),
            },
        ],
    },

    "NYRU": {
        "aesthetic": (
            "Taíno Caribbean fantasy, turquoise ocean, tropical jungle, vibrant coral colors, "
            "warm golden sunlight, palm leaves, woven textures, ceremonial body paint, "
            "cemí geometric patterns in red and black"
        ),
        "consumables": [
            {
                "name": "Guanabana",
                "desc": "large spiny soursop fruit with dark green bumpy skin, creamy white interior in cross-section",
                "type": "fruit",
            },
            {
                "name": "Mamey",
                "desc": "mamey sapote fruit cut open, russet brown skin, vibrant salmon-orange flesh, single dark glossy seed",
                "type": "fruit",
            },
            {
                "name": "Papaya_Silvestre",
                "desc": "small wild papaya cut open showing bright orange flesh and black seeds arranged in a star",
                "type": "fruit",
            },
            {
                "name": "Coco_Verde",
                "desc": "fresh green coconut with top cut open, bamboo drinking straw, condensation on the shell",
                "type": "fruit",
            },
            {
                "name": "Hongo_Azul_del_Manglar",
                "desc": "iridescent blue mangrove mushroom with bioluminescent gills, growing from twisted roots",
                "type": "mushroom",
            },
            {
                "name": "Raíz_de_Bejuco",
                "desc": "thick woody tropical vine root coiled into a bundle, reddish-brown bark, medicinal plant",
                "type": "medicinal plant",
            },
            {
                "name": "Flor_de_Flamboyan",
                "desc": "brilliant flame-red flamboyant flower cluster with delicate petals, deep green leaves",
                "type": "flower",
            },
            {
                "name": "Escama_de_Coral",
                "desc": "thin iridescent coral scale shaped like a fish scale, pink and white, faintly glowing",
                "type": "organic mineral",
            },
        ],
        "recipes": [
            {
                "name": "Casabe_de_Yuca_con_Pescado",
                "desc": (
                    "circular flat yuca bread on a woven palm leaf, topped with grilled reef fish, "
                    "lime wedges and wild herb garnish, painted wooden platter"
                ),
            },
            {
                "name": "Sancocho_Nyruani",
                "desc": (
                    "thick tropical stew with yam, green plantain, iguana meat and Caribbean chili "
                    "in a clay pot with painted cemí motifs"
                ),
            },
            {
                "name": "Mofongo_de_Mar",
                "desc": (
                    "mashed fried green plantain dome in a wooden pilón bowl, "
                    "filled with garlic-shrimp broth, steam in warm tropical light"
                ),
            },
            {
                "name": "Bebida_de_Cacao_Ritual",
                "desc": (
                    "ceremonial chocolate drink in a painted clay cup, deep brown with orange chili foam, "
                    "cacao pods around it, candlelight"
                ),
            },
            {
                "name": "Tamal_de_Coco_con_Camarón",
                "desc": (
                    "coconut and shrimp tamal wrapped in banana leaf tied with palm string, "
                    "partially opened to reveal golden filling"
                ),
            },
        ],
        "architecture": [
            {
                "name": "Casas_sobre_Pilotes_Nyru",
                "desc": (
                    "Taíno Caribbean fantasy stilt houses built on wooden ceiba poles over a turquoise lagoon, "
                    "connected by hanging rope bridges, each house painted a different vibrant color "
                    "(blue, yellow, coral red), cone-shaped thatched palm roofs, "
                    "fishing nets hanging from the sides, sunset light on calm water"
                ),
            },
            {
                "name": "Bohío_Nyruani",
                "desc": (
                    "circular Taíno bohío dwelling with a high conical thatched palm roof, "
                    "walls painted with red and black cemí geometric patterns, "
                    "open doorway with a woven curtain, surrounded by tropical flowers and banana plants, "
                    "warm golden sunlight, Caribbean fantasy village"
                ),
            },
            {
                "name": "Templo_Piedra_Coralina",
                "desc": (
                    "Taíno ceremonial temple built from pink coral stone with deep relief carvings of sea turtles, "
                    "serpents and cemí spirits on every wall, wide stone steps leading to an open altar, "
                    "ocean visible behind it, torches in the walls, sacred and imposing"
                ),
            },
            {
                "name": "Torre_Avistamiento_Acantilado",
                "desc": (
                    "tall watchtower built from bamboo and driftwood at the edge of a sea cliff, "
                    "overlooking turquoise ocean where sea dragon silhouettes glow under the water, "
                    "a Nyruani scout stands at the top with a conch shell horn, "
                    "tropical fantasy atmosphere, dramatic ocean view"
                ),
            },
            {
                "name": "Plaza_Ceremonial_Bato",
                "desc": (
                    "Taíno ceremonial plaza, large open area of packed earth surrounded by carved standing stones "
                    "with cemí faces, colorful banners strung between poles, "
                    "a central fire pit with ritual offerings, villagers in ceremonial dress around it, "
                    "Caribbean fantasy village, evening light"
                ),
            },
        ],
        "npcs": [
            {
                "name": "Pescador_Nyruani",
                "desc": (
                    "male Taíno Caribbean fantasy fisherman, full body front view character reference sheet, "
                    "minimal clothing: short cotton wrap skirt in natural brown, bare-chested, "
                    "geometric body paint in red and black on arms and face, shell and bone necklaces, "
                    "rope bracelet, fishing spear in hand, dark skin, curly black hair, "
                    "confident and weathered expression"
                ),
            },
            {
                "name": "Cacica_Chamana",
                "desc": (
                    "female Taíno cacica and shaman leader, full body front view character reference sheet, "
                    "wearing a ceremonial cotton dress with red and black cemí patterns, "
                    "large feathered headdress with macaw and parrot feathers, "
                    "elaborate shell and bone jewelry on neck, wrists and ankles, "
                    "ritual staff with carved cemí face, dark skin, commanding presence, "
                    "Caribbean fantasy noble"
                ),
            },
            {
                "name": "Vendedora_Mercado_Nyru",
                "desc": (
                    "female Nyruani market seller, full body front view character reference sheet, "
                    "wearing colorful cotton blouse with tropical flower print, wrapped skirt in teal and yellow, "
                    "woven basket hat, multiple shell bracelets, carrying a basket of tropical fruits, "
                    "warm smile, middle-aged, Caribbean fantasy village market"
                ),
            },
            {
                "name": "Joven_Explorador_Nyru",
                "desc": (
                    "young male Nyruani explorer and boat guide, full body front view character reference sheet, "
                    "wearing light cotton shorts and an open vest with blue geometric patterns, "
                    "rope sandals, small feather in hair, carries a carved wooden oar, "
                    "lean build, adventurous expression, Caribbean fantasy teenager"
                ),
            },
        ],
    },

    "CARTAGO": {
        "aesthetic": (
            "colonial Costa Rica medieval fantasy, black volcanic stone architecture, "
            "white lime-washed walls, orange clay roof tiles, lush cloud forest greenery, "
            "morning mist, religious motifs, tension between beauty and corruption"
        ),
        "consumables": [
            {
                "name": "Pejibaye",
                "desc": "cluster of peach-palm fruits with orange-red glossy skin, fibrous texture, on the palm stalk",
                "type": "fruit",
            },
            {
                "name": "Cas",
                "desc": "small pale yellow-green cas fruit cut in half showing white grainy tart flesh",
                "type": "sour fruit",
            },
            {
                "name": "Cacao_en_Bruto",
                "desc": "open cacao pod with purple-white seeds arranged inside, rich ridged brown shell",
                "type": "seed",
            },
            {
                "name": "Hongo_de_Selva_Nubosa",
                "desc": "delicate pale green cloud-forest mushroom with translucent cap, growing from mossy log in mist",
                "type": "mushroom",
            },
            {
                "name": "Hoja_de_Ortigón",
                "desc": "large dark green nettle leaf with serrated edges and fine medicinal hairs, on stone surface",
                "type": "medicinal plant",
            },
            {
                "name": "Chile_Chombo",
                "desc": "vibrant orange scotch bonnet pepper, wrinkled and plump, fiery warm glow",
                "type": "spice",
            },
            {
                "name": "Achiote",
                "desc": "open red achiote pod with bright vermilion seeds inside, dried leaves around it",
                "type": "dye and spice",
            },
            {
                "name": "Polvo_de_Ala_de_Morpho",
                "desc": "iridescent electric-blue powder from morpho butterfly wings in a small glass vial, shimmering",
                "type": "magical ingredient",
            },
        ],
        "recipes": [
            {
                "name": "Gallo_Pinto_de_Viajero",
                "desc": (
                    "classic traveler's gallo pinto with rice and black beans in a cast iron pan, "
                    "cilantro garnish and Lizano sauce bottle on the side"
                ),
            },
            {
                "name": "Tamal_de_Navidad",
                "desc": (
                    "festive Costa Rican tamal wrapped in banana leaf with a red ribbon, "
                    "partially unwrapped showing spiced pork and saffron rice filling"
                ),
            },
            {
                "name": "Chorreada_con_Cuajada",
                "desc": (
                    "fresh corn pancake on a clay plate with a slice of white cuajada cheese melting on top, "
                    "steam rising"
                ),
            },
            {
                "name": "Cacao_Ritual_de_la_Negrita",
                "desc": (
                    "sacred dark chocolate ritual drink in a stone mortar cup with sweet pepper and jungle honey, "
                    "glowing faintly gold, surrounded by flower offerings"
                ),
            },
            {
                "name": "Sopa_de_Palmito",
                "desc": (
                    "creamy hearts-of-palm soup in a colonial ceramic bowl with blue floral pattern, "
                    "coconut cream swirl and sweet pepper garnish"
                ),
            },
        ],
        "architecture": [
            {
                "name": "Basilica_de_la_Negrita",
                "desc": (
                    "grand colonial-medieval basilica built from dark volcanic stone with a pale blue Byzantine dome, "
                    "white lime-washed walls, twin bell towers, wide stone steps with worshippers, "
                    "surrounded by tropical flowers and candles at the base, "
                    "morning mist in the mountains behind it, Costa Rica colonial fantasy"
                ),
            },
            {
                "name": "Plaza_Central_de_Cartago",
                "desc": (
                    "colonial Costa Rica medieval fantasy main plaza, black volcanic stone paving, "
                    "a central fountain with a dragon-and-serpent motif, market stalls around the edges, "
                    "grand buildings with arched porticoes on each side, orange roof tiles, "
                    "soldiers patrolling, tense atmosphere, misty morning"
                ),
            },
            {
                "name": "Hacienda_Mendoza",
                "desc": (
                    "imposing colonial hacienda surrounded by high black volcanic stone walls with iron spike tops, "
                    "heavy iron gate with a wealthy family crest, coffee plantations visible on the hills beyond, "
                    "watchtowers at the corners, guards with spears, "
                    "grand but oppressive atmosphere, Costa Rica colonial fantasy"
                ),
            },
            {
                "name": "Ruinas_del_Primer_Cartago",
                "desc": (
                    "ruins of the first Cartago cathedral, only the stone perimeter walls remain standing, "
                    "cracked and moss-covered from a great earthquake, inside is an open-air memorial "
                    "with candles and offerings, wild tropical flowers growing through the cracks, "
                    "haunting and beautiful, colonial Costa Rica fantasy"
                ),
            },
            {
                "name": "Casa_del_Pueblo_Cartago",
                "desc": (
                    "small humble adobe and wood house in the poor quarter of Cartago near the river, "
                    "simple orange tiled roof, window with a cloth curtain, "
                    "small garden with medicinal plants and a guanabana tree, "
                    "laundry hanging outside, warm but modest, colonial Costa Rica fantasy"
                ),
            },
        ],
        "npcs": [
            {
                "name": "Jornalero_Pobre_Cartago",
                "desc": (
                    "male poor laborer from Cartago, full body front view character reference sheet, "
                    "wearing a worn patched linen shirt, simple dark trousers held by a rope belt, "
                    "battered straw hat, cracked leather sandals, callused hands, tired expression, "
                    "tanned skin from outdoor work, Costa Rica colonial medieval fantasy"
                ),
            },
            {
                "name": "Noble_Señor_Feudal",
                "desc": (
                    "male wealthy feudal lord from Cartago, full body front view character reference sheet, "
                    "wearing a rich Spanish colonial doublet in deep burgundy with gold trim, "
                    "ruffled white collar, velvet breeches, polished leather boots, "
                    "a gold signet ring, sword at hip with ornate guard, "
                    "arrogant expression, well-groomed dark beard, colonial Costa Rica medieval fantasy"
                ),
            },
            {
                "name": "Sacerdotisa_de_la_Negrita",
                "desc": (
                    "female priestess of the Negrita, full body front view character reference sheet, "
                    "wearing a flowing black habit with a white wimple and gold embroidered cross on the chest, "
                    "wooden rosary beads, small dark stone figurine hanging at her waist, "
                    "gentle but resolute expression, middle-aged, Costa Rica colonial fantasy religious figure"
                ),
            },
            {
                "name": "Soldado_de_Cartago",
                "desc": (
                    "male soldier of the Cartago noble house, full body front view character reference sheet, "
                    "wearing a dark leather brigandine with metal studs, "
                    "a steel morion helmet with a plume, boots and greaves, "
                    "short sword and crossbow, neutral expression, colonial fantasy soldier"
                ),
            },
        ],
    },

    "SHIHIMA": {
        "aesthetic": (
            "feudal Japan fantasy, bamboo forest, zen rock garden, wooden Shinto shrine, "
            "paper lanterns at dusk, cherry blossom petals, sacred river, "
            "ink-wash painting atmosphere, spiritual serenity"
        ),
        "consumables": [
            {
                "name": "Ciruela_Umeboshi",
                "desc": "wrinkled pickled red ume plum on a small ceramic dish with a pinch of salt crystals",
                "type": "pickled fruit",
            },
            {
                "name": "Seta_Shiitake_Seca",
                "desc": "dried shiitake mushroom cap, dark brown with star-shaped white cracking pattern on top",
                "type": "mushroom",
            },
            {
                "name": "Bambú_Tierno",
                "desc": "freshly cut bamboo shoot cross-section, pale cream interior with concentric rings, earthy",
                "type": "vegetable",
            },
            {
                "name": "Raíz_de_Wasabi_Silvestre",
                "desc": "knobbly wild wasabi rhizome, vibrant green, with a small ceramic grater beside it, forest floor",
                "type": "plant root",
            },
            {
                "name": "Alga_del_Río_Sagrado",
                "desc": "translucent emerald-green sacred river algae in a small porcelain bowl of water, faintly glowing",
                "type": "aquatic plant",
            },
            {
                "name": "Pétalo_de_Sakura",
                "desc": "five delicate pink cherry blossom petals arranged on a black lacquered tray, dew drops",
                "type": "flower petal",
            },
            {
                "name": "Mora_de_Montaña",
                "desc": "deep purple mountain berries in a small woven bamboo basket, glistening",
                "type": "berry",
            },
            {
                "name": "Semilla_de_Loto",
                "desc": "dried lotus seed pod open, round pale seeds inside the honeycomb structure, sacred",
                "type": "sacred plant",
            },
        ],
        "recipes": [
            {
                "name": "Onigiri_de_Ciervo_Sagrado",
                "desc": (
                    "triangular rice onigiri wrapped in dark nori, filled with seasoned sacred deer meat, "
                    "served on a cedar leaf on a wooden shrine tray"
                ),
            },
            {
                "name": "Sopa_Miso_de_Montaña",
                "desc": (
                    "mountain miso soup in a lacquered wooden bowl with tofu, shiitake and wakame seaweed, "
                    "chopsticks resting on the rim"
                ),
            },
            {
                "name": "Mochi_de_Cerezo",
                "desc": (
                    "three pink sakura mochi rice cakes on a ceramic plate, "
                    "wrapped in pickled cherry blossom leaves, petals floating around"
                ),
            },
            {
                "name": "Fideos_Soba_del_Río_Sagrado",
                "desc": (
                    "dark buckwheat soba noodles in clear sacred river broth, mountain scallions "
                    "and golden koi-shaped kamaboko in a deep lacquer bowl"
                ),
            },
            {
                "name": "Té_de_Ceremonia_del_Santuario",
                "desc": (
                    "matcha tea ceremony bowl with frothy green tea, a small lotus flower floating on top, "
                    "tatami mat and incense smoke in the background"
                ),
            },
        ],
        "architecture": [
            {
                "name": "Casa_Minka_Gassho",
                "desc": (
                    "feudal Japan fantasy farmhouse in gassho-zukuri style with an extremely steep thatched roof "
                    "resembling hands in prayer, 45-degree pitch, dark oak beams without nails, "
                    "warm candlelight inside the windows, bamboo fence, small zen garden in front, "
                    "snow on the roof, mountain cedar forest behind"
                ),
            },
            {
                "name": "Pagoda_Cinco_Pisos",
                "desc": (
                    "five-story feudal Japan fantasy pagoda on a forested hill, each level smaller than the one below, "
                    "upturned green-glazed ceramic roof edges with wind bells, "
                    "stone lanterns lining the path to the entrance, "
                    "cherry blossom trees in bloom around the base, misty mountains behind, "
                    "sacred and imposing, dusk lighting"
                ),
            },
            {
                "name": "Torii_del_Río_Sagrado",
                "desc": (
                    "ancient red-lacquered wooden torii gate standing in the middle of a clear sacred river, "
                    "moss and lichen on its base, reflection in the calm water, "
                    "surrounded by ancient cedar trees, paper offerings tied to its crossbeam, "
                    "spiritual and serene, Shinto fantasy atmosphere"
                ),
            },
            {
                "name": "Aldea_Shiramachi",
                "desc": (
                    "peaceful feudal Japan fantasy village main street, wooden minka buildings on both sides, "
                    "paper lanterns hanging between rooftops, merchant stalls with cloth banners, "
                    "a bamboo water channel running along the street, "
                    "Mount Fuji-like peak visible at the end of the road, cherry blossoms falling"
                ),
            },
            {
                "name": "Santuario_del_Último_Torii",
                "desc": (
                    "hidden Shinto fantasy sanctuary at the end of a mossy forest path, "
                    "a single ancient torii gate so old it has turned gray, "
                    "beyond it a simple wooden shrine building with a sacred rope (shimenawa) across the door, "
                    "white paper zigzag streamers hanging, deer nearby, total silence and peace"
                ),
            },
        ],
        "npcs": [
            {
                "name": "Campesino_Shihima",
                "desc": (
                    "male feudal Japan fantasy farmer villager, full body front view character reference sheet, "
                    "wearing a plain indigo kimono tied with a straw rope, bamboo sandals (zori), "
                    "wide conical straw hat (kasa), carrying a bamboo hoe, "
                    "lean build, sun-tanned skin, calm expression, "
                    "simple and dignified look, ink-wash illustration style"
                ),
            },
            {
                "name": "Miko_Sacerdotisa",
                "desc": (
                    "female Shinto shrine priestess (miko), full body front view character reference sheet, "
                    "wearing the classic white haori jacket over a red hakama skirt, "
                    "black hair in a simple updo with a red ribbon, white tabi socks, "
                    "holding a ceremonial sakaki branch with white paper streamers, "
                    "serene and graceful expression, feudal Japan fantasy"
                ),
            },
            {
                "name": "Guardián_Guerrero_Shihima",
                "desc": (
                    "male feudal Japan fantasy samurai guardian of Shihima, full body front view character reference sheet, "
                    "wearing lamellar lacquered armor (oyoroi) in dark green and gold, "
                    "kabuto helmet with a crescent moon crest, katana at the waist, "
                    "stern focused expression, kneeling ready stance, "
                    "detailed feudal Japan fantasy warrior"
                ),
            },
            {
                "name": "Mercader_Shihima",
                "desc": (
                    "male travelling merchant from Shihima, full body front view character reference sheet, "
                    "wearing a patterned merchant's kimono in warm brown and ochre, "
                    "carrying a tenbin pole across the shoulders with two large woven baskets, "
                    "small coin purse on the belt, sandals, cheerful expression, "
                    "feudal Japan fantasy traveling trader"
                ),
            },
        ],
    },
}

ALL_CATEGORIES = ["consumables", "recipes", "architecture", "npcs"]

# ---------------------------------------------------------------------------
# PROMPT BUILDERS
# ---------------------------------------------------------------------------

ITEM_STYLE = (
    "fantasy RPG game concept art, hand-painted illustration, "
    "detailed textures, soft even lighting, centered composition, "
    "flat neutral gray background (#AAAAAA), front view, "
    "2D game inventory reference art, rich saturated colors, clean edges"
)

ARCH_STYLE = (
    "fantasy RPG game environment concept art, hand-painted illustration, "
    "architectural exterior view, natural lighting, detailed, "
    "establishing shot, game world concept art, rich atmosphere"
)

NPC_STYLE = (
    "fantasy RPG character design reference sheet, full body front view, "
    "standing neutral pose, hand-painted illustration, "
    "flat neutral gray background (#AAAAAA), "
    "detailed clothing and costume design, "
    "game character concept art, clear silhouette, rich colors"
)


def build_prompt(item: dict, region_aesthetic: str, category: str) -> str:
    name = item["name"].replace("_", " ")

    if category == "consumables":
        subject = (
            f"A fantasy RPG game item '{name}' "
            f"({item.get('type', 'consumable')}): {item['desc']}. "
            f"Isolated on flat gray background, front view, centered."
        )
        style = ITEM_STYLE

    elif category == "recipes":
        subject = (
            f"A fantasy RPG game food dish '{name}': {item['desc']}. "
            f"Shown as a single plated dish centered, flat gray background, front view."
        )
        style = ITEM_STYLE

    elif category == "architecture":
        subject = f"A fantasy RPG game building '{name}': {item['desc']}."
        style = ARCH_STYLE

    elif category == "npcs":
        subject = (
            f"Fantasy RPG character '{name}': {item['desc']}. "
            f"Full body, front view, flat gray background, standing pose."
        )
        style = NPC_STYLE

    return f"{subject} {style}. Region visual theme: {region_aesthetic}."


# ---------------------------------------------------------------------------
# IMAGE GENERATION
# ---------------------------------------------------------------------------

def generate_and_save(
    client: "OpenAI", prompt: str, output_path: Path, dry_run: bool
) -> bool:
    if dry_run:
        print(f"    [DRY RUN] {output_path.name}")
        print(f"    Prompt: {prompt[:130]}...")
        return True

    if output_path.exists():
        print(f"    [SKIP] {output_path.name} already exists")
        return True

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        img_data = requests.get(image_url, timeout=30).content
        output_path.write_bytes(img_data)
        print(f"    [OK] {output_path.name}")
        return True
    except Exception as exc:
        print(f"    [ERROR] {output_path.name}: {exc}")
        return False


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate Eteria game art references with DALL-E 3"
    )
    parser.add_argument(
        "--region", choices=list(REGIONS.keys()), help="Generate only this region"
    )
    parser.add_argument(
        "--only",
        choices=ALL_CATEGORIES,
        help="Generate only this category",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without calling the API",
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: Set the OPENAI_API_KEY environment variable.")
        sys.exit(1)

    client = OpenAI(api_key=api_key) if not args.dry_run else None

    output_root = Path("art_references")
    output_root.mkdir(exist_ok=True)

    categories = [args.only] if args.only else ALL_CATEGORIES
    regions_to_process = (
        {args.region: REGIONS[args.region]} if args.region else REGIONS
    )

    log = []

    for region_name, region_data in regions_to_process.items():
        print(f"\n{'='*64}")
        print(f"  Region: {region_name}")
        print(f"{'='*64}")

        region_dir = output_root / region_name.lower()
        region_dir.mkdir(exist_ok=True)
        aesthetic = region_data["aesthetic"]

        for category in categories:
            items = region_data.get(category, [])
            if not items:
                continue

            cat_dir = region_dir / category
            cat_dir.mkdir(exist_ok=True)
            print(f"\n  [{category.upper()}]  ({len(items)} items)")

            for item in items:
                safe_name = item["name"].replace(" ", "_").replace("/", "-")
                output_path = cat_dir / f"{safe_name}.png"
                prompt = build_prompt(item, aesthetic, category)

                ok = generate_and_save(client, prompt, output_path, args.dry_run)
                log.append(
                    {
                        "region": region_name,
                        "category": category,
                        "name": item["name"],
                        "file": str(output_path),
                        "success": ok,
                    }
                )
                if not args.dry_run and ok:
                    time.sleep(1)  # respect DALL-E rate limits

    # Save summary log
    log_path = output_root / "generation_log.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2))

    total = len(log)
    success = sum(1 for e in log if e["success"])
    print(f"\n{'='*64}")
    print(f"  Done: {success}/{total} images generated")
    print(f"  Output: {output_root.resolve()}")
    print(f"  Log:    {log_path}")


if __name__ == "__main__":
    main()
