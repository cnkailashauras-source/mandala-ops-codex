import csv
import tempfile
import unittest
from pathlib import Path

from mandala_ops.creative_studio import (
    product_output_paths,
    products_payload,
    render_studio,
    run_product_kit,
    run_studio_action,
    status_payload,
)


class CreativeStudioTest(unittest.TestCase):
    def write_csv(self, path: Path, rows: list[dict[str, str]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def product_rows(self):
        return [
            {
                "Handle": "violet-beaded-bracelet",
                "Recommended Title": "Violet Beaded Bracelet | Everyday Purple Crystal Jewelry",
                "Focus Category": "Crystal Bracelet",
                "Priority": "High",
            },
            {
                "Handle": "green-quartzite-ring",
                "Recommended Title": "African Green Quartzite Ring | Minimal Green Stone Jewelry",
                "Focus Category": "African Green Quartzite",
                "Priority": "Medium",
            },
            {
                "Handle": "buddha-bracelet",
                "Recommended Title": "Buddha Bracelet",
                "Focus Category": "Excluded Religious Item",
                "Priority": "Skip",
            },
        ]

    def test_render_studio_is_social_creative_focused(self):
        html = render_studio()
        self.assertIn("Mandala Creative Studio", html)
        self.assertIn("GPT Image", html)
        self.assertIn("Kling", html)
        self.assertIn("HyperFrames", html)
        self.assertIn("不修改 Shopify", html)

    def test_products_payload_skips_religious_or_skip_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_csv(root / "output/first_batch_commercial_seo_audit.csv", self.product_rows())
            products = products_payload(root)
        handles = {product["handle"] for product in products}
        self.assertIn("violet-beaded-bracelet", handles)
        self.assertIn("green-quartzite-ring", handles)
        self.assertNotIn("buddha-bracelet", handles)

    def test_full_creative_action_generates_pipeline_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_csv(root / "output/first_batch_commercial_seo_audit.csv", self.product_rows())
            result = run_studio_action("full-creative", root)
            self.assertIn("社媒创意生产流水线已重建", result["message"])
            status = status_payload(root)
            self.assertGreater(status["counts"]["image_jobs"], 0)
            self.assertGreater(status["counts"]["video_jobs"], 0)
            self.assertTrue((root / "output/ai_image_generation_jobs.csv").exists())
            self.assertTrue((root / "output/auto_edit_plan.csv").exists())

    def test_product_kit_generates_gpt_image_kling_and_edit_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_csv(root / "output/first_batch_commercial_seo_audit.csv", self.product_rows())
            run_studio_action("full-creative", root)
            result = run_product_kit(root, "green-quartzite-ring")
            paths = product_output_paths("green-quartzite-ring")
            self.assertIn("green-quartzite-ring 的社媒素材包已生成", result["message"])
            for path in paths.values():
                self.assertTrue((root / path).exists())
            joined = " ".join((root / paths["image"]).read_text(encoding="utf-8-sig").split())
            self.assertIn("African Green Quartzite", joined)
            self.assertNotIn("Jade", joined)


if __name__ == "__main__":
    unittest.main()
