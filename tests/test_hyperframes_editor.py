import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mandala_ops.hyperframes_editor import (
    UploadedMedia,
    create_hyperframes_project,
    list_hyperframes_projects,
    render_composition_html,
    render_hyperframes_project,
    resolution_for_aspect,
    target_seconds_from_prompt,
)
from mandala_ops.hyperframes_studio import render_hyperframes_studio


class HyperFramesEditorTest(unittest.TestCase):
    def test_duration_and_resolution_helpers(self):
        self.assertEqual(target_seconds_from_prompt("剪成 15 秒 TikTok"), 15)
        self.assertEqual(target_seconds_from_prompt("make a 90 second edit"), 90)
        self.assertEqual(resolution_for_aspect("9:16"), (1080, 1920))
        self.assertEqual(resolution_for_aspect("4:5"), (1080, 1350))

    def test_composition_contains_hyperframes_timeline_attributes(self):
        html = render_composition_html(
            [{"filename": "clip.mp4", "path": "assets/clip.mp4", "type": "video"}],
            "15 second product video with captions",
            "9:16",
            15,
        )
        self.assertIn('data-width="1080"', html)
        self.assertIn('data-height="1920"', html)
        self.assertIn('data-duration="15"', html)
        self.assertIn("data-start", html)
        self.assertIn('class="clip media', html)
        self.assertIn('data-composition-id="root"', html)
        self.assertNotIn("Mandala Jewels", html)
        self.assertNotIn("Save the styling idea", html)
        self.assertNotIn("@mandalajewels", html)
        self.assertNotIn("caption", html.lower())

    def test_create_project_writes_hyperframes_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = create_hyperframes_project(
                root,
                [
                    UploadedMedia("product.jpg", b"fake image bytes"),
                    UploadedMedia("clip.mp4", b"fake video bytes"),
                ],
                "15 second TikTok product edit with hook and CTA",
                "Purple Bracelet Test",
                "9:16",
            )
            project_dir = root / result["project_dir"]
            self.assertTrue((project_dir / "comp.html").exists())
            self.assertTrue((project_dir / "package.json").exists())
            self.assertIn("npx --yes hyperframes preview", result["commands"]["preview"])
            self.assertIn("npx --yes hyperframes render", result["commands"]["render"])
            self.assertEqual(len(list_hyperframes_projects(root)), 1)

    def test_render_project_returns_mp4_when_hyperframes_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = create_hyperframes_project(
                root,
                [UploadedMedia("clip.mp4", b"fake video bytes")],
                "15 second TikTok product edit",
                "Render Test",
                "9:16",
            )
            project_dir = root / result["project_dir"]

            def fake_run(*args, **kwargs):
                (project_dir / "output.mp4").write_bytes(b"mp4")
                return SimpleNamespace(returncode=0, stdout="render ok")

            with patch("mandala_ops.hyperframes_editor.shutil.which", return_value="npx"), patch(
                "mandala_ops.hyperframes_editor.subprocess.run", side_effect=fake_run
            ):
                render = render_hyperframes_project(root, result["project_id"])

            self.assertEqual(render["status"], "Rendered")
            self.assertTrue((root / render["output_video"]).exists())
            self.assertTrue((project_dir / "render_log.txt").exists())

    def test_studio_page_is_hyperframes_focused(self):
        html = render_hyperframes_studio()
        self.assertIn("Mandala HyperFrames Studio", html)
        self.assertIn("GPT Image 2", html)
        self.assertIn("Kling", html)
        self.assertIn("剪映", html)
        self.assertIn("生成 HyperFrames 工程", html)
        self.assertIn("render_now", html)
        self.assertIn("/api/render-project", html)


if __name__ == "__main__":
    unittest.main()
