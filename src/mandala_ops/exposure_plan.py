from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path


OUTPUT_FIELDS = [
    "Date",
    "Platform",
    "Product Handle",
    "Product Title",
    "Content Angle",
    "Hook",
    "Script / Caption",
    "CTA",
    "Hashtags",
    "UTM URL",
    "Asset Needed",
    "Status",
]

SAFE_ANGLES = [
    "everyday jewelry",
    "stackable bracelet",
    "gift for her",
    "purple bracelet",
    "green stone jewelry",
    "minimalist styling",
    "outfit detail",
    "natural stone accessory",
]

BLOCKED_TERMS = [
    "healing",
    "heal",
    "cure",
    "guaranteed protection",
    "bring wealth",
    "make money",
    "jade",
]


def read_products(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def eligible_products(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    products = []
    for row in rows:
        priority = row.get("Priority", "").strip()
        category = row.get("Focus Category", "").strip()
        if priority not in {"High", "Medium"}:
            continue
        if priority == "Skip" or category == "Excluded Religious Item":
            continue
        products.append(row)
    return products


def product_title(row: dict[str, str]) -> str:
    return row.get("Recommended Title") or row.get("Title") or row.get("Product Title") or row.get("Handle", "")


def focus_category(row: dict[str, str]) -> str:
    return row.get("Focus Category", "")


def content_angles(row: dict[str, str]) -> list[str]:
    if focus_category(row) == "Crystal Bracelet":
        return ["purple bracelet", "stackable bracelet", "gift for her", "everyday jewelry", "outfit detail"]
    if focus_category(row) == "African Green Quartzite":
        return ["green stone jewelry", "natural stone accessory", "minimalist styling", "everyday jewelry", "gift for her"]
    return ["everyday jewelry", "minimalist styling", "outfit detail"]


def hashtags(row: dict[str, str]) -> str:
    if focus_category(row) == "Crystal Bracelet":
        tags = [
            "#MandalaJewels",
            "#CrystalBracelet",
            "#PurpleBracelet",
            "#BeadedBracelet",
            "#StackableBracelet",
            "#GiftForHer",
            "#EverydayJewelry",
        ]
    elif focus_category(row) == "African Green Quartzite":
        tags = [
            "#MandalaJewels",
            "#AfricanGreenQuartzite",
            "#GreenQuartziteJewelry",
            "#GreenStoneJewelry",
            "#NaturalStoneAccessory",
            "#MinimalJewelry",
            "#GiftJewelry",
        ]
    else:
        tags = ["#MandalaJewels", "#EverydayJewelry", "#MinimalJewelry"]
    return " ".join(tags)


def utm_url(handle: str, platform: str, angle: str) -> str:
    source = platform.lower().replace("/", "_").replace(" ", "_")
    content = angle.lower().replace(" ", "_")
    return (
        f"https://mandalajewelshop.com/products/{handle}"
        f"?utm_source={source}&utm_medium=organic_social"
        f"&utm_campaign=active_exposure&utm_content={content}"
    )


def sanitize_copy(text: str) -> str:
    output = text.replace("Jade", "Green Quartzite").replace("jade", "green quartzite")
    risky_replacements = {
        "healing": "styling",
        "heal": "style",
        "cure": "refresh",
        "guaranteed protection": "everyday meaning",
        "bring wealth": "complete the outfit",
        "make money": "style confidently",
    }
    for term, replacement in risky_replacements.items():
        output = output.replace(term, replacement).replace(term.title(), replacement.title())
    return output


def hook_for(row: dict[str, str], platform: str, angle: str, index: int) -> str:
    category = focus_category(row)
    if category == "Crystal Bracelet":
        hooks = [
            "A small purple bracelet detail that changes the whole outfit",
            "Three ways to style a stackable purple bracelet",
            "The everyday bracelet that makes a simple look feel finished",
        ]
    elif category == "African Green Quartzite":
        hooks = [
            "A natural green stone detail for simple everyday outfits",
            "How to style African Green Quartzite without overthinking it",
            "A minimal green stone accessory for soft, polished looks",
        ]
    else:
        hooks = [
            "A quiet jewelry detail for everyday styling",
            "A minimal accessory idea for this week",
            "One small piece, three outfit moods",
        ]
    if platform == "Pinterest":
        return hooks[index % len(hooks)].replace("How to ", "")
    return hooks[index % len(hooks)]


def script_for(row: dict[str, str], platform: str, angle: str, index: int) -> str:
    title = product_title(row)
    category = focus_category(row)
    if category == "Crystal Bracelet":
        base = (
            f"Show {title} on wrist, then layer it with a watch, a neutral knit, and a simple ring. "
            f"Keep the focus on {angle}: soft color, easy stacking, and everyday jewelry styling."
        )
    elif category == "African Green Quartzite":
        base = (
            f"Show {title} in natural light, then pair it with white, denim, and warm neutrals. "
            f"Describe it as African Green Quartzite / Green Quartzite Jewelry with a natural green stone look."
        )
    else:
        base = f"Show {title} as a small outfit detail, then style it with a clean everyday look."

    if platform == "Pinterest":
        return f"{title} styled as {angle}. Save this idea for simple everyday jewelry inspiration."
    if platform == "Instagram":
        return f"{title} for {angle}. A small jewelry detail for outfits that need one soft finishing touch."
    return base


def cta_for(platform: str) -> str:
    if platform == "Pinterest":
        return "Save this jewelry styling idea"
    if platform == "Instagram":
        return "Tap to shop or save for later"
    return "Shop the piece or save the styling idea"


def asset_for(platform: str, row: dict[str, str]) -> str:
    if platform in {"TikTok/Reels", "YouTube Shorts"}:
        return "Vertical product video: wrist/neck/ear close-up, outfit styling, natural light"
    if platform == "Pinterest":
        return "Vertical pin image: product close-up plus outfit detail"
    return "Square or vertical lifestyle image with product detail"


def build_rows(products: list[dict[str, str]], days: int = 30, start: date | None = None) -> list[dict[str, str]]:
    start_date = start or date.today()
    rows: list[dict[str, str]] = []
    cadence = [
        ("TikTok/Reels", 3),
        ("YouTube Shorts", 3),
        ("Pinterest", 5),
        ("Instagram", 2),
    ]
    post_index = 0

    for product in products:
        handle = product.get("Handle", "")
        title = product_title(product)
        angles = content_angles(product)
        for platform, count in cadence:
            for index in range(count):
                angle = angles[(index + post_index) % len(angles)]
                scheduled = start_date + timedelta(days=post_index % max(days, 1))
                row = {
                    "Date": scheduled.isoformat(),
                    "Platform": platform,
                    "Product Handle": handle,
                    "Product Title": title,
                    "Content Angle": angle,
                    "Hook": hook_for(product, platform, angle, index),
                    "Script / Caption": script_for(product, platform, angle, index),
                    "CTA": cta_for(platform),
                    "Hashtags": hashtags(product),
                    "UTM URL": utm_url(handle, platform, angle),
                    "Asset Needed": asset_for(platform, product),
                    "Status": "Draft",
                }
                rows.append({key: sanitize_copy(value) for key, value in row.items()})
                post_index += 1
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str] = OUTPUT_FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_exposure_plan(input_path: Path, output_path: Path, days: int = 30) -> list[dict[str, str]]:
    products = eligible_products(read_products(input_path))
    rows = build_rows(products, days=days)
    write_csv(output_path, rows)
    return rows


def write_channel_plans(rows: list[dict[str, str]], pinterest_path: Path, short_video_path: Path) -> None:
    pinterest_rows = [row for row in rows if row["Platform"] == "Pinterest"]
    short_video_rows = [row for row in rows if row["Platform"] in {"TikTok/Reels", "YouTube Shorts"}]
    write_csv(pinterest_path, pinterest_rows)
    write_csv(short_video_path, short_video_rows)
