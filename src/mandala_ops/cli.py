from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable

from .config import get_settings
from .content_plan import rows as content_rows
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

    content = subparsers.add_parser("content-plan", help="Generate GEO/SEO content plan CSV.")
    content.add_argument("--out", default="output/content_plan.csv")

    subparsers.add_parser("env-check", help="Check required environment variables.")

    args = parser.parse_args()

    if args.command == "audit":
        audit_csv(Path(args.input_csv), Path(args.out), focus=args.focus)
        print(f"Wrote {args.out}")
    elif args.command == "content-plan":
        write_content_plan(Path(args.out))
        print(f"Wrote {args.out}")
    elif args.command == "env-check":
        settings = get_settings()
        print(f"Shopify domain configured: {bool(settings.shopify_shop_domain)}")
        print(f"Shopify token configured: {bool(settings.shopify_admin_access_token)}")
        print(f"Dry run: {settings.dry_run}")


if __name__ == "__main__":
    main()
