from __future__ import annotations

import csv
from pathlib import Path


TRACKER_FIELDS = [
    "Platform",
    "Handle",
    "Niche",
    "Follower Range",
    "Avg Views",
    "Country",
    "Contact Method",
    "Fit Score",
    "Product Match",
    "Outreach Status",
    "Gifted Product",
    "Discount Code",
    "Affiliate Code",
    "FTC Disclosure Required",
]

DM_FIELDS = ["Template Name", "Platform", "Message", "Compliance Notes"]

DISCLOSURE_TEXT = (
    "Please disclose that the item was gifted by Mandala Jewels, use #ad when required, "
    "and mention any affiliate link or commission if applicable."
)


def seed_rows() -> list[dict[str, str]]:
    return [
        {
            "Platform": "TikTok",
            "Handle": "",
            "Niche": "micro creator / everyday jewelry styling",
            "Follower Range": "5k-50k",
            "Avg Views": "",
            "Country": "US",
            "Contact Method": "Manual review",
            "Fit Score": "",
            "Product Match": "Crystal Bracelet / African Green Quartzite",
            "Outreach Status": "Prospect",
            "Gifted Product": "",
            "Discount Code": "",
            "Affiliate Code": "",
            "FTC Disclosure Required": "Yes",
        },
        {
            "Platform": "Instagram",
            "Handle": "",
            "Niche": "minimal styling / outfit detail",
            "Follower Range": "5k-100k",
            "Avg Views": "",
            "Country": "US",
            "Contact Method": "Manual review",
            "Fit Score": "",
            "Product Match": "Purple Bracelet",
            "Outreach Status": "Prospect",
            "Gifted Product": "",
            "Discount Code": "",
            "Affiliate Code": "",
            "FTC Disclosure Required": "Yes",
        },
        {
            "Platform": "Pinterest",
            "Handle": "",
            "Niche": "gift guides / jewelry boards",
            "Follower Range": "Any engaged account",
            "Avg Views": "",
            "Country": "US",
            "Contact Method": "Manual review",
            "Fit Score": "",
            "Product Match": "Gift Jewelry",
            "Outreach Status": "Prospect",
            "Gifted Product": "",
            "Discount Code": "",
            "Affiliate Code": "",
            "FTC Disclosure Required": "Yes",
        },
    ]


def dm_templates() -> list[dict[str, str]]:
    templates = [
        (
            "TikTok micro creator",
            "TikTok",
            "Hi {first_name}, I liked your everyday styling videos. Mandala Jewels is seeding a few purple crystal bracelets and African Green Quartzite pieces for creators who enjoy simple outfit details. Would you be open to receiving a gifted piece with no requirement for a positive review? If you share content, please disclose that it was gifted by Mandala Jewels, use #ad when required, and mention any affiliate link or commission if applicable.",
        ),
        (
            "Instagram styling creator",
            "Instagram",
            "Hi {first_name}, your minimal outfit styling feels like a lovely fit for Mandala Jewels. We are looking for creators to style a gifted bracelet or green stone jewelry piece in everyday looks. There is no request for a scripted or false review. If you post, please disclose that it was gifted by Mandala Jewels, use #ad when required, and mention any affiliate link or commission if applicable.",
        ),
        (
            "Pinterest creator",
            "Pinterest",
            "Hi {first_name}, we are preparing jewelry styling ideas for Pinterest around stackable bracelets, gift jewelry, and natural green stone accessories. Would you be interested in reviewing a gifted Mandala Jewels piece for possible styling content? Any post should disclose that it was gifted by Mandala Jewels, use #ad when required, and mention any affiliate link or commission if applicable.",
        ),
        (
            "UGC creator",
            "UGC",
            "Hi {first_name}, Mandala Jewels is looking for UGC creators who can film clean product close-ups, outfit details, and simple styling clips. We can provide a gifted product for review, but we do not ask for false praise or guarantee any earnings. Please disclose that it was gifted by Mandala Jewels, use #ad when required, and mention any affiliate link or commission if applicable.",
        ),
        (
            "Follow-up message",
            "Any",
            "Hi {first_name}, just following up on my note about a possible Mandala Jewels gifted product collaboration. No pressure if it is not a fit. If you do choose to share content, please disclose that it was gifted by Mandala Jewels, use #ad when required, and mention any affiliate link or commission if applicable.",
        ),
    ]
    return [
        {
            "Template Name": name,
            "Platform": platform,
            "Message": message,
            "Compliance Notes": DISCLOSURE_TEXT,
        }
        for name, platform, message in templates
    ]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_tracker(path: Path) -> None:
    write_csv(path, seed_rows(), TRACKER_FIELDS)


def write_seed_template(path: Path) -> None:
    write_csv(path, seed_rows(), TRACKER_FIELDS)


def write_dm_template_csv(path: Path) -> list[dict[str, str]]:
    rows = dm_templates()
    write_csv(path, rows, DM_FIELDS)
    return rows


def write_dm_template_markdown(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sections = ["# Creator Outreach DM Templates", ""]
    for row in dm_templates():
        sections.extend(
            [
                f"## {row['Template Name']}",
                "",
                f"Platform: {row['Platform']}",
                "",
                row["Message"],
                "",
                f"Compliance: {row['Compliance Notes']}",
                "",
            ]
        )
    path.write_text("\n".join(sections), encoding="utf-8")
