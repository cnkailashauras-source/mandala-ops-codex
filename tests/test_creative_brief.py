import unittest

from mandala_ops.creative_brief import (
    EDIT_FIELDS,
    IMAGE_FIELDS,
    REVIEW_FIELDS,
    VIDEO_FIELDS,
    build_edit_plan,
    build_image_jobs,
    build_review_tracker,
    build_video_jobs,
)


class CreativeBriefTest(unittest.TestCase):
    def calendar_rows(self):
        return [
            {
                "Date": "2026-06-01",
                "Platform": "Pinterest",
                "Product Handle": "violet-beaded-bracelet",
                "Product Title": "Violet Beaded Bracelet | Everyday Purple Crystal Jewelry",
                "Content Angle": "purple bracelet",
                "Hook": "A small purple bracelet detail",
                "CTA": "Save this idea",
                "Hashtags": "#CrystalBracelet #PurpleBracelet",
            },
            {
                "Date": "2026-06-02",
                "Platform": "TikTok/Reels",
                "Product Handle": "green-quartzite-ring",
                "Product Title": "African Green Quartzite Ring | Minimal Green Stone Jewelry",
                "Content Angle": "green stone jewelry",
                "Hook": "A natural green stone detail",
                "CTA": "Shop the piece",
                "Hashtags": "#AfricanGreenQuartzite #GreenStoneJewelry",
            },
        ]

    def test_image_jobs_include_platform_prompt_fields(self):
        jobs = build_image_jobs(self.calendar_rows())
        self.assertEqual(len(jobs), 2)
        for field in ["Platform", "Image Prompt", "Aspect Ratio", "Status"]:
            self.assertIn(field, IMAGE_FIELDS)
        self.assertEqual(jobs[0]["Aspect Ratio"], "2:3")

    def test_video_jobs_only_use_short_video_platforms(self):
        jobs = build_video_jobs(self.calendar_rows())
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["Platform"], "TikTok/Reels")
        for field in ["Video Prompt", "Shot List", "On-screen Text", "Voiceover"]:
            self.assertIn(field, VIDEO_FIELDS)

    def test_green_quartzite_prompts_do_not_contain_jade_or_claims(self):
        rows = self.calendar_rows()
        text = " ".join(
            [job["Image Prompt"] + " " + job["Negative Prompt"] for job in build_image_jobs(rows)]
            + [job["Video Prompt"] + " " + job["Voiceover"] for job in build_video_jobs(rows)]
        ).lower()
        for blocked in ["jade", "jadeite", "healing", "cure", "bring wealth", "make money"]:
            self.assertNotIn(blocked, text)
        self.assertIn("african green quartzite", text)
        self.assertNotIn("styleth", text)

    def test_edit_plan_and_review_tracker_fields(self):
        video_jobs = build_video_jobs(self.calendar_rows())
        edit_rows = build_edit_plan(video_jobs)
        review_rows = build_review_tracker(build_image_jobs(self.calendar_rows()), video_jobs, edit_rows)
        self.assertEqual(len(edit_rows), 1)
        self.assertIn("Export Filename", EDIT_FIELDS)
        self.assertIn("Review Status", REVIEW_FIELDS)
        self.assertGreater(len(review_rows), len(edit_rows))


if __name__ == "__main__":
    unittest.main()
