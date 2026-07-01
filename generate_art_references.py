"""
Eteria — Game Art Reference Generator
Generates DALL-E 3 reference images for consumable items, plants, and recipes
organized by region (Valkar, Nyru, Cartago, Shihima).

Usage:
    export OPENAI_API_KEY="sk-..."
    python generate_art_references.py

    # Only one region:
    python generate_art_references.py --region VALKAR

    # Only recipes (skip individual consumables):
    python generate_art_references.py --only recipes

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
# DATA — consumables, plants and recipes per region
# ---------------------------------------------------------------------------

REGIONS = {
    "VALKAR": {
        "aesthetic": (
            "Carpathian medieval fantasy, dark pine forest, snow, stone castle, "
            "cold northern atmosphere, candlelight, wooden textures"
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
                    "golden cornmeal porridge in a rustic clay bowl topped with melted mountain sheep cheese, "
                    "steam rising, served on a rough wooden table"
                ),
            },
            {
                "name": "Sarmale Real",
                "desc": (
                    "stuffed white cabbage rolls with smoked venison and wild rice, arranged on a carved wooden plate, "
                    "garnished with dried herbs"
                ),
            },
            {
                "name": "Tochitura del Guardia Real",
                "desc": (
                    "hearty Carpathian stew of salted pork, eagle egg, aged cheese and black garlic "
                    "in a deep iron pot over embers"
                ),
            },
            {
                "name": "Cozonac de Festividad",
                "desc": (
                    "braided celebration bread with rye flour, forest honey, Carpathian walnuts and sheep milk, "
                    "golden-brown crust, dusted with powdered sugar"
                ),
            },
            {
                "name": "Ciorbă del Santuario",
                "desc": (
                    "sacred sanctuary broth with bear bone, white turnip and glacier water in a stone bowl, "
                    "wisps of herbal steam, dark and mystical"
                ),
            },
        ],
    },

    "NYRU": {
        "aesthetic": (
            "Taíno Caribbean fantasy, turquoise ocean, tropical jungle, vibrant coral colors, "
            "warm sunlight, palm leaves, woven textures, ceremonial patterns"
        ),
        "consumables": [
            {
                "name": "Guanabana",
                "desc": "large spiny soursop fruit with dark green bumpy skin and creamy white interior visible in a cross-section",
                "type": "fruit",
            },
            {
                "name": "Mamey",
                "desc": "whole mamey sapote fruit, russet brown skin, vibrant salmon-orange flesh exposed, "
                        "single dark glossy seed",
                "type": "fruit",
            },
            {
                "name": "Papaya Silvestre",
                "desc": "small wild papaya cut open showing bright orange flesh and black seeds arranged in a star",
                "type": "fruit",
            },
            {
                "name": "Coco Verde",
                "desc": "fresh green coconut with its top cut open, drinking straw made of bamboo, "
                        "condensation on the shell",
                "type": "fruit",
            },
            {
                "name": "Hongo Azul del Manglar",
                "desc": "iridescent blue mangrove mushroom with bioluminescent gills, growing from twisted roots",
                "type": "mushroom",
            },
            {
                "name": "Raíz de Bejuco",
                "desc": "thick woody tropical vine root coiled into a bundle, reddish-brown bark, medicinal",
                "type": "medicinal plant",
            },
            {
                "name": "Flor de Flamboyan",
                "desc": "brilliant flame-red flamboyant flower cluster with delicate petals, deep green leaves",
                "type": "flower",
            },
            {
                "name": "Escama de Coral",
                "desc": "thin iridescent coral scale shaped like a fish scale, pink and white, faintly glowing",
                "type": "organic mineral",
            },
        ],
        "recipes": [
            {
                "name": "Casabe de Yuca con Pescado",
                "desc": (
                    "circular flat yuca bread on a woven palm leaf, topped with grilled reef fish, "
                    "lime wedges and wild herb garnish, served on a painted wooden platter"
                ),
            },
            {
                "name": "Sancocho Nyruani",
                "desc": (
                    "thick tropical stew with yam, green plantain, iguana meat and Caribbean chili "
                    "in a large clay pot with painted cemí motifs"
                ),
            },
            {
                "name": "Mofongo de Mar",
                "desc": (
                    "mashed fried green plantain molded into a dome in a wooden pilón bowl, "
                    "filled with garlic-shrimp broth, steam rising in warm tropical light"
                ),
            },
            {
                "name": "Bebida de Cacao Ritual",
                "desc": (
                    "ceremonial chocolate drink in a painted clay cup, deep brown with orange chili foam, "
                    "served on a woven mat with cacao pods around it, candlelight"
                ),
            },
            {
                "name": "Tamal de Coco con Camarón",
                "desc": (
                    "coconut and shrimp tamal wrapped in banana leaf tied with palm string, "
                    "partially opened to reveal the golden filling, tropical background"
                ),
            },
        ],
    },

    "CARTAGO": {
        "aesthetic": (
            "colonial Costa Rica medieval fantasy, black volcanic stone, white lime walls, "
            "orange roof tiles, cloud forest greenery, misty mountains, religious motifs"
        ),
        "consumables": [
            {
                "name": "Pejibaye",
                "desc": "cluster of peach-palm fruits with orange-red glossy skin and fibrous texture, on the palm stalk",
                "type": "fruit",
            },
            {
                "name": "Cas",
                "desc": "small pale yellow-green cas fruit, tart tropical, cut in half showing white grainy flesh",
                "type": "sour fruit",
            },
            {
                "name": "Cacao en Bruto",
                "desc": "open cacao pod with purple-white seeds arranged inside, rich brown shell with ridges",
                "type": "seed",
            },
            {
                "name": "Hongo de Selva Nubosa",
                "desc": "delicate pale green cloud-forest mushroom with translucent cap, growing from mossy log in mist",
                "type": "mushroom",
            },
            {
                "name": "Hoja de Ortigón",
                "desc": "large dark green nettle leaf with serrated edges and fine medicinal hairs, on stone surface",
                "type": "medicinal plant",
            },
            {
                "name": "Chile Chombo",
                "desc": "vibrant orange scotch bonnet pepper, wrinkled and plump, with fiery glow",
                "type": "spice",
            },
            {
                "name": "Achiote",
                "desc": "open red achiote pod with bright vermilion seeds inside, dried leaves around it",
                "type": "dye and spice",
            },
            {
                "name": "Polvo de Ala de Morpho",
                "desc": "iridescent electric-blue powder from morpho butterfly wings in a small glass vial, shimmering",
                "type": "magical ingredient",
            },
        ],
        "recipes": [
            {
                "name": "Gallo Pinto de Viajero",
                "desc": (
                    "classic traveler's gallo pinto with rice and black beans in a cast iron pan, "
                    "cilantro garnish and Lizano sauce on the side, rustic stone kitchen"
                ),
            },
            {
                "name": "Tamal de Navidad",
                "desc": (
                    "festive Costa Rican tamal wrapped in banana leaf with a red ribbon, "
                    "partially unwrapped showing spiced pork and saffron rice filling"
                ),
            },
            {
                "name": "Chorreada con Cuajada",
                "desc": (
                    "fresh corn chorreada pancake on a clay plate with a slice of white cuajada cheese "
                    "melting on top, steam rising, rustic wooden table"
                ),
            },
            {
                "name": "Cacao Ritual de la Negrita",
                "desc": (
                    "sacred dark chocolate ritual drink in a stone mortar cup, with sweet pepper "
                    "and jungle honey, glowing faintly gold, surrounded by flower offerings"
                ),
            },
            {
                "name": "Sopa de Palmito",
                "desc": (
                    "creamy hearts-of-palm soup in a colonial ceramic bowl with blue floral pattern, "
                    "garnished with coconut cream swirl and sweet pepper"
                ),
            },
        ],
    },

    "SHIHIMA": {
        "aesthetic": (
            "feudal Japan fantasy, bamboo forest, zen garden, wooden shrine, paper lanterns, "
            "cherry blossoms, ink-wash atmosphere, sacred river, peaceful spirituality"
        ),
        "consumables": [
            {
                "name": "Ciruela Umeboshi",
                "desc": "wrinkled pickled red ume plum on a small ceramic dish with a pinch of salt crystals",
                "type": "pickled fruit",
            },
            {
                "name": "Seta Shiitake Seca",
                "desc": "dried shiitake mushroom cap, dark brown with star-shaped white cracking pattern on top",
                "type": "mushroom",
            },
            {
                "name": "Bambú Tierno",
                "desc": "freshly cut bamboo shoot cross-section, pale cream interior with concentric rings, earthy",
                "type": "vegetable",
            },
            {
                "name": "Raíz de Wasabi Silvestre",
                "desc": "knobbly wild wasabi rhizome, vibrant green, with a small grater beside it, forest floor",
                "type": "plant root",
            },
            {
                "name": "Alga del Río Sagrado",
                "desc": "translucent emerald-green sacred river algae in a small porcelain bowl of water, faintly glowing",
                "type": "aquatic plant",
            },
            {
                "name": "Pétalo de Sakura",
                "desc": "five delicate pink cherry blossom petals arranged on a lacquered black tray, dew drops",
                "type": "flower petal",
            },
            {
                "name": "Mora de Montaña",
                "desc": "deep purple mountain berries in a small woven bamboo basket, glistening",
                "type": "berry",
            },
            {
                "name": "Semilla de Loto",
                "desc": "sacred lotus seed pod dried and open, revealing round pale seeds inside the honeycomb structure",
                "type": "sacred plant",
            },
        ],
        "recipes": [
            {
                "name": "Onigiri de Ciervo Sagrado",
                "desc": (
                    "triangular rice onigiri wrapped in dark nori, filled with seasoned sacred deer meat, "
                    "served on a cedar leaf on a wooden shrine tray"
                ),
            },
            {
                "name": "Sopa Miso de Montaña",
                "desc": (
                    "mountain miso soup in a lacquered wooden bowl with tofu, shiitake and wakame seaweed, "
                    "chopsticks resting on the bowl rim, morning light"
                ),
            },
            {
                "name": "Mochi de Cerezo",
                "desc": (
                    "three pink sakura mochi rice cakes on a ceramic plate, wrapped in pickled cherry blossom leaves, "
                    "petals floating in background"
                ),
            },
            {
                "name": "Fideos Soba del Río Sagrado",
                "desc": (
                    "dark buckwheat soba noodles in a clear sacred river broth, with mountain scallions "
                    "and golden koi-shaped kamaboko, served in a deep lacquer bowl"
                ),
            },
            {
                "name": "Té de Ceremonia del Santuario",
                "desc": (
                    "matcha tea ceremony bowl with frothy green tea, a small lotus flower floating on top, "
                    "tatami mat and incense smoke in the background"
                ),
            },
        ],
    },
}

# ---------------------------------------------------------------------------
# PROMPT BUILDER
# ---------------------------------------------------------------------------

BASE_STYLE = (
    "fantasy RPG game concept art, hand-painted illustration style, "
    "detailed textures, warm natural lighting, 2D game art, "
    "clean composition, rich saturated colors, inventory item reference sheet style"
)


def build_prompt(item: dict, region_aesthetic: str, item_type: str) -> str:
    if item_type == "recipe":
        subject = f"A fantasy RPG game food dish called '{item['name']}': {item['desc']}"
        context = "served as a game recipe card illustration, appetizing, stylized"
    else:
        subject = (
            f"A fantasy RPG game item called '{item['name']}' "
            f"({item.get('type', 'consumable')}): {item['desc']}"
        )
        context = "isolated on a worn parchment background, item card illustration"

    return f"{subject}. {context}. {BASE_STYLE}. Region aesthetic: {region_aesthetic}."


# ---------------------------------------------------------------------------
# IMAGE GENERATION
# ---------------------------------------------------------------------------

def generate_and_save(client: "OpenAI", prompt: str, output_path: Path, dry_run: bool) -> bool:
    if dry_run:
        print(f"  [DRY RUN] Would generate: {output_path.name}")
        print(f"  Prompt: {prompt[:120]}...")
        return True

    if output_path.exists():
        print(f"  [SKIP] Already exists: {output_path.name}")
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
        print(f"  [OK] Saved: {output_path.name}")
        return True
    except Exception as exc:
        print(f"  [ERROR] {output_path.name}: {exc}")
        return False


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate Eteria game art references with DALL-E 3")
    parser.add_argument("--region", choices=list(REGIONS.keys()), help="Generate only this region")
    parser.add_argument("--only", choices=["consumables", "recipes"], help="Generate only this category")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling the API")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: Set OPENAI_API_KEY environment variable.")
        sys.exit(1)

    client = OpenAI(api_key=api_key) if not args.dry_run else None

    output_root = Path("art_references")
    output_root.mkdir(exist_ok=True)

    log = []
    regions_to_process = {args.region: REGIONS[args.region]} if args.region else REGIONS

    for region_name, region_data in regions_to_process.items():
        print(f"\n{'='*60}")
        print(f"Region: {region_name}")
        print(f"{'='*60}")

        aesthetic = region_data["aesthetic"]
        region_dir = output_root / region_name.lower()
        region_dir.mkdir(exist_ok=True)

        # — Consumables —
        if args.only != "recipes":
            consumables_dir = region_dir / "consumables"
            consumables_dir.mkdir(exist_ok=True)
            print(f"\nConsumables ({len(region_data['consumables'])} items):")

            for item in region_data["consumables"]:
                safe_name = item["name"].replace(" ", "_").replace("/", "-")
                output_path = consumables_dir / f"{safe_name}.png"
                prompt = build_prompt(item, aesthetic, "consumable")

                ok = generate_and_save(client, prompt, output_path, args.dry_run)
                log.append({
                    "region": region_name,
                    "category": "consumable",
                    "name": item["name"],
                    "type": item.get("type", ""),
                    "file": str(output_path),
                    "success": ok,
                })
                if not args.dry_run and ok:
                    time.sleep(1)  # respect rate limits

        # — Recipes —
        if args.only != "consumables":
            recipes_dir = region_dir / "recipes"
            recipes_dir.mkdir(exist_ok=True)
            print(f"\nRecipes ({len(region_data['recipes'])} items):")

            for item in region_data["recipes"]:
                safe_name = item["name"].replace(" ", "_").replace("/", "-")
                output_path = recipes_dir / f"{safe_name}.png"
                prompt = build_prompt(item, aesthetic, "recipe")

                ok = generate_and_save(client, prompt, output_path, args.dry_run)
                log.append({
                    "region": region_name,
                    "category": "recipe",
                    "name": item["name"],
                    "file": str(output_path),
                    "success": ok,
                })
                if not args.dry_run and ok:
                    time.sleep(1)

    # Save summary log
    log_path = output_root / "generation_log.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2))

    total = len(log)
    success = sum(1 for e in log if e["success"])
    print(f"\n{'='*60}")
    print(f"Done: {success}/{total} images generated")
    print(f"Output folder: {output_root.resolve()}")
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()
