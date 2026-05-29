from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContentItem:
    content_type: str
    title: str
    primary_keyword: str
    target_collection: str
    repurpose: str


CORE_CONTENT_PLAN = [
    ContentItem("Blog", "What Is Thangka Jewelry? A Guide to Wearable Tibetan Art", "thangka jewelry", "Tibetan Thangka Pendants", "5 Pinterest pins, 2 Reels, 1 TikTok script"),
    ContentItem("Blog", "Green Tara Meaning in Tibetan Art and Jewelry", "Green Tara pendant", "Green Tara Jewelry", "Symbol explainer carousel, short video, product pin"),
    ContentItem("Blog", "Buddha Eye Symbol Meaning: Wisdom and Awareness in Tibetan Art", "Buddha eye pendant", "Buddha Eye Pendants", "Pinterest infographic, TikTok voiceover"),
    ContentItem("Blog", "Chinese Zodiac Guardian Jewelry: A Cultural Guide", "zodiac guardian jewelry", "Zodiac Guardian Jewelry", "12 zodiac pins, 3 short videos"),
    ContentItem("Blog", "How to Choose a Meaningful Spiritual Necklace as a Gift", "meaningful spiritual necklace", "Meaningful Gifts for Her", "Gift guide pins, Instagram carousel"),
    ContentItem("Blog", "How to Style Tibetan Pendant Necklaces for Everyday Wear", "Tibetan pendant necklace", "Spiritual Necklaces", "Outfit reels, Pinterest style board"),
    ContentItem("Blog", "Amethyst Beaded Bracelets: Color, Styling, and Gift Meaning", "amethyst beaded bracelet", "Purple Crystal Bracelets", "Bracelet styling reels, pin set"),
    ContentItem("Blog", "How to Care for Hand-Painted Thangka Pendants", "care for thangka pendant", "Tibetan Thangka Pendants", "FAQ pin, care guide reel"),
]


def rows() -> list[dict[str, str]]:
    return [item.__dict__ for item in CORE_CONTENT_PLAN]
