from __future__ import annotations

import csv
import re
from pathlib import Path


IMAGE_FIELDS = [
    "Job ID",
    "Source Date",
    "Platform",
    "Product Handle",
    "Product Title",
    "Content Angle",
    "Asset Type",
    "Aspect Ratio",
    "Image Prompt",
    "Negative Prompt",
    "Reference Image Needed",
    "Model Suggestion",
    "Status",
]

VIDEO_FIELDS = [
    "Job ID",
    "Source Date",
    "Platform",
    "Product Handle",
    "Product Title",
    "Content Angle",
    "Asset Type",
    "Aspect Ratio",
    "Duration Seconds",
    "Video Prompt",
    "Shot List",
    "On-screen Text",
    "Voiceover",
    "Model Suggestion",
    "Status",
]

EDIT_FIELDS = [
    "Edit ID",
    "Source Video Job ID",
    "Platform",
    "Product Handle",
    "Product Title",
    "Aspect Ratio",
    "Duration Seconds",
    "Edit Structure",
    "Caption Text",
    "Music Direction",
    "Required Assets",
    "Export Filename",
    "Status",
]

REVIEW_FIELDS = [
    "Asset ID",
    "Asset Type",
    "Platform",
    "Product Handle",
    "Product Title",
    "Content Angle",
    "Prompt Summary",
    "Generated Asset Path",
    "Review Status",
    "Compliance Check",
    "Notes",
]

BLOCKED_TERMS = [
    "healing",
    "heal",
    "cure",
    "guaranteed protection",
    "bring wealth",
    "make money",
    "jade",
    "jadeite",
]


def read_calendar(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def safe_text(value: str) -> str:
    text = value.replace("Jade", "Green Quartzite").replace("jadeite", "quartzite").replace("jade", "green quartzite")
    replacements = {
        "healing": "styling",
        "heal": "style",
        "cure": "refresh",
        "guaranteed protection": "everyday meaning",
        "bring wealth": "complete the outfit",
        "make money": "style confidently",
    }
    for source, replacement in replacements.items():
        if source.isalpha():
            text = re.sub(rf"\b{re.escape(source)}\b", replacement, text, flags=re.IGNORECASE)
        else:
            text = text.replace(source, replacement).replace(source.title(), replacement.title())
    return text


def category_for(row: dict[str, str]) -> str:
    text = " ".join(
        [
            row.get("Product Title", ""),
            row.get("Product Handle", ""),
            row.get("Hashtags", ""),
            row.get("Content Angle", ""),
        ]
    ).lower()
    if "african green quartzite" in text or "green quartzite" in text or "green stone" in text:
        return "African Green Quartzite"
    if "purple" in text or "crystal bracelet" in text or "beaded bracelet" in text:
        return "Crystal Bracelet"
    return "Commercial Jewelry"


def image_asset_type(platform: str) -> str:
    if platform == "Pinterest":
        return "Pinterest Pin Image"
    if platform == "Instagram":
        return "Instagram Lifestyle Image"
    return "Product Reference Still"


def image_aspect_ratio(platform: str) -> str:
    if platform == "Pinterest":
        return "2:3"
    if platform == "Instagram":
        return "4:5"
    return "9:16"


def image_prompt(row: dict[str, str]) -> str:
    title = row.get("Product Title", "")
    angle = row.get("Content Angle", "")
    category = category_for(row)
    if category == "African Green Quartzite":
        material = "African Green Quartzite jewelry, natural green stone look, quartzite wording only"
        color = "soft green stone tones"
    elif category == "Crystal Bracelet":
        material = "purple crystal beaded bracelet"
        color = "lavender, violet, and soft purple tones"
    else:
        material = "minimal everyday jewelry"
        color = "neutral styling palette"
    prompt = (
        f"Photorealistic product lifestyle image for Mandala Jewels: {title}. "
        f"Show {material} as {angle}, styled with {color}, clean natural light, "
        "minimal outfit detail, elegant hands or flat lay, premium ecommerce composition, no religious symbols, no text overlay."
    )
    return safe_text(prompt)


def negative_prompt() -> str:
    return (
        "no medical claims, no wealth claims, no religious iconography, no exaggerated gemstones, "
        "no fake logo, no misspelled text, no misleading green stone material names"
    )


def video_prompt(row: dict[str, str]) -> str:
    title = row.get("Product Title", "")
    angle = row.get("Content Angle", "")
    category = category_for(row)
    if category == "African Green Quartzite":
        material = "African Green Quartzite / Green Quartzite Jewelry with a natural green stone look"
        styling = "white shirt, denim, warm neutral outfit, minimal styling"
    elif category == "Crystal Bracelet":
        material = "purple crystal beaded bracelet"
        styling = "neutral knit, simple ring, watch stack, soft everyday outfit"
    else:
        material = "minimal everyday jewelry"
        styling = "clean outfit detail and natural light"
    prompt = (
        f"Create a vertical short video for Mandala Jewels featuring {title}. "
        f"Show {material}; focus on {angle}. Use {styling}. "
        "Camera: macro close-up, wrist or neckline detail, gentle hand movement, outfit transition, natural window light. "
        "Tone: calm, modern, premium, organic social. Avoid claims about luck, wellness, protection, or money."
    )
    return safe_text(prompt)


def shot_list(row: dict[str, str]) -> str:
    return (
        "0-2s product close-up hook; 2-6s hand/wrist or outfit detail; "
        "6-10s styling transition; 10-14s final product hero shot with CTA-safe frame"
    )


def on_screen_text(row: dict[str, str]) -> str:
    return safe_text(f"{row.get('Hook', '')} | {row.get('CTA', '')}")


def voiceover(row: dict[str, str]) -> str:
    return safe_text(
        f"{row.get('Hook', '')}. Style it as {row.get('Content Angle', '')}. {row.get('CTA', '')}."
    )


def build_image_jobs(calendar_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    jobs = []
    for index, row in enumerate(calendar_rows, start=1):
        platform = row.get("Platform", "")
        if platform not in {"Pinterest", "Instagram", "TikTok/Reels", "YouTube Shorts"}:
            continue
        job_id = f"IMG-{index:04d}"
        jobs.append(
            {
                "Job ID": job_id,
                "Source Date": row.get("Date", ""),
                "Platform": platform,
                "Product Handle": row.get("Product Handle", ""),
                "Product Title": row.get("Product Title", ""),
                "Content Angle": row.get("Content Angle", ""),
                "Asset Type": image_asset_type(platform),
                "Aspect Ratio": image_aspect_ratio(platform),
                "Image Prompt": image_prompt(row),
                "Negative Prompt": negative_prompt(),
                "Reference Image Needed": "Yes - use real product photo when available",
                "Model Suggestion": "Image model or product-preserving image edit workflow",
                "Status": "Prompt Ready",
            }
        )
    return jobs


def build_video_jobs(calendar_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    jobs = []
    source_rows = [row for row in calendar_rows if row.get("Platform") in {"TikTok/Reels", "YouTube Shorts"}]
    for index, row in enumerate(source_rows, start=1):
        job_id = f"VID-{index:04d}"
        jobs.append(
            {
                "Job ID": job_id,
                "Source Date": row.get("Date", ""),
                "Platform": row.get("Platform", ""),
                "Product Handle": row.get("Product Handle", ""),
                "Product Title": row.get("Product Title", ""),
                "Content Angle": row.get("Content Angle", ""),
                "Asset Type": "AI Image-to-Video Clip",
                "Aspect Ratio": "9:16",
                "Duration Seconds": "14",
                "Video Prompt": video_prompt(row),
                "Shot List": shot_list(row),
                "On-screen Text": on_screen_text(row),
                "Voiceover": voiceover(row),
                "Model Suggestion": "Runway/Luma/Kling image-to-video after product image approval",
                "Status": "Prompt Ready",
            }
        )
    return jobs


def build_edit_plan(video_jobs: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for index, job in enumerate(video_jobs, start=1):
        edit_id = f"EDIT-{index:04d}"
        handle = job["Product Handle"]
        rows.append(
            {
                "Edit ID": edit_id,
                "Source Video Job ID": job["Job ID"],
                "Platform": job["Platform"],
                "Product Handle": handle,
                "Product Title": job["Product Title"],
                "Aspect Ratio": "9:16",
                "Duration Seconds": "15",
                "Edit Structure": "Hook frame, product close-up, outfit styling, final CTA, burned-in captions",
                "Caption Text": job["On-screen Text"],
                "Music Direction": "Soft modern lifestyle beat, low volume under captions",
                "Required Assets": "Approved product still, generated video clip, logo-free end frame, UTM link",
                "Export Filename": f"{handle}_{job['Platform'].lower().replace('/', '_').replace(' ', '_')}_{index:04d}.mp4",
                "Status": "Needs Generated Assets",
            }
        )
    return rows


def build_review_tracker(
    image_jobs: list[dict[str, str]], video_jobs: list[dict[str, str]], edit_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    rows = []
    for job in image_jobs:
        rows.append(
            {
                "Asset ID": job["Job ID"],
                "Asset Type": job["Asset Type"],
                "Platform": job["Platform"],
                "Product Handle": job["Product Handle"],
                "Product Title": job["Product Title"],
                "Content Angle": job["Content Angle"],
                "Prompt Summary": job["Image Prompt"][:180],
                "Generated Asset Path": "",
                "Review Status": "Needs Generation",
                "Compliance Check": "No claims; no religious symbols; product appearance must be reviewed",
                "Notes": "",
            }
        )
    for job in video_jobs:
        rows.append(
            {
                "Asset ID": job["Job ID"],
                "Asset Type": job["Asset Type"],
                "Platform": job["Platform"],
                "Product Handle": job["Product Handle"],
                "Product Title": job["Product Title"],
                "Content Angle": job["Content Angle"],
                "Prompt Summary": job["Video Prompt"][:180],
                "Generated Asset Path": "",
                "Review Status": "Needs Generation",
                "Compliance Check": "No claims; product resemblance and subtitles must be reviewed",
                "Notes": "",
            }
        )
    for row in edit_rows:
        rows.append(
            {
                "Asset ID": row["Edit ID"],
                "Asset Type": "Edited Short Video",
                "Platform": row["Platform"],
                "Product Handle": row["Product Handle"],
                "Product Title": row["Product Title"],
                "Content Angle": "",
                "Prompt Summary": row["Edit Structure"],
                "Generated Asset Path": "",
                "Review Status": "Needs Edit",
                "Compliance Check": "Captions, CTA, music rights, and product accuracy must be reviewed",
                "Notes": "",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_creative_plan(
    input_path: Path,
    image_out: Path,
    video_out: Path,
    edit_out: Path,
    review_out: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    calendar_rows = read_calendar(input_path)
    image_jobs = build_image_jobs(calendar_rows)
    video_jobs = build_video_jobs(calendar_rows)
    edit_rows = build_edit_plan(video_jobs)
    review_rows = build_review_tracker(image_jobs, video_jobs, edit_rows)
    write_csv(image_out, image_jobs, IMAGE_FIELDS)
    write_csv(video_out, video_jobs, VIDEO_FIELDS)
    write_csv(edit_out, edit_rows, EDIT_FIELDS)
    write_csv(review_out, review_rows, REVIEW_FIELDS)
    return image_jobs, video_jobs, edit_rows, review_rows
