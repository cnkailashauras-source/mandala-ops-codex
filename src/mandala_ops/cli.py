from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .config import get_settings
from .content_plan import rows as content_rows
from .seo_rules import (
    ProductRow,
    collection_candidates,
    compliance_notes,
    recommended_alt_text,
    recommended_meta_description,
    recommended_product_type,
    recommended_tags,
    recommended_title,
    listing_recommendation,
)


FIELD_ALIASES = {
    "handle": ["Handle", "handle"],
    "title": ["Title", "title"],
    "body_html": ["Body HTML", "Body (HTML)", "descriptionHtml", "body_html"],
    "vendor": ["Vendor", "vendor"],
    "product_type": ["Type", "Product Type", "productType", "product_type"],
    "tags": ["Tags", "tags"],
    "status": ["Status", "status"],
    "sku": ["Variant SKU", "SKU", "sku"],
    "price": ["Variant Price", "Price", "price"],
    "image_src": ["Image Src", "Image URL", "image_src"],
    "image_alt_text": ["Image Alt Text", "Image Alt", "image_alt_text"],
    "seo_title": ["SEO Title", "Search Engine Listing Title", "seo_title"],
    "seo_description": ["SEO Description", "Search Engine Listing Description", "seo_description"],
}


def get_value(row: dict[str, str], key: str) -> str:
    for alias in FIELD_ALIASES[key]:
        if alias in row:
            return row.get(alias, "")
    return ""


def parse_product(row: dict[str, str]) -> ProductRow:
    return ProductRow(**{key: get_value(row, key) for key in FIELD_ALIASES})


def audit_csv(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        input_rows = list(reader)

    output_fields = [
        "Handle",
        "Original Title",
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
        for raw in input_rows:
            product = parse_product(raw)
            rec_title = recommended_title(product)
            writer.writerow(
                {
                    "Handle": product.handle,
                    "Original Title": product.title,
                    "Recommended Title": rec_title,
                    "Recommended SEO Title": f"{rec_title.split('|')[0].strip()} – Mandala Jewels",
                    "Recommended SEO Description": recommended_meta_description(product),
                    "Recommended Product Type": recommended_product_type(product),
                    "Recommended Tags": ", ".join(recommended_tags(product)),
                    "Recommended Image Alt Text": recommended_alt_text(product),
                    "Collection Candidates": ", ".join(collection_candidates(product)),
                    "Listing Recommendation": listing_recommendation(product),
                    "Compliance Notes": compliance_notes(product),
                }
            )


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
    audit.add_argument("--out", default="output/seo_audit.csv")

    content = subparsers.add_parser("content-plan", help="Generate GEO/SEO content plan CSV.")
    content.add_argument("--out", default="output/content_plan.csv")

    subparsers.add_parser("env-check", help="Check required environment variables.")

    args = parser.parse_args()

    if args.command == "audit":
        audit_csv(Path(args.input_csv), Path(args.out))
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
