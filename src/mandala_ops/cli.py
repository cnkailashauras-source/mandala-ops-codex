from __future__ import annotations

import argparse
import csv
from html import escape
from pathlib import Path
from typing import Iterable

from .config import get_settings
from .content_plan import rows as content_rows
from .creative_brief import write_creative_plan
from .creator_outreach import (
    write_dm_template_csv,
    write_dm_template_markdown,
    write_seed_template,
    write_tracker,
)
from .exposure_plan import write_channel_plans, write_exposure_plan
from .seo_rules import (
    ProductRow,
    collection_candidates,
    compliance_notes,
    commercial_collection_candidates,
    commercial_compliance_notes,
    commercial_focus_category,
    commercial_listing_recommendation,
    commercial_priority,
    commercial_recommended_alt_text,
    commercial_recommended_meta_description,
    commercial_recommended_product_type,
    commercial_recommended_tags,
    commercial_recommended_title,
    recommended_alt_text,
    recommended_meta_description,
    recommended_product_type,
    recommended_tags,
    recommended_title,
    listing_recommendation,
)


FIELD_ALIASES = {
    "handle": ["Handle", "Product Handle", "handle"],
    "title": ["Title", "Product Title", "title"],
    "body_html": ["Body HTML", "Body (HTML)", "Description HTML", "descriptionHtml", "body_html"],
    "vendor": ["Vendor", "Product Vendor", "vendor"],
    "product_type": ["Type", "Product Type", "productType", "product_type"],
    "tags": ["Tags", "Product Tags", "tags"],
    "status": ["Status", "Published", "productStatus", "status"],
    "sku": ["Variant SKU", "SKU", "Variant: SKU", "sku"],
    "price": ["Variant Price", "Price", "Variant: Price", "price"],
    "image_src": ["Image Src", "Image URL", "Image: Src", "image_src"],
    "image_alt_text": ["Image Alt Text", "Image Alt", "Image: Alt Text", "image_alt_text"],
    "seo_title": ["SEO Title", "Search Engine Listing Title", "Metafield: title_tag", "seo_title"],
    "seo_description": [
        "SEO Description",
        "Search Engine Listing Description",
        "Metafield: description_tag",
        "seo_description",
    ],
}


def get_value(row: dict[str, str], key: str) -> str:
    normalized = {name.strip().lower(): value for name, value in row.items()}
    for alias in FIELD_ALIASES[key]:
        if alias in row:
            return (row.get(alias, "") or "").strip()
        value = normalized.get(alias.strip().lower())
        if value is not None:
            return (value or "").strip()
    return ""


def parse_product(row: dict[str, str]) -> ProductRow:
    return ProductRow(**{key: get_value(row, key) for key in FIELD_ALIASES})


def merge_product_rows(rows: Iterable[dict[str, str]]) -> list[ProductRow]:
    products: dict[str, dict[str, str]] = {}
    current_handle = ""

    for raw in rows:
        handle = get_value(raw, "handle") or current_handle
        if not handle:
            continue
        current_handle = handle
        product = products.setdefault(handle, {"Handle": handle})

        for key, aliases in FIELD_ALIASES.items():
            existing = get_value(product, key)
            incoming = get_value(raw, key)
            if incoming and not existing:
                product[aliases[0]] = incoming

    return [parse_product(product) for product in products.values()]


def recommended_seo_title(rec_title: str) -> str:
    title = f"{rec_title.split('|')[0].strip()} - Mandala Jewels"
    return title[:70].rstrip(" -")


def audit_rows(input_rows: Iterable[dict[str, str]], focus: str = "general") -> list[dict[str, str]]:
    output = []
    for product in merge_product_rows(input_rows):
        if focus == "commercial_jewelry":
            rec_title = commercial_recommended_title(product)
            rec_description = commercial_recommended_meta_description(product)
            rec_product_type = commercial_recommended_product_type(product)
            rec_tags = commercial_recommended_tags(product)
            rec_alt_text = commercial_recommended_alt_text(product)
            collections = commercial_collection_candidates(product)
            listing = commercial_listing_recommendation(product)
            notes = commercial_compliance_notes(product)
            focus_category = commercial_focus_category(product)
            priority = commercial_priority(product)
        else:
            rec_title = recommended_title(product)
            rec_description = recommended_meta_description(product)
            rec_product_type = recommended_product_type(product)
            rec_tags = recommended_tags(product)
            rec_alt_text = recommended_alt_text(product)
            collections = collection_candidates(product)
            listing = listing_recommendation(product)
            notes = compliance_notes(product)
            focus_category = "Other"
            priority = "Low"

        output.append(
            {
                "Handle": product.handle,
                "Command": "UPDATE",
                "Focus Category": focus_category,
                "Priority": priority,
                "Original Title": product.title,
                "Original Type": product.product_type,
                "Original Tags": product.tags,
                "Original SEO Title": product.seo_title,
                "Original SEO Description": product.seo_description,
                "Variant SKU": product.sku,
                "Variant Price": product.price,
                "Image Src": product.image_src,
                "Recommended Title": rec_title,
                "Recommended SEO Title": recommended_seo_title(rec_title),
                "Recommended SEO Description": rec_description,
                "Recommended Product Type": rec_product_type,
                "Recommended Tags": ", ".join(rec_tags),
                "Recommended Image Alt Text": rec_alt_text,
                "Collection Candidates": ", ".join(collections),
                "Listing Recommendation": listing,
                "Compliance Notes": notes,
            }
        )
    return output


def audit_csv(input_path: Path, output_path: Path, focus: str = "general") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        input_rows = list(reader)

    output_fields = [
        "Handle",
        "Command",
        "Focus Category",
        "Priority",
        "Original Title",
        "Original Type",
        "Original Tags",
        "Original SEO Title",
        "Original SEO Description",
        "Variant SKU",
        "Variant Price",
        "Image Src",
        "Recommended Title",
        "Recommended SEO Title",
        "Recommended SEO Description",
        "Recommended Product Type",
        "Recommended Tags",
        "Recommended Image Alt Text",
        "Collection Candidates",
        "Listing Recommendation",
        "Compliance Notes",
    ]

    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(audit_rows(input_rows, focus=focus))


def matrixify_update_rows(input_rows: Iterable[dict[str, str]], focus: str = "commercial_jewelry") -> list[dict[str, str]]:
    rows = []
    for audit in audit_rows(input_rows, focus=focus):
        if audit["Priority"] == "Skip":
            continue
        description = audit["Recommended SEO Description"]
        rows.append(
            {
                "Handle": audit["Handle"],
                "Title": audit["Recommended Title"],
                "Body HTML": f"<p>{escape(description)}</p>",
                "Type": audit["Recommended Product Type"],
                "Tags": audit["Recommended Tags"],
                "SEO Title": audit["Recommended SEO Title"],
                "SEO Description": description,
                "Image Alt Text": audit["Recommended Image Alt Text"],
                "Collection Candidates": audit["Collection Candidates"],
                "Focus Category": audit["Focus Category"],
                "Priority": audit["Priority"],
                "Listing Recommendation": audit["Listing Recommendation"],
                "Compliance Notes": audit["Compliance Notes"],
            }
        )
    return rows


def matrixify_update_template_csv(input_path: Path, output_path: Path, focus: str = "commercial_jewelry") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        input_rows = list(reader)

    output_fields = [
        "Handle",
        "Title",
        "Body HTML",
        "Type",
        "Tags",
        "SEO Title",
        "SEO Description",
        "Image Alt Text",
        "Collection Candidates",
        "Focus Category",
        "Priority",
        "Listing Recommendation",
        "Compliance Notes",
    ]

    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(matrixify_update_rows(input_rows, focus=focus))


def write_content_plan(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = content_rows()
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mandala Jewels Codex operations automation.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="Generate SEO audit CSV from product export.")
    audit.add_argument("input_csv")
    audit.add_argument("--focus", choices=["general", "commercial_jewelry"], default="general")
    audit.add_argument("--out", default="output/seo_audit.csv")

    matrixify = subparsers.add_parser("matrixify-template", help="Generate a reviewable Matrixify update CSV.")
    matrixify.add_argument("input_csv")
    matrixify.add_argument("--focus", choices=["general", "commercial_jewelry"], default="commercial_jewelry")
    matrixify.add_argument("--out", default="output/matrixify_update_template.csv")

    content = subparsers.add_parser("content-plan", help="Generate GEO/SEO content plan CSV.")
    content.add_argument("--out", default="output/content_plan.csv")

    exposure = subparsers.add_parser("exposure-plan", help="Generate organic content distribution plans.")
    exposure.add_argument("--input", required=True)
    exposure.add_argument("--days", type=int, default=30)
    exposure.add_argument("--out", default="output/active_exposure_calendar.csv")
    exposure.add_argument("--pinterest-out", default="output/pinterest_pin_plan.csv")
    exposure.add_argument("--short-video-out", default="output/short_video_script_plan.csv")

    creator = subparsers.add_parser("creator-outreach", help="Generate creator outreach tracking templates.")
    creator.add_argument("--out", default="output/creator_outreach_tracker.csv")
    creator.add_argument("--seed-out", default="data/creator_seed_list_template.csv")
    creator.add_argument("--dm-out", default="output/creator_dm_templates.csv")
    creator.add_argument("--dm-md-out", default="output/creator_dm_templates.md")

    creative = subparsers.add_parser("creative-plan", help="Generate AI image, video, edit, and review job tables.")
    creative.add_argument("--input", default="output/active_exposure_calendar.csv")
    creative.add_argument("--image-out", default="output/ai_image_generation_jobs.csv")
    creative.add_argument("--video-out", default="output/ai_video_generation_jobs.csv")
    creative.add_argument("--edit-out", default="output/auto_edit_plan.csv")
    creative.add_argument("--review-out", default="output/creative_asset_review_tracker.csv")

    workbench = subparsers.add_parser("workbench", help="Start the local Mandala Ops browser workbench.")
    workbench.add_argument("--host", default="127.0.0.1")
    workbench.add_argument("--port", type=int, default=8787)
    workbench.add_argument("--no-browser", action="store_true")

    studio = subparsers.add_parser("creative-studio", help="Start the Mandala social creative production studio.")
    studio.add_argument("--host", default="127.0.0.1")
    studio.add_argument("--port", type=int, default=8790)
    studio.add_argument("--no-browser", action="store_true")

    hyperframes = subparsers.add_parser("hyperframes-studio", help="Start the Codex + HyperFrames editing studio.")
    hyperframes.add_argument("--host", default="127.0.0.1")
    hyperframes.add_argument("--port", type=int, default=8792)
    hyperframes.add_argument("--no-browser", action="store_true")

    subparsers.add_parser("env-check", help="Check required environment variables.")

    args = parser.parse_args()

    if args.command == "audit":
        audit_csv(Path(args.input_csv), Path(args.out), focus=args.focus)
        print(f"Wrote {args.out}")
    elif args.command == "matrixify-template":
        matrixify_update_template_csv(Path(args.input_csv), Path(args.out), focus=args.focus)
        print(f"Wrote {args.out}")
    elif args.command == "content-plan":
        write_content_plan(Path(args.out))
        print(f"Wrote {args.out}")
    elif args.command == "exposure-plan":
        rows = write_exposure_plan(Path(args.input), Path(args.out), days=args.days)
        write_channel_plans(rows, Path(args.pinterest_out), Path(args.short_video_out))
        print(f"Wrote {args.out}")
        print(f"Wrote {args.pinterest_out}")
        print(f"Wrote {args.short_video_out}")
    elif args.command == "creator-outreach":
        write_tracker(Path(args.out))
        write_seed_template(Path(args.seed_out))
        write_dm_template_csv(Path(args.dm_out))
        write_dm_template_markdown(Path(args.dm_md_out))
        print(f"Wrote {args.out}")
        print(f"Wrote {args.seed_out}")
        print(f"Wrote {args.dm_out}")
        print(f"Wrote {args.dm_md_out}")
    elif args.command == "creative-plan":
        write_creative_plan(
            Path(args.input),
            Path(args.image_out),
            Path(args.video_out),
            Path(args.edit_out),
            Path(args.review_out),
        )
        print(f"Wrote {args.image_out}")
        print(f"Wrote {args.video_out}")
        print(f"Wrote {args.edit_out}")
        print(f"Wrote {args.review_out}")
    elif args.command == "workbench":
        from .workbench import serve_workbench

        serve_workbench(host=args.host, port=args.port, open_browser=not args.no_browser)
    elif args.command == "creative-studio":
        from .creative_studio import serve_creative_studio

        serve_creative_studio(host=args.host, port=args.port, open_browser=not args.no_browser)
    elif args.command == "hyperframes-studio":
        from .hyperframes_studio import serve_hyperframes_studio

        serve_hyperframes_studio(host=args.host, port=args.port, open_browser=not args.no_browser)
    elif args.command == "env-check":
        settings = get_settings()
        print(f"Shopify domain configured: {bool(settings.shopify_shop_domain)}")
        print(f"Shopify token configured: {bool(settings.shopify_admin_access_token)}")
        print(f"Dry run: {settings.dry_run}")


if __name__ == "__main__":
    main()
