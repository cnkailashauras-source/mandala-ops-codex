from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from typing import Iterable


DEITY_KEYWORDS = {
    "green tara": ["green tara", "绿度母", "tara"],
    "amitabha": ["amitabha", "阿弥陀", "无量光"],
    "avalokiteshvara": ["avalokiteshvara", "观音", "四臂观音"],
    "manjushri": ["manjushri", "文殊"],
    "akasagarbha": ["akasagarbha", "虚空藏"],
    "yellow jambhala": ["yellow jambhala", "jambhala", "黄财神", "财神"],
    "acala": ["acala", "不动明王"],
    "medicine buddha": ["medicine buddha", "药师佛"],
    "vairocana": ["vairocana", "mahavairocana", "大日如来"],
    "samantabhadra": ["samantabhadra", "普贤"],
    "mahasthamaprapta": ["mahasthamaprapta", "大势至"],
    "om mantra": ["om", "嗡", "六字真言", "mantra"],
}

OLD_BRAND_TERMS = ["KAILASH AURAS", "冈仁波齐奥拉斯"]

HIGH_RISK_TERMS = [
    "guaranteed",
    "cure",
    "heal",
    "bring wealth",
    "make money",
    "治病",
    "保证",
    "必定",
    "暴富",
    "发财",
]

ZODIAC_MAP = {
    "rat": ["rat", "鼠"],
    "ox & tiger": ["ox", "tiger", "牛", "虎"],
    "rabbit": ["rabbit", "兔"],
    "dragon & snake": ["dragon", "snake", "龙", "蛇"],
    "horse": ["horse", "马"],
    "sheep & monkey": ["sheep", "monkey", "goat", "羊", "猴"],
    "rooster": ["rooster", "鸡"],
    "dog & pig": ["dog", "pig", "狗", "猪"],
}

COMMERCIAL_JEWELRY_INCLUDE_TERMS = [
    "bracelet",
    "beaded bracelet",
    "crystal bracelet",
    "purple bracelet",
    "水晶",
    "紫晶",
    "串珠",
    "手链",
    "非洲翠",
    "石英质玉",
    "石英岩玉",
    "african green quartzite",
    "green quartzite",
    "natural green stone",
]

RELIGIOUS_EXCLUDE_TERMS = [
    "thangka",
    "唐卡",
    "buddha",
    "佛",
    "菩萨",
    "tara",
    "度母",
    "jambhala",
    "财神",
    "mantra",
    "真言",
    "佛眼",
]

CRYSTAL_BRACELET_TITLES = [
    ("薰衣草紫晶手链", "Lavender Crystal Beaded Bracelet | Stackable Purple Jewelry"),
    ("黑曜紫光水晶手链", "Obsidian Glow Beaded Bracelet | Black & Purple Crystal Jewelry"),
    ("柔雾丁香紫串珠手链", "Soft Lilac Beaded Bracelet | Delicate Purple Crystal Jewelry"),
    ("月影紫水晶串珠手链", "Moonlit Violet Beaded Bracelet | Stackable Crystal Bracelet"),
    ("暮色紫晶串珠手链", "Twilight Purple Beaded Bracelet | Stackable Purple Jewelry"),
    ("紫晶串珠手链", "Violet Beaded Bracelet | Everyday Purple Crystal Jewelry"),
]

AFRICAN_GREEN_QUARTZITE_TITLES = [
    ("非洲翠手串", "African Green Quartzite Beaded Bracelet | Natural Green Stone Jewelry"),
    ("非洲翠平安扣吊坠", "African Green Quartzite Peace Buckle Pendant | Natural Green Stone Necklace"),
    ("非洲翠耳坠", "African Green Quartzite Drop Earrings | Natural Green Stone Jewelry"),
    ("非洲翠戒圈", "African Green Quartzite Ring | Minimal Green Stone Jewelry"),
    ("非洲翠葫芦吊坠", "African Green Quartzite Hulu Pendant | Natural Green Stone Necklace"),
]


@dataclass
class ProductRow:
    handle: str = ""
    title: str = ""
    body_html: str = ""
    vendor: str = ""
    product_type: str = ""
    tags: str = ""
    status: str = ""
    sku: str = ""
    price: str = ""
    image_src: str = ""
    image_alt_text: str = ""
    seo_title: str = ""
    seo_description: str = ""


def clean_text(value: str | None) -> str:
    text = unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def contains_term(text: str, term: str) -> bool:
    if re.search(r"[a-zA-Z]", term):
        if term == "heal":
            pattern = r"\bheal(?:s|ed|ing)?\b"
        elif term == "cure":
            pattern = r"\bcure(?:s|d)?\b"
        else:
            pattern = rf"\b{re.escape(term)}\b"
        return bool(re.search(pattern, text, flags=re.IGNORECASE))
    return term in text


def detect_theme(*parts: str) -> str:
    haystack = " ".join(clean_text(p).lower() for p in parts)
    for theme, keys in DEITY_KEYWORDS.items():
        if any(k.lower() in haystack for k in keys):
            return theme
    if any(k in haystack for k in ["amethyst", "purple", "紫"]):
        return "purple crystal"
    if any(k in haystack for k in ["bracelet", "手链", "beaded"]):
        return "beaded crystal"
    return "tibetan thangka"


def product_text(row: ProductRow) -> str:
    return clean_text(
        " ".join(
            [
                row.handle,
                row.title,
                row.body_html,
                row.product_type,
                row.tags,
                row.image_alt_text,
                row.seo_title,
                row.seo_description,
            ]
        )
    )


def is_religious_or_cultural_item(row: ProductRow) -> bool:
    text = product_text(row).lower()
    return any(contains_term(text, term.lower()) for term in RELIGIOUS_EXCLUDE_TERMS)


def is_commercial_jewelry_candidate(row: ProductRow) -> bool:
    text = product_text(row).lower()
    return any(contains_term(text, term.lower()) for term in COMMERCIAL_JEWELRY_INCLUDE_TERMS)


def is_african_green_quartzite(row: ProductRow) -> bool:
    text = product_text(row).lower()
    return any(
        term in text
        for term in [
            "非洲翠",
            "石英质玉",
            "石英岩玉",
            "african green quartzite",
            "green quartzite",
            "natural green stone",
        ]
    )


def is_crystal_bracelet(row: ProductRow) -> bool:
    if is_african_green_quartzite(row):
        return False
    text = product_text(row).lower()
    return any(
        term in text
        for term in [
            "bracelet",
            "beaded bracelet",
            "crystal bracelet",
            "purple bracelet",
            "水晶",
            "紫晶",
            "串珠",
            "手链",
        ]
    )


def commercial_focus_category(row: ProductRow) -> str:
    if is_religious_or_cultural_item(row):
        return "Excluded Religious Item"
    if is_african_green_quartzite(row):
        return "African Green Quartzite"
    if is_crystal_bracelet(row):
        return "Crystal Bracelet"
    if is_commercial_jewelry_candidate(row):
        return "Other"
    return "Other"


def commercial_priority(row: ProductRow) -> str:
    category = commercial_focus_category(row)
    if category == "Excluded Religious Item":
        return "Skip"
    if category == "Crystal Bracelet":
        return "High"
    if category == "African Green Quartzite":
        text = product_text(row).lower()
        if any(term in text for term in ["bracelet", "beaded", "手串", "手链"]):
            return "High"
        return "Medium"
    return "Low"


def detect_zodiac(*parts: str) -> str:
    haystack = " ".join(clean_text(p).lower() for p in parts)
    for sign, keys in ZODIAC_MAP.items():
        if any(k.lower() in haystack for k in keys):
            return sign
    return ""


def price_bucket(price: str) -> str:
    try:
        value = float(str(price).replace("$", "").strip())
    except ValueError:
        return "Needs Price"
    if value < 150:
        return "Under 150"
    if value < 300:
        return "150-300"
    if value < 700:
        return "300-700"
    return "700 Plus"


def gift_price_collection(price: str) -> str:
    try:
        value = float(str(price).replace("$", "").strip())
    except ValueError:
        return ""
    if value < 150:
        return "Gifts Under $150"
    if value < 300:
        return "Gifts Under $300"
    return ""


def title_case_theme(theme: str) -> str:
    special = {
        "green tara": "Green Tara",
        "amitabha": "Amitābha",
        "avalokiteshvara": "Avalokiteshvara",
        "manjushri": "Manjushri",
        "akasagarbha": "Akasagarbha",
        "yellow jambhala": "Yellow Jambhala",
        "acala": "Acala",
        "medicine buddha": "Medicine Buddha",
        "vairocana": "Vairocana",
        "samantabhadra": "Samantabhadra",
        "mahasthamaprapta": "Mahasthamaprapta",
        "om mantra": "Om Mantra",
        "purple crystal": "Purple Crystal",
        "beaded crystal": "Beaded Crystal",
        "tibetan thangka": "Tibetan Thangka",
    }
    return special.get(theme, theme.title())


def recommended_title(row: ProductRow) -> str:
    theme = detect_theme(row.title, row.body_html, row.tags)
    nice = title_case_theme(theme)
    if "bracelet" in clean_text(row.title).lower() or "crystal" in theme:
        return f"{nice} Beaded Bracelet | Meaningful Crystal Jewelry"
    return f"{nice} Thangka Pendant Necklace | Wearable Tibetan Art Jewelry"


def commercial_recommended_title(row: ProductRow) -> str:
    title = clean_text(row.title)
    for source, recommendation in CRYSTAL_BRACELET_TITLES + AFRICAN_GREEN_QUARTZITE_TITLES:
        if source in title:
            return recommendation

    if is_african_green_quartzite(row):
        lowered = product_text(row).lower()
        if any(term in lowered for term in ["earring", "earrings", "耳坠", "耳环"]):
            if "平安扣" in product_text(row):
                return "African Green Quartzite Peace Buckle Earrings | Natural Green Stone Jewelry"
            if "耳钉" in product_text(row):
                return "African Green Quartzite Stud Earrings | Natural Green Stone Jewelry"
            return "African Green Quartzite Drop Earrings | Natural Green Stone Jewelry"
        if any(term in lowered for term in ["ring", "戒圈", "戒指"]):
            return "African Green Quartzite Ring | Minimal Green Stone Jewelry"
        if any(term in lowered for term in ["bracelet", "beaded", "手串", "手链"]):
            return "African Green Quartzite Beaded Bracelet | Natural Green Stone Jewelry"
        if "平安扣" in product_text(row):
            return "African Green Quartzite Peace Buckle Pendant | Natural Green Stone Necklace"
        if "无事牌" in product_text(row):
            return "African Green Quartzite Tablet Pendant | Minimal Green Stone Necklace"
        if "圆珠吊坠" in product_text(row):
            return "African Green Quartzite Round Bead Pendant | Natural Green Stone Necklace"
        return "African Green Quartzite Pendant | Natural Green Stone Necklace"

    if is_crystal_bracelet(row):
        lowered = product_text(row).lower()
        if any(term in lowered for term in ["obsidian", "black"]) or "黑" in title:
            return "Obsidian Glow Beaded Bracelet | Black & Purple Crystal Jewelry"
        if "twilight" in lowered or "暮色" in title:
            return "Twilight Purple Beaded Bracelet | Stackable Purple Jewelry"
        if "moonlit" in lowered or "月影" in title:
            return "Moonlit Violet Beaded Bracelet | Stackable Crystal Bracelet"
        if "soft-lilac" in lowered or "soft lilac" in lowered or "柔雾丁香" in title:
            return "Soft Lilac Beaded Bracelet | Delicate Purple Crystal Jewelry"
        if "lavender" in lowered or "薰衣草" in title:
            return "Lavender Crystal Beaded Bracelet | Stackable Purple Jewelry"
        return "Violet Beaded Bracelet | Everyday Purple Crystal Jewelry"

    return recommended_title(row)


def recommended_product_type(row: ProductRow) -> str:
    text = clean_text(" ".join([row.title, row.body_html, row.tags])).lower()
    if "bracelet" in text or "手链" in text:
        return "Bracelet"
    if any(k in text for k in ["earring", "earrings", "耳坠", "耳环"]):
        return "Earrings"
    if any(k in text for k in ["ring", "戒圈", "戒指"]):
        return "Ring"
    return "Apparel & Accessories > Jewelry > Charms & Pendants"


def commercial_recommended_product_type(row: ProductRow) -> str:
    category = commercial_focus_category(row)
    if category == "Crystal Bracelet":
        return "Bracelet"
    if category == "African Green Quartzite":
        text = product_text(row).lower()
        if any(k in text for k in ["earring", "earrings", "耳坠", "耳环"]):
            return "Earrings"
        if any(k in text for k in ["ring", "戒圈", "戒指"]):
            return "Ring"
        if any(k in text for k in ["bracelet", "beaded", "手串", "手链"]):
            return "Bracelet"
        return "Apparel & Accessories > Jewelry > Necklaces"
    return recommended_product_type(row)


def recommended_tags(row: ProductRow) -> list[str]:
    theme = detect_theme(row.title, row.body_html, row.tags)
    zodiac = detect_zodiac(row.title, row.body_html, row.tags)
    bucket = price_bucket(row.price)

    tags = [
        "Mandala Jewels",
        "Meaningful Jewelry",
        "Spiritual Jewelry",
        bucket,
        "Needs SEO Review",
    ]

    if "crystal" in theme or "bracelet" in clean_text(row.title).lower():
        tags.extend(["Crystal Bracelet", "Beaded Bracelet", "Gift For Her", "Pinterest Ready"])
    else:
        tags.extend(["Tibetan Jewelry", "Thangka Pendant", "Wearable Tibetan Art", "Mindful Gift"])

    if theme:
        tags.append(title_case_theme(theme))
    if zodiac:
        tags.extend(["Zodiac Guardian", f"Zodiac {zodiac.title()}"])

    return dedupe(tags)


def commercial_recommended_tags(row: ProductRow) -> list[str]:
    category = commercial_focus_category(row)
    if category == "Crystal Bracelet":
        return [
            "Mandala Jewels",
            "Crystal Bracelet",
            "Beaded Bracelet",
            "Purple Bracelet",
            "Stackable Bracelet",
            "Gift For Her",
            "Everyday Jewelry",
            "Minimal Jewelry",
            "Pinterest Ready",
            "TikTok Ready",
        ]
    if category == "African Green Quartzite":
        tags = [
            "Mandala Jewels",
            "African Green Quartzite",
            "Green Quartzite Jewelry",
            "Natural Green Stone",
            "Green Stone Jewelry",
            "Gift For Her",
            "Pinterest Ready",
            "TikTok Ready",
        ]
        product_type = commercial_recommended_product_type(row)
        if product_type == "Bracelet":
            tags.append("Beaded Bracelet")
        elif product_type == "Earrings":
            tags.append("Earrings")
        elif product_type == "Ring":
            tags.append("Ring")
        else:
            tags.append("Pendant Necklace")
        return dedupe(tags)
    return recommended_tags(row)


def recommended_meta_description(row: ProductRow) -> str:
    theme = title_case_theme(detect_theme(row.title, row.body_html, row.tags))
    article = "An" if theme[:1].lower() in {"a", "e", "i", "o", "u"} else "A"
    if "Bracelet" in recommended_product_type(row):
        desc = (
            f"{article} {theme.lower()} beaded bracelet designed as meaningful crystal jewelry "
            "for everyday styling, mindful gifting, and soft layered looks."
        )
    else:
        desc = (
            f"{article} {theme} thangka pendant inspired by Tibetan art symbolism, designed "
            "as meaningful jewelry for mindful wearing, gifting, and reflection."
        )
    return desc[:158].rstrip()


def commercial_recommended_meta_description(row: ProductRow) -> str:
    category = commercial_focus_category(row)
    if category == "Crystal Bracelet":
        desc = (
            "A stackable purple crystal beaded bracelet designed for everyday styling, "
            "easy gifting, and soft minimal jewelry looks."
        )
    elif category == "African Green Quartzite":
        desc = (
            "African Green Quartzite jewelry with a natural green stone look, using cautious "
            "quartzite wording for everyday outfits, gifting, and minimal styling."
        )
    elif category == "Excluded Religious Item":
        desc = (
            "A cultural jewelry piece suitable for storytelling content, collection pages, "
            "and education-led discovery rather than first-wave product feed optimization."
        )
    else:
        return recommended_meta_description(row)
    return desc[:158].rstrip()


def recommended_alt_text(row: ProductRow) -> str:
    return f"{recommended_title(row).split('|')[0].strip()} by Mandala Jewels"


def commercial_recommended_alt_text(row: ProductRow) -> str:
    return f"{commercial_recommended_title(row).split('|')[0].strip()} by Mandala Jewels"


def compliance_notes(row: ProductRow) -> str:
    text = clean_text(
        " ".join(
            [
                row.title,
                row.body_html,
                row.tags,
                row.image_alt_text,
                row.seo_title,
                row.seo_description,
            ]
        )
    )
    lowered = text.lower()
    found_risk_terms = [term for term in HIGH_RISK_TERMS if contains_term(lowered, term.lower())]
    found_old_brand_terms = [term for term in OLD_BRAND_TERMS if contains_term(lowered, term.lower())]
    notes = []
    if found_old_brand_terms:
        notes.append("Old brand term found: " + ", ".join(found_old_brand_terms))
    if found_risk_terms:
        notes.append("High-risk compliance terms: " + ", ".join(found_risk_terms))
    if contains_cjk(row.title):
        notes.append("Title contains Chinese; create English SEO title")
    if not row.product_type:
        notes.append("Missing product type")
    if not row.tags:
        notes.append("Missing tags")
    return "; ".join(notes) or "OK"


def commercial_compliance_notes(row: ProductRow) -> str:
    if commercial_focus_category(row) == "Excluded Religious Item":
        return "Religious/cultural item, do not force commercial Google feed optimization"
    return compliance_notes(row)


def listing_recommendation(row: ProductRow) -> str:
    notes = compliance_notes(row)
    if "High-risk compliance terms" in notes or "Old brand term found" in notes:
        return "Fix Before Scaling"
    if "Title contains Chinese" in notes or "Missing" in notes:
        return "Needs SEO Cleanup"
    return "Can Scale"


def commercial_listing_recommendation(row: ProductRow) -> str:
    category = commercial_focus_category(row)
    if category == "Excluded Religious Item":
        return "Content Only / Skip Google Merchant First"
    if commercial_priority(row) in {"High", "Medium"}:
        return "Optimize for Commercial SEO / Google Merchant Review"
    return "Not First Commercial Batch"


def collection_candidates(row: ProductRow) -> list[str]:
    theme = detect_theme(row.title, row.body_html, row.tags)
    bucket = price_bucket(row.price)
    collections = []
    if "Bracelet" in recommended_product_type(row):
        collections += ["Beaded Crystal Bracelets", "Meaningful Gifts for Her"]
        if theme == "purple crystal":
            collections.append("Purple Crystal Bracelets")
    else:
        collections += ["Tibetan Thangka Pendants", "Spiritual Necklaces"]
        if detect_zodiac(row.title, row.body_html, row.tags):
            collections.append("Zodiac Guardian Jewelry")
        if theme == "green tara":
            collections.append("Green Tara Jewelry")
        if "buddha" in theme or "eye" in clean_text(row.title).lower():
            collections.append("Buddha Eye Pendants")
        if "jambhala" in theme:
            collections.append("Jambhala Wealth Jewelry")
        if bucket == "Under 150":
            collections.append("Gifts Under $150")
        if bucket == "700 Plus":
            collections.append("Heirloom Thangka Jewelry")
    return dedupe(collections)


def commercial_collection_candidates(row: ProductRow) -> list[str]:
    category = commercial_focus_category(row)
    if category == "Crystal Bracelet":
        collections = [
            "Beaded Crystal Bracelets",
            "Purple Crystal Bracelets",
            "Stackable Bracelets",
        ]
        gift_collection = gift_price_collection(row.price)
        if gift_collection:
            collections.append(gift_collection)
        collections.append("Meaningful Gifts for Her")
        return dedupe(collections)
    if category == "African Green Quartzite":
        product_type = commercial_recommended_product_type(row)
        collections = [
            "African Green Quartzite Jewelry",
            "Green Stone Jewelry",
        ]
        if product_type == "Bracelet":
            collections.append("Green Stone Bracelets")
        elif product_type != "Earrings" and product_type != "Ring":
            collections.append("Natural Stone Pendants")
        collections.append("Gift Jewelry")
        return dedupe(collections)
    if category == "Excluded Religious Item":
        return ["Content Only", "Cultural Jewelry Stories"]
    return collection_candidates(row)


def dedupe(items: Iterable[str]) -> list[str]:
    seen = set()
    output = []
    for item in items:
        if item and item not in seen:
            output.append(item)
            seen.add(item)
    return output
