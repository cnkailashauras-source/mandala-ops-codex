from __future__ import annotations

import csv
import json
import re
import threading
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .creative_brief import (
    EDIT_FIELDS,
    IMAGE_FIELDS,
    REVIEW_FIELDS,
    VIDEO_FIELDS,
    build_edit_plan,
    build_image_jobs,
    build_review_tracker,
    build_video_jobs,
    write_creative_plan,
    write_csv,
)
from .exposure_plan import write_channel_plans, write_exposure_plan


PRODUCT_SOURCE = "output/first_batch_commercial_seo_audit.csv"
EXPOSURE_CALENDAR = "output/active_exposure_calendar.csv"


@dataclass(frozen=True)
class StudioOutput:
    path: str
    label: str
    stage: str


STUDIO_OUTPUTS: tuple[StudioOutput, ...] = (
    StudioOutput("output/active_exposure_calendar.csv", "社媒内容日历", "内容策划"),
    StudioOutput("output/pinterest_pin_plan.csv", "Pinterest 图文计划", "内容策划"),
    StudioOutput("output/short_video_script_plan.csv", "短视频脚本计划", "内容策划"),
    StudioOutput("output/ai_image_generation_jobs.csv", "GPT Image 生图任务表", "AI 生图"),
    StudioOutput("output/ai_video_generation_jobs.csv", "Kling 生视频任务表", "AI 视频"),
    StudioOutput("output/auto_edit_plan.csv", "剪映 / HyperFrames 剪辑任务表", "自动剪辑"),
    StudioOutput("output/creative_asset_review_tracker.csv", "素材审核表", "审核发布"),
)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return max(0, sum(1 for line in f if line.strip()) - 1)


def output_status(root: Path, output: StudioOutput) -> dict[str, object]:
    path = root / output.path
    exists = path.exists()
    return {
        "path": output.path,
        "label": output.label,
        "stage": output.stage,
        "exists": exists,
        "rows": csv_row_count(path) if exists and path.suffix.lower() == ".csv" else 0,
        "modified": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M") if exists else "",
    }


def product_source_rows(root: Path) -> list[dict[str, str]]:
    rows = read_csv_rows(root / PRODUCT_SOURCE)
    if rows:
        return rows
    return read_csv_rows(root / "data/first_batch_commercial_products.csv")


def product_title(row: dict[str, str]) -> str:
    return row.get("Recommended Title") or row.get("Title") or row.get("Original Title") or row.get("Handle", "")


def product_category(row: dict[str, str]) -> str:
    category = row.get("Focus Category", "")
    if category:
        return category
    text = " ".join([row.get("Handle", ""), row.get("Title", ""), row.get("Tags", "")]).lower()
    if "quartzite" in text or "green" in text or "非洲翠" in text:
        return "African Green Quartzite"
    if "bracelet" in text or "水晶" in text or "紫晶" in text:
        return "Crystal Bracelet"
    return "Commercial Jewelry"


def products_payload(root: Path) -> list[dict[str, str]]:
    products = []
    for row in product_source_rows(root):
        handle = row.get("Handle", "").strip()
        if not handle:
            continue
        priority = row.get("Priority", "Medium").strip() or "Medium"
        category = product_category(row)
        if priority == "Skip" or category == "Excluded Religious Item":
            continue
        products.append(
            {
                "handle": handle,
                "title": product_title(row),
                "category": category,
                "priority": priority,
                "price": row.get("Variant Price", ""),
                "image": row.get("Image Src", ""),
            }
        )
    return products


def dashboard_counts(root: Path) -> dict[str, int]:
    return {
        "products": len(products_payload(root)),
        "image_jobs": csv_row_count(root / "output/ai_image_generation_jobs.csv"),
        "video_jobs": csv_row_count(root / "output/ai_video_generation_jobs.csv"),
        "edit_jobs": csv_row_count(root / "output/auto_edit_plan.csv"),
        "review_items": csv_row_count(root / "output/creative_asset_review_tracker.csv"),
    }


def status_payload(root: Path) -> dict[str, object]:
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "counts": dashboard_counts(root),
        "products": products_payload(root),
        "outputs": [output_status(root, output) for output in STUDIO_OUTPUTS],
    }


def run_exposure(root: Path) -> None:
    rows = write_exposure_plan(root / PRODUCT_SOURCE, root / "output/active_exposure_calendar.csv", days=30)
    write_channel_plans(rows, root / "output/pinterest_pin_plan.csv", root / "output/short_video_script_plan.csv")


def run_creative(root: Path) -> None:
    write_creative_plan(
        root / EXPOSURE_CALENDAR,
        root / "output/ai_image_generation_jobs.csv",
        root / "output/ai_video_generation_jobs.csv",
        root / "output/auto_edit_plan.csv",
        root / "output/creative_asset_review_tracker.csv",
    )


def run_studio_action(action: str, root: Path) -> dict[str, object]:
    if action == "build-exposure":
        run_exposure(root)
        message = "社媒内容计划已生成"
    elif action == "build-creative":
        run_creative(root)
        message = "AI 生图 / Kling 视频 / 剪辑任务已生成"
    elif action == "full-creative":
        run_exposure(root)
        run_creative(root)
        message = "社媒创意生产流水线已重建"
    else:
        raise ValueError(f"Unknown studio action: {action}")
    return {"message": message, "status": status_payload(root)}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return slug or "selected-product"


def product_calendar_rows(root: Path, handle: str) -> list[dict[str, str]]:
    rows = read_csv_rows(root / EXPOSURE_CALENDAR)
    return [row for row in rows if row.get("Product Handle") == handle]


def product_output_paths(handle: str) -> dict[str, str]:
    slug = slugify(handle)
    base = f"output/creative_studio/{slug}"
    return {
        "image": f"{base}_gpt_image_jobs.csv",
        "video": f"{base}_kling_video_jobs.csv",
        "edit": f"{base}_capcut_hyperframes_edit_plan.csv",
        "review": f"{base}_asset_review_tracker.csv",
        "brief": f"{base}_creative_brief.md",
    }


def write_product_brief(root: Path, handle: str, rows: list[dict[str, str]], paths: dict[str, str]) -> None:
    product = next((item for item in products_payload(root) if item["handle"] == handle), None)
    title = product["title"] if product else handle
    category = product["category"] if product else "Commercial Jewelry"
    angles = sorted({row.get("Content Angle", "") for row in rows if row.get("Content Angle")})
    body = [
        f"# Mandala Creative Brief: {title}",
        "",
        f"- Product Handle: `{handle}`",
        f"- Focus Category: {category}",
        "- Production Goal: create reviewable social assets for GPT Image, Kling, and CapCut / HyperFrames.",
        "- Safety: no Shopify edits, no auto-posting, no medical or wealth claims, no misleading material names.",
        "",
        "## Content Angles",
        "",
    ]
    body.extend([f"- {angle}" for angle in angles] or ["- everyday jewelry"])
    body.extend(
        [
            "",
            "## Output Files",
            "",
            f"- GPT Image jobs: `{paths['image']}`",
            f"- Kling video jobs: `{paths['video']}`",
            f"- CapCut / HyperFrames edit plan: `{paths['edit']}`",
            f"- Asset review tracker: `{paths['review']}`",
        ]
    )
    out_path = root / paths["brief"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(body) + "\n", encoding="utf-8")


def run_product_kit(root: Path, handle: str) -> dict[str, object]:
    if not (root / EXPOSURE_CALENDAR).exists():
        run_exposure(root)
    rows = product_calendar_rows(root, handle)
    if not rows:
        raise ValueError(f"No content calendar rows found for product: {handle}")

    image_jobs = build_image_jobs(rows)
    video_jobs = build_video_jobs(rows)
    edit_rows = build_edit_plan(video_jobs)
    review_rows = build_review_tracker(image_jobs, video_jobs, edit_rows)
    paths = product_output_paths(handle)

    write_csv(root / paths["image"], image_jobs, IMAGE_FIELDS)
    write_csv(root / paths["video"], video_jobs, VIDEO_FIELDS)
    write_csv(root / paths["edit"], edit_rows, EDIT_FIELDS)
    write_csv(root / paths["review"], review_rows, REVIEW_FIELDS)
    write_product_brief(root, handle, rows, paths)

    return {
        "message": f"{handle} 的社媒素材包已生成",
        "files": [{"label": label, "path": path} for label, path in paths.items()],
        "status": status_payload(root),
    }


def render_studio() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mandala Creative Studio</title>
  <style>
    :root {
      --ink: #1f2428;
      --muted: #66707a;
      --line: #dbe2e8;
      --panel: #ffffff;
      --soft: #f4f7f6;
      --accent: #0f766e;
      --accent-2: #7c3aed;
      --deep: #132f2c;
      font-family: Arial, "Microsoft YaHei", sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--soft); color: var(--ink); }
    header {
      padding: 24px 40px;
      background: var(--deep);
      color: #fff;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 20px;
    }
    h1 { margin: 0 0 8px; font-size: 28px; line-height: 1.2; }
    header p { margin: 0; color: #d8e8e5; line-height: 1.55; }
    main {
      padding: 22px 40px 36px;
      display: grid;
      grid-template-columns: 330px 1fr;
      gap: 18px;
      align-items: start;
    }
    .panel, .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    .stack { display: grid; gap: 14px; }
    .actions { display: grid; gap: 10px; }
    button {
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      height: 38px;
      padding: 0 12px;
      font-weight: 700;
      cursor: pointer;
    }
    button.secondary { background: var(--accent-2); }
    button.ghost { background: #e7f3f1; color: #0b5d58; }
    button:disabled { opacity: .55; cursor: wait; }
    h2 { margin: 0 0 10px; font-size: 18px; }
    h3 { margin: 0 0 6px; font-size: 15px; }
    p { color: var(--muted); line-height: 1.55; margin: 0; }
    .metrics {
      display: grid;
      grid-template-columns: repeat(5, minmax(110px, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .metric {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
    }
    .metric strong { display: block; font-size: 24px; margin-top: 4px; }
    .product-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 12px;
    }
    .product-card {
      display: grid;
      gap: 12px;
      min-height: 190px;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }
    .badge {
      display: inline-flex;
      border-radius: 999px;
      padding: 3px 8px;
      font-size: 12px;
      font-weight: 700;
      background: #e7f3f1;
      color: #0f766e;
    }
    .badge.purple { background: #f0e7ff; color: #6d28d9; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { border-bottom: 1px solid var(--line); padding: 10px 8px; text-align: left; vertical-align: top; }
    th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
    a { color: #0b5d58; text-decoration: none; font-weight: 700; }
    .notice {
      display: none;
      margin-bottom: 14px;
      padding: 12px;
      border-radius: 8px;
      background: #ecfdf5;
      color: #065f46;
    }
    .tabs {
      display: flex;
      gap: 8px;
      margin-bottom: 14px;
    }
    .tabs button { background: #e7f3f1; color: #0b5d58; }
    .tabs button.active { background: var(--accent); color: #fff; }
    @media (max-width: 980px) {
      header { padding: 22px; align-items: flex-start; flex-direction: column; }
      main { padding: 18px; grid-template-columns: 1fr; }
      .metrics { grid-template-columns: repeat(2, 1fr); }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Mandala Creative Studio</h1>
      <p>社媒 AI 内容生产工作台：围绕商品生成 GPT Image 生图任务、Kling 视频任务、剪映 / HyperFrames 剪辑任务和审核表。</p>
    </div>
    <button type="button" id="refresh" class="ghost">刷新状态</button>
  </header>
  <main>
    <aside class="stack">
      <section class="panel">
        <h2>生产流程</h2>
        <div class="actions">
          <button type="button" data-action="build-exposure">生成社媒内容日历</button>
          <button type="button" data-action="build-creative" class="secondary">生成 AI 素材任务</button>
          <button type="button" data-action="full-creative">一键重建创意流水线</button>
        </div>
      </section>
      <section class="panel">
        <h2>使用方式</h2>
        <p>先点一键重建创意流水线，再选择单个商品生成素材包。素材包可以交给 GPT Image、Kling、剪映或 HyperFrames 使用。当前不自动调用外部平台。</p>
      </section>
      <section class="panel">
        <h2>安全边界</h2>
        <p>不修改 Shopify，不自动发布社媒，不自动联系达人，不写功效承诺，不把非洲翠写成 Jade。</p>
      </section>
    </aside>
    <section class="stack">
      <div id="notice" class="notice"></div>
      <section class="metrics" id="metrics"></section>
      <section class="panel">
        <div class="tabs">
          <button type="button" class="active" data-tab="products">商品素材库</button>
          <button type="button" data-tab="outputs">输出文件</button>
        </div>
        <div id="products-tab">
          <div class="product-grid" id="products"></div>
        </div>
        <div id="outputs-tab" style="display:none">
          <div id="outputs"></div>
        </div>
      </section>
    </section>
  </main>
  <script>
    const noticeEl = document.getElementById("notice");
    const metricsEl = document.getElementById("metrics");
    const productsEl = document.getElementById("products");
    const outputsEl = document.getElementById("outputs");

    function notice(message, isError = false) {
      noticeEl.textContent = message;
      noticeEl.style.display = "block";
      noticeEl.style.background = isError ? "#fef2f2" : "#ecfdf5";
      noticeEl.style.color = isError ? "#991b1b" : "#065f46";
    }

    function link(path) {
      return `<a href="/download?path=${encodeURIComponent(path)}">${path}</a>`;
    }

    function renderMetrics(counts) {
      const labels = [
        ["products", "可生产商品"],
        ["image_jobs", "生图任务"],
        ["video_jobs", "视频任务"],
        ["edit_jobs", "剪辑任务"],
        ["review_items", "审核项"]
      ];
      metricsEl.innerHTML = labels.map(([key, label]) => `
        <div class="metric"><p>${label}</p><strong>${counts[key] || 0}</strong></div>
      `).join("");
    }

    function renderProducts(products) {
      if (!products.length) {
        productsEl.innerHTML = "<p>还没有可用商品。请先生成第一批商品审核表。</p>";
        return;
      }
      productsEl.innerHTML = products.map(product => `
        <article class="card product-card">
          <div>
            <h3>${product.title}</h3>
            <p>${product.handle}</p>
            <div class="meta">
              <span class="badge ${product.category.includes("Crystal") ? "purple" : ""}">${product.category}</span>
              <span class="badge">${product.priority}</span>
            </div>
          </div>
          <button type="button" data-product="${product.handle}">生成该商品素材包</button>
        </article>
      `).join("");
      document.querySelectorAll("[data-product]").forEach(button => {
        button.addEventListener("click", () => generateProductKit(button.dataset.product, button));
      });
    }

    function renderOutputs(outputs) {
      outputsEl.innerHTML = `
        <table>
          <thead><tr><th>阶段</th><th>文件</th><th>行数</th><th>更新时间</th></tr></thead>
          <tbody>
            ${outputs.map(output => `
              <tr>
                <td>${output.stage}</td>
                <td>${output.exists ? link(output.path) : output.path}</td>
                <td>${output.rows || "-"}</td>
                <td>${output.modified || "-"}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

    async function refresh() {
      const response = await fetch("/api/status");
      const payload = await response.json();
      renderMetrics(payload.counts);
      renderProducts(payload.products);
      renderOutputs(payload.outputs);
    }

    async function runAction(action, button) {
      const original = button.textContent;
      button.disabled = true;
      button.textContent = "生成中";
      notice("正在生成本地任务表...");
      try {
        const response = await fetch("/api/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action })
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "生成失败");
        notice(payload.message);
        renderMetrics(payload.status.counts);
        renderProducts(payload.status.products);
        renderOutputs(payload.status.outputs);
      } catch (error) {
        notice(error.message, true);
      } finally {
        button.disabled = false;
        button.textContent = original;
      }
    }

    async function generateProductKit(handle, button) {
      const original = button.textContent;
      button.disabled = true;
      button.textContent = "生成中";
      notice(`正在生成 ${handle} 的素材包...`);
      try {
        const response = await fetch("/api/product-kit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ handle })
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "生成失败");
        const files = payload.files.map(file => `${file.label}: ${file.path}`).join(" / ");
        notice(`${payload.message}。${files}`);
      } catch (error) {
        notice(error.message, true);
      } finally {
        button.disabled = false;
        button.textContent = original;
        refresh();
      }
    }

    document.querySelectorAll("[data-action]").forEach(button => {
      button.addEventListener("click", () => runAction(button.dataset.action, button));
    });
    document.querySelectorAll("[data-tab]").forEach(button => {
      button.addEventListener("click", () => {
        document.querySelectorAll("[data-tab]").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        document.getElementById("products-tab").style.display = button.dataset.tab === "products" ? "block" : "none";
        document.getElementById("outputs-tab").style.display = button.dataset.tab === "outputs" ? "block" : "none";
      });
    });
    document.getElementById("refresh").addEventListener("click", refresh);
    refresh();
  </script>
</body>
</html>"""


class CreativeStudioHandler(BaseHTTPRequestHandler):
    server: "CreativeStudioServer"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_text(render_studio(), "text/html; charset=utf-8")
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
        try:
            payload = self.read_json()
            if parsed.path == "/api/run":
                self.send_json(run_studio_action(str(payload.get("action", "")), self.server.repo_root))
                return
            if parsed.path == "/api/product-kit":
                self.send_json(run_product_kit(self.server.repo_root, str(payload.get("handle", ""))))
                return
            self.send_error(404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=400)

    def read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

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
        safe_paths = {output.path for output in STUDIO_OUTPUTS}
        safe = requested in safe_paths or requested.startswith("output/creative_studio/")
        if not safe:
            self.send_error(403)
            return
        file_path = self.server.repo_root / requested
        if not file_path.exists():
            self.send_error(404)
            return
        body = file_path.read_bytes()
        content_type = "text/markdown; charset=utf-8" if file_path.suffix == ".md" else "text/csv; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{escape(file_path.name)}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class CreativeStudioServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], repo_root: Path):
        super().__init__(server_address, CreativeStudioHandler)
        self.repo_root = repo_root


def serve_creative_studio(
    host: str = "127.0.0.1", port: int = 8790, open_browser: bool = True, root: Path | None = None
) -> None:
    repo_root = (root or Path.cwd()).resolve()
    server = CreativeStudioServer((host, port), repo_root)
    url = f"http://{host}:{server.server_port}/"
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    print(f"Mandala Creative Studio running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
