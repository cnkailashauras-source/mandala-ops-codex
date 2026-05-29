import csv
import tempfile
import unittest
from pathlib import Path

from mandala_ops.cli import audit_csv, audit_rows
from mandala_ops.seo_rules import (
    ProductRow,
    compliance_notes,
    recommended_product_type,
    recommended_tags,
    recommended_title,
)


class SeoRulesTest(unittest.TestCase):
    def test_detect_green_tara_pendant(self):
        row = ProductRow(title="绿度母 & 文殊菩萨 • Green Tara & Manjushri", price="1350")
        self.assertIn("Green Tara", recommended_title(row))
        self.assertIn("Thangka Pendant", recommended_tags(row))
        self.assertEqual(recommended_product_type(row), "Apparel & Accessories > Jewelry > Charms & Pendants")

    def test_detect_bracelet(self):
        row = ProductRow(title="柔雾丁香紫串珠手链", price="95")
        self.assertIn("Bracelet", recommended_title(row))
        self.assertIn("Crystal Bracelet", recommended_tags(row))
        self.assertEqual(recommended_product_type(row), "Bracelet")

    def test_compliance_flags_old_brand(self):
        row = ProductRow(title="Amitabha Pendant", body_html="KAILASH AURAS product story")
        self.assertIn("Old brand", compliance_notes(row))

    def test_compliance_flags_chinese_old_brand_and_high_risk_terms(self):
        row = ProductRow(
            title="冈仁波齐奥拉斯 Bracelet",
            body_html="This charm is guaranteed to heal and bring wealth.",
        )
        notes = compliance_notes(row)
        self.assertIn("Old brand", notes)
        self.assertIn("guaranteed", notes)
        self.assertIn("heal", notes)
        self.assertIn("bring wealth", notes)

    def test_compliance_does_not_flag_health_as_heal(self):
        row = ProductRow(title="Green Tara Pendant", body_html="A healthy daily styling choice.")
        self.assertNotIn("heal", compliance_notes(row))

    def test_matrixify_rows_are_grouped_by_handle(self):
        rows = [
            {
                "Handle": "green-tara-pendant",
                "Title": "Green Tara Pendant",
                "Body HTML": "Inspired by Tibetan art symbolism.",
                "Type": "",
                "Tags": "",
                "Variant SKU": "SKU-1",
                "Variant Price": "180",
                "Image Src": "https://example.com/one.jpg",
                "SEO Title": "",
                "SEO Description": "",
            },
            {
                "Handle": "green-tara-pendant",
                "Title": "",
                "Body HTML": "",
                "Type": "",
                "Tags": "",
                "Variant SKU": "SKU-2",
                "Variant Price": "190",
                "Image Src": "https://example.com/two.jpg",
                "SEO Title": "",
                "SEO Description": "",
            },
        ]
        output = audit_rows(rows)
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0]["Handle"], "green-tara-pendant")
        self.assertEqual(output[0]["Command"], "UPDATE")
        self.assertIn("Recommended SEO Title", output[0])

    def test_commercial_focus_detects_purple_crystal_bracelet(self):
        rows = [{"Handle": "purple-bracelet", "Title": "紫晶串珠手链", "Variant Price": "88"}]
        output = audit_rows(rows, focus="commercial_jewelry")
        self.assertEqual(output[0]["Focus Category"], "Crystal Bracelet")
        self.assertEqual(output[0]["Priority"], "High")
        self.assertEqual(
            output[0]["Recommended Title"],
            "Violet Beaded Bracelet | Everyday Purple Crystal Jewelry",
        )

    def test_commercial_focus_detects_african_green_quartzite_bracelet(self):
        rows = [{"Handle": "green-quartzite-bracelet", "Title": "非洲翠手串", "Variant Price": "128"}]
        output = audit_rows(rows, focus="commercial_jewelry")
        self.assertEqual(output[0]["Focus Category"], "African Green Quartzite")
        self.assertEqual(output[0]["Priority"], "High")
        self.assertIn("African Green Quartzite", output[0]["Recommended Tags"])

    def test_commercial_focus_detects_african_green_quartzite_pendant(self):
        rows = [{"Handle": "green-quartzite-pendant", "Title": "非洲翠平安扣吊坠", "Variant Price": "220"}]
        output = audit_rows(rows, focus="commercial_jewelry")
        self.assertEqual(output[0]["Focus Category"], "African Green Quartzite")
        self.assertEqual(output[0]["Priority"], "Medium")
        self.assertIn("Peace Buckle Pendant", output[0]["Recommended Title"])
        self.assertNotIn("Jade", output[0]["Recommended Title"])

    def test_commercial_focus_excludes_thangka_pendant(self):
        rows = [{"Handle": "thangka-pendant", "Title": "Green Tara Thangka Pendant", "Variant Price": "680"}]
        output = audit_rows(rows, focus="commercial_jewelry")
        self.assertEqual(output[0]["Focus Category"], "Excluded Religious Item")
        self.assertEqual(output[0]["Priority"], "Skip")
        self.assertEqual(output[0]["Listing Recommendation"], "Content Only / Skip Google Merchant First")
        self.assertEqual(
            output[0]["Compliance Notes"],
            "Religious/cultural item, do not force commercial Google feed optimization",
        )

    def test_commercial_focus_excludes_buddhist_bracelet(self):
        rows = [{"Handle": "buddhist-bracelet", "Title": "佛牌手串", "Variant Price": "95"}]
        output = audit_rows(rows, focus="commercial_jewelry")
        self.assertEqual(output[0]["Focus Category"], "Excluded Religious Item")
        self.assertEqual(output[0]["Priority"], "Skip")

    def test_commercial_focus_csv_contains_focus_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "products.csv"
            output_path = Path(tmp) / "audit.csv"
            with input_path.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["Handle", "Title", "Variant Price"])
                writer.writeheader()
                writer.writerow({"Handle": "soft-lilac", "Title": "柔雾丁香紫串珠手链", "Variant Price": "95"})

            audit_csv(input_path, output_path, focus="commercial_jewelry")

            with output_path.open("r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                self.assertIn("Focus Category", reader.fieldnames or [])
                self.assertIn("Priority", reader.fieldnames or [])
                row = next(reader)
                self.assertEqual(row["Focus Category"], "Crystal Bracelet")
                self.assertEqual(row["Priority"], "High")


if __name__ == "__main__":
    unittest.main()
