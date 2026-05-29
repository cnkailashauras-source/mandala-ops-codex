import unittest

from mandala_ops.cli import audit_rows
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


if __name__ == "__main__":
    unittest.main()
