from __future__ import annotations

import json
import threading
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .creative_brief import write_creative_plan
from .creator_outreach import (
    write_dm_template_csv,
    write_dm_template_markdown,
    write_seed_template,
    write_tracker,
)
from .exposure_plan import write_channel_plans, write_exposure_plan


@dataclass(frozen=True)
class OutputFile:
    path: str
    label: str


@dataclass(frozen=True)
class Workflow:
    workflow_id: str
    title: str
    description: str
    outputs: tuple[OutputFile, ...]


WORKFLOWS: tuple[Workflow, ...] = (
    Workflow(
        "commercial-seo",
        "第一批商品 SEO 审核",
        "读取真实商品 CSV，生成 commercial_jewelry SEO/GEO 审核表。",
        (
            OutputFile("output/first_batch_commercial_seo_audit.csv", "SEO 审核表"),
            OutputFile("output/matrixify_commercial_update_template.csv", "Matrixify 回写模板"),
        ),
    ),
    Workflow(
        "active-exposure",
        "主动曝光内容分发表",
        "把优先商品生成 TikTok/Reels、Pinterest、YouTube Shorts、Instagram 内容计划。",
        (
            OutputFile("output/active_exposure_calendar.csv", "主动曝光日历"),
            OutputFile("output/pinterest_pin_plan.csv", "Pinterest Pin 计划"),
            OutputFile("output/short_video_script_plan.csv", "短视频脚本计划"),
        ),
    ),
    Workflow(
        "creator-outreach",
        "达人触达与 UGC 寄样表",
        "生成达人筛选表、触达跟进表，以及英文 DM 模板。",
        (
            OutputFile("data/creator_seed_list_template.csv", "达人筛选模板"),
            OutputFile("output/creator_outreach_tracker.csv", "达人跟进表"),
            OutputFile("output/creator_dm_templates.csv", "DM 模板 CSV"),
            OutputFile("output/creator_dm_templates.md", "DM 模板文档"),
        ),
    ),
    Workflow(
        "creative-production",
        "AI 生图/生视频/剪辑任务表",
        "把内容日历拆成 AI 图片提示词、AI 视频提示词、自动剪辑表和审核表。",
        (
            OutputFile("output/ai_image_generation_jobs.csv", "AI 生图任务表"),
            OutputFile("output/ai_video_generation_jobs.csv", "AI 生视频任务表"),
            OutputFile("output/auto_edit_plan.csv", "自动剪辑任务表"),
            OutputFile("output/creative_asset_review_tracker.csv", "素材审核表"),
        ),
    ),
    Workflow(
        "full-local-pipeline",
        "一键重建全部本地流程",
        "从商品 SEO 到主动曝光、达人触达、AI 创意生产计划全部重新生成。",
        (
            OutputFile("output/first_batch_commercial_seo_audit.csv", "SEO 审核表"),
            OutputFile("output/active_exposure_calendar.csv", "主动曝光日历"),
            OutputFile("output/creator_outreach_tracker.csv", "达人跟进表"),
            OutputFile("output/ai_image_generation_jobs.csv", "AI 生图任务表"),
            OutputFile("output/ai_video_generation_jobs.csv", "AI 生视频任务表"),
            OutputFile("output/auto_edit_plan.csv", "自动剪辑任务表"),
        ),
    ),
)


WORKFLOW_BY_ID = {workflow.workflow_id: workflow for workflow in WORKFLOWS}


def csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        lines = sum(1 for line in f if line.strip())
    return max(0, lines - 1)


def file_status(root: Path, output: OutputFile) -> dict[str, str | int | bool]:
    path = root / output.path
    exists = path.exists()
    modified = ""
    size = 0
    rows = 0
    if exists:
        stat = path.stat()
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        if path.suffix.lower() == ".csv":
            rows = csv_row_count(path)
    return {
        "path": output.path,
        "label": output.label,
        "exists": exists,
        "rows": rows,
        "size": size,
        "modified": modified,
    }


def status_payload(root: Path) -> dict[str, object]:
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "workflows": [
            {
                "id": workflow.workflow_id,
                "title": workflow.title,
                "description": workflow.description,
                "outputs": [file_status(root, output) for output in workflow.outputs],
            }
            for workflow in WORKFLOWS
        ],
    }


def run_workflow(workflow_id: str, root: Path) -> dict[str, object]:
    if workflow_id not in WORKFLOW_BY_ID:
        raise ValueError(f"Unknown workflow: {workflow_id}")

    if workflow_id == "commercial-seo":
        run_commercial_seo(root)
    elif workflow_id == "active-exposure":
        run_active_exposure(root)
    elif workflow_id == "creator-outreach":
        run_creator_outreach(root)
    elif workflow_id == "creative-production":
        run_creative_production(root)
    elif workflow_id == "full-local-pipeline":
        run_commercial_seo(root)
        run_active_exposure(root)
        run_creator_outreach(root)
        run_creative_production(root)

    return {
        "message": f"{WORKFLOW_BY_ID[workflow_id].title} 已完成",
        "status": status_payload(root),
    }


def run_commercial_seo(root: Path) -> None:
    from .cli import audit_csv, matrixify_update_template_csv

    input_path = root / "data/first_batch_commercial_products.csv"
    audit_out = root / "output/first_batch_commercial_seo_audit.csv"
    matrixify_out = root / "output/matrixify_commercial_update_template.csv"
    audit_csv(input_path, audit_out, focus="commercial_jewelry")
    matrixify_update_template_csv(input_path, matrixify_out, focus="commercial_jewelry")


def run_active_exposure(root: Path) -> None:
    rows = write_exposure_plan(
        root / "output/first_batch_commercial_seo_audit.csv",
        root / "output/active_exposure_calendar.csv",
        days=30,
    )
    write_channel_plans(
        rows,
        root / "output/pinterest_pin_plan.csv",
        root / "output/short_video_script_plan.csv",
    )


def run_creator_outreach(root: Path) -> None:
    write_tracker(root / "output/creator_outreach_tracker.csv")
    write_seed_template(root / "data/creator_seed_list_template.csv")
    write_dm_template_csv(root / "output/creator_dm_templates.csv")
    write_dm_template_markdown(root / "output/creator_dm_templates.md")


def run_creative_production(root: Path) -> None:
    write_creative_plan(
        root / "output/active_exposure_calendar.csv",
        root / "output/ai_image_generation_jobs.csv",
        root / "output/ai_video_generation_jobs.csv",
        root / "output/auto_edit_plan.csv",
        root / "output/creative_asset_review_tracker.csv",
    )


def render_dashboard() -> str:
    workflow_cards = "\n".join(
        f"""
        <article class="workflow-card" data-workflow="{workflow.workflow_id}">
          <div>
            <p class="eyebrow">Workflow</p>
            <h2>{workflow.title}</h2>
            <p>{workflow.description}</p>
          </div>
          <button type="button" data-run="{workflow.workflow_id}">运行</button>
        </article>
        """
        for workflow in WORKFLOWS
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mandala Ops Workbench</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #202124;
      --muted: #687078;
      --line: #d9dee3;
      --panel: #ffffff;
      --soft: #f5f7f8;
      --accent: #0f766e;
      --accent-dark: #0b5d58;
      --warn: #9a3412;
      font-family: Arial, "Microsoft YaHei", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--soft);
      color: var(--ink);
    }}
    header {{
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      padding: 24px min(5vw, 56px);
    }}
    header h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.2;
    }}
    header p {{
      margin: 0;
      color: var(--muted);
      max-width: 920px;
      line-height: 1.6;
    }}
    main {{
      display: grid;
      grid-template-columns: minmax(280px, 420px) 1fr;
      gap: 20px;
      padding: 24px min(5vw, 56px);
      align-items: start;
    }}
    .stack {{ display: grid; gap: 14px; }}
    .workflow-card, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .workflow-card {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 16px;
      align-items: center;
    }}
    .eyebrow {{
      margin: 0 0 4px;
      color: var(--accent);
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: .08em;
      font-weight: 700;
    }}
    h2 {{
      margin: 0 0 8px;
      font-size: 18px;
      line-height: 1.3;
    }}
    .workflow-card p:not(.eyebrow), .panel p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.55;
      font-size: 14px;
    }}
    button {{
      appearance: none;
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      min-width: 74px;
      height: 38px;
      padding: 0 14px;
      font-weight: 700;
      cursor: pointer;
    }}
    button:hover {{ background: var(--accent-dark); }}
    button:disabled {{ opacity: .55; cursor: wait; }}
    .panel h2 {{ font-size: 20px; }}
    .status-bar {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 16px;
    }}
    .notice {{
      margin-top: 14px;
      padding: 12px;
      border-radius: 8px;
      background: #ecfdf5;
      color: #065f46;
      display: none;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      background: #fff;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      text-align: left;
      padding: 11px 10px;
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .badge {{
      display: inline-flex;
      border-radius: 999px;
      padding: 3px 9px;
      background: #e6f4f1;
      color: #0f766e;
      font-weight: 700;
      font-size: 12px;
      white-space: nowrap;
    }}
    .missing {{ background: #fff7ed; color: var(--warn); }}
    a {{ color: var(--accent-dark); font-weight: 700; text-decoration: none; }}
    @media (max-width: 900px) {{
      main {{ grid-template-columns: 1fr; }}
      .workflow-card {{ grid-template-columns: 1fr; }}
      button {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Mandala Ops Workbench</h1>
    <p>这是本地操作面板。它只读取和生成这个仓库里的 CSV 文件，不连接 Shopify API，不修改线上商品，也不会自动发布内容。</p>
  </header>
  <main>
    <section class="stack">
      {workflow_cards}
    </section>
    <section class="panel">
      <div class="status-bar">
        <div>
          <h2>输出文件状态</h2>
          <p id="updated">正在读取...</p>
        </div>
        <button type="button" id="refresh">刷新</button>
      </div>
      <div id="notice" class="notice"></div>
      <div id="status"></div>
    </section>
  </main>
  <script>
    const statusEl = document.getElementById("status");
    const updatedEl = document.getElementById("updated");
    const noticeEl = document.getElementById("notice");

    function showNotice(message, isError = false) {{
      noticeEl.textContent = message;
      noticeEl.style.display = "block";
      noticeEl.style.background = isError ? "#fef2f2" : "#ecfdf5";
      noticeEl.style.color = isError ? "#991b1b" : "#065f46";
    }}

    function renderStatus(payload) {{
      updatedEl.textContent = "最后刷新：" + payload.generated_at;
      const rows = payload.workflows.flatMap(workflow =>
        workflow.outputs.map(output => `
          <tr>
            <td>${{workflow.title}}</td>
            <td><a href="/download?path=${{encodeURIComponent(output.path)}}">${{output.path}}</a></td>
            <td><span class="badge ${{output.exists ? "" : "missing"}}">${{output.exists ? "已生成" : "未生成"}}</span></td>
            <td>${{output.rows || "-"}}</td>
            <td>${{output.modified || "-"}}</td>
          </tr>
        `)
      ).join("");
      statusEl.innerHTML = `
        <table>
          <thead><tr><th>流程</th><th>文件</th><th>状态</th><th>行数</th><th>更新时间</th></tr></thead>
          <tbody>${{rows}}</tbody>
        </table>
      `;
    }}

    async function refreshStatus() {{
      const response = await fetch("/api/status");
      renderStatus(await response.json());
    }}

    async function runWorkflow(id, button) {{
      const original = button.textContent;
      button.disabled = true;
      button.textContent = "运行中";
      showNotice("正在生成本地 CSV，请稍等...");
      try {{
        const response = await fetch("/api/run", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ workflow_id: id }})
        }});
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "运行失败");
        renderStatus(payload.status);
        showNotice(payload.message);
      }} catch (error) {{
        showNotice(error.message, true);
      }} finally {{
        button.disabled = false;
        button.textContent = original;
      }}
    }}

    document.querySelectorAll("[data-run]").forEach(button => {{
      button.addEventListener("click", () => runWorkflow(button.dataset.run, button));
    }});
    document.getElementById("refresh").addEventListener("click", refreshStatus);
    refreshStatus();
  </script>
</body>
</html>"""


class WorkbenchHandler(BaseHTTPRequestHandler):
    server: "WorkbenchServer"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_text(render_dashboard(), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/status":
            self.send_json(status_payload(self.server.repo_root))
            return
        if parsed.path == "/download":
            self.send_download(parsed.query)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/run":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            result = run_workflow(str(payload.get("workflow_id", "")), self.server.repo_root)
            self.send_json(result)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=400)

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_text(self, text: str, content_type: str) -> None:
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_download(self, query: str) -> None:
        params = parse_qs(query)
        requested = params.get("path", [""])[0]
        safe_paths = {output.path for workflow in WORKFLOWS for output in workflow.outputs}
        if requested not in safe_paths:
            self.send_error(403)
            return
        file_path = self.server.repo_root / requested
        if not file_path.exists():
            self.send_error(404)
            return
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class WorkbenchServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], repo_root: Path):
        super().__init__(server_address, WorkbenchHandler)
        self.repo_root = repo_root


def serve_workbench(host: str = "127.0.0.1", port: int = 8787, open_browser: bool = True, root: Path | None = None) -> None:
    repo_root = (root or Path.cwd()).resolve()
    server = WorkbenchServer((host, port), repo_root)
    url = f"http://{host}:{server.server_port}/"
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    print(f"Mandala Ops Workbench running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
