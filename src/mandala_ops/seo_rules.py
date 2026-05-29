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

RISK_TERMS = [
    "guaranteed", "cure", "heal illness", "make money", "bring wealth",
    "treat disease", "祛病", "治病", "包治", "发财", "暴富", "必定", "保证",
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


def recommended_product_type(row: ProductRow) -> str:
    text = clean_text(" ".join([row.title, row.body_html, row.tags])).lower()
    if "bracelet" in text or "手链" in text:
        return "Bracelet"
    return "Apparel & Accessories > Jewelry > Charms & Pendants"


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


def recommended_meta_description(row: ProductRow) -> str:
    theme = title_case_theme(detect_theme(row.title, row.body_html, row.tags))
    if "Bracelet" in recommended_product_type(row):
        desc = (
            f"A {theme.lower()} beaded bracelet designed as meaningful crystal jewelry "
            "for everyday styling, mindful gifting, and soft layered looks."
        )
    else:
        desc = (
            f"A {theme} thangka pendant inspired by Tibetan art symbolism, designed "
            "as meaningful jewelry for mindful wearing, gifting, and reflection."
        )
    return desc[:158].rstrip()


def recommended_alt_text(row: ProductRow) -> str:
    return f"{recommended_title(row).split('|')[0].strip()} by Mandala Jewels"


def compliance_notes(row: ProductRow) -> str:
    text = clean_text(" ".join([row.title, row.body_html, row.seo_title, row.seo_description])).lower()
    found = [term for term in RISK_TERMS if term.lower() in text]
    notes = []
    if found:
        notes.append("Replace outcome-guarantee terms: " + ", ".join(found))
    if "kailash auras" in text or "冈仁波齐奥拉斯" in text:
        notes.append("Replace old brand term with Mandala Jewels")
    if contains_cjk(row.title):
        notes.append("Title contains Chinese; create English SEO title")
    if not row.product_type:
        notes.append("Missing product type")
    if not row.tags:
        notes.append("Missing tags")
    return "; ".join(notes) or "OK"


def listing_recommendation(row: ProductRow) -> str:
    notes = compliance_notes(row)
    if "outcome-guarantee" in notes or "Replace old brand" in notes:
        return "Fix Before Scaling"
    if "Title contains Chinese" in notes or "Missing" in notes:
        return "Needs SEO Cleanup"
    return "Can Scale"


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


def dedupe(items: Iterable[str]) -> list[str]:
    seen = set()
    output = []
    for item in items:
        if item and item not in seen:
            output.append(item)
            seen.add(item)
    return output
