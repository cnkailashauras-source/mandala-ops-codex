import unittest

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
        self.assertIn("old brand", compliance_notes(row))


if __name__ == "__main__":
    unittest.main()
