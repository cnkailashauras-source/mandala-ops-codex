import tempfile
import unittest
from pathlib import Path

from mandala_ops.workbench import WORKFLOWS, file_status, render_dashboard, run_workflow, status_payload


class WorkbenchTest(unittest.TestCase):
    def test_dashboard_exposes_all_workflow_buttons(self):
        html = render_dashboard()
        self.assertIn("Mandala Ops Workbench", html)
        for workflow in WORKFLOWS:
            self.assertIn(workflow.workflow_id, html)
            self.assertIn(workflow.title, html)

    def test_status_payload_counts_existing_csv_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = WORKFLOWS[0].outputs[0]
            path = root / output.path
            path.parent.mkdir(parents=True)
            path.write_text("Handle,Title\none,One\ntwo,Two\n", encoding="utf-8")

            status = file_status(root, output)
            self.assertTrue(status["exists"])
            self.assertEqual(status["rows"], 2)
            self.assertEqual(status["path"], output.path)

    def test_status_payload_contains_workflow_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = status_payload(Path(tmp))
        self.assertIn("workflows", payload)
        self.assertGreaterEqual(len(payload["workflows"]), 5)
        first = payload["workflows"][0]
        self.assertIn("outputs", first)
        self.assertIn("description", first)

    def test_unknown_workflow_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                run_workflow("shopify-live-update", Path(tmp))


if __name__ == "__main__":
    unittest.main()
