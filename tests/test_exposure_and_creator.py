import unittest

from mandala_ops.creator_outreach import dm_templates
from mandala_ops.exposure_plan import OUTPUT_FIELDS, build_rows, eligible_products


class ExposureAndCreatorTest(unittest.TestCase):
    def test_religious_product_is_skipped(self):
        rows = [
            {
                "Handle": "green-tara-pendant",
                "Recommended Title": "Green Tara Thangka Pendant",
                "Focus Category": "Excluded Religious Item",
                "Priority": "High",
            }
        ]
        self.assertEqual(eligible_products(rows), [])

    def test_priority_skip_is_skipped(self):
        rows = [
            {
                "Handle": "skip-product",
                "Recommended Title": "Skip Product",
                "Focus Category": "Crystal Bracelet",
                "Priority": "Skip",
            }
        ]
        self.assertEqual(eligible_products(rows), [])

    def test_crystal_bracelet_generates_tiktok_reels_pinterest_content(self):
        products = [
            {
                "Handle": "violet-beaded-bracelet",
                "Recommended Title": "Violet Beaded Bracelet | Everyday Purple Crystal Jewelry",
                "Focus Category": "Crystal Bracelet",
                "Priority": "High",
            }
        ]
        rows = build_rows(products, days=30)
        platforms = {row["Platform"] for row in rows}
        self.assertIn("TikTok/Reels", platforms)
        self.assertIn("Pinterest", platforms)
        self.assertEqual(len([row for row in rows if row["Platform"] == "Pinterest"]), 5)
        self.assertEqual(len([row for row in rows if row["Platform"] == "TikTok/Reels"]), 3)

    def test_african_green_quartzite_content_does_not_contain_jade(self):
        products = [
            {
                "Handle": "green-quartzite-ring",
                "Recommended Title": "African Green Quartzite Ring | Minimal Green Stone Jewelry",
                "Focus Category": "African Green Quartzite",
                "Priority": "Medium",
            }
        ]
        rows = build_rows(products, days=30)
        joined = " ".join(" ".join(row.values()) for row in rows)
        self.assertIn("African Green Quartzite", joined)
        self.assertNotIn("Jade", joined)
        self.assertNotIn("jade", joined.lower())

    def test_all_creator_templates_include_disclosure(self):
        for template in dm_templates():
            message = template["Message"]
            self.assertIn("gifted by Mandala Jewels", message)
            self.assertIn("affiliate link or commission if applicable", message)
            self.assertIn("#ad when required", message)
            self.assertNotIn("guaranteed earnings", message.lower())
            self.assertNotIn("must post a positive review", message.lower())

    def test_exposure_output_fields(self):
        for field in ["Platform", "Hook", "CTA", "UTM URL", "Status"]:
            self.assertIn(field, OUTPUT_FIELDS)


if __name__ == "__main__":
    unittest.main()
