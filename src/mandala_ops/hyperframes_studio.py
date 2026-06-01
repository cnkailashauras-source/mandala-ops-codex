from __future__ import annotations

import cgi
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .hyperframes_editor import (
    UploadedMedia,
    create_hyperframes_project,
    hyperframes_available,
    list_hyperframes_projects,
    render_hyperframes_project,
)


def render_hyperframes_studio() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mandala HyperFrames Studio</title>
  <style>
    :root {
      --ink: #1f2428;
      --muted: #66707a;
      --line: #dbe2e8;
      --panel: #ffffff;
      --soft: #f4f7f6;
      --accent: #0f766e;
      --accent-2: #7c3aed;
      --deep: #111f1d;
      font-family: Arial, "Microsoft YaHei", sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; color: var(--ink); background: var(--soft); }
    header {
      background: var(--deep);
      color: #fff;
      padding: 28px 42px;
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: center;
    }
    h1 { margin: 0 0 8px; font-size: 30px; }
    header p { margin: 0; color: #d5e7e4; line-height: 1.55; }
    main {
      display: grid;
      grid-template-columns: minmax(320px, 420px) 1fr;
      gap: 20px;
      padding: 24px 42px 40px;
      align-items: start;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    .stack { display: grid; gap: 16px; }
    h2 { margin: 0 0 12px; font-size: 19px; }
    p, li { color: var(--muted); line-height: 1.55; }
    label {
      display: grid;
      gap: 7px;
      margin-bottom: 13px;
      color: var(--ink);
      font-weight: 700;
      font-size: 14px;
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      font: inherit;
      background: #fff;
    }
    textarea { min-height: 180px; resize: vertical; }
    button {
      border: 0;
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      height: 40px;
      padding: 0 16px;
      font-weight: 700;
      cursor: pointer;
    }
    button.secondary { background: var(--accent-2); }
    button:disabled { opacity: .55; cursor: wait; }
    .notice {
      display: none;
      padding: 12px;
      border-radius: 8px;
      background: #ecfdf5;
      color: #065f46;
      margin-bottom: 14px;
      line-height: 1.6;
    }
    .result {
      display: none;
      margin-top: 14px;
      padding: 14px;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: #f8fafc;
      line-height: 1.65;
    }
    .code {
      display: block;
      background: #101828;
      color: #e6edf6;
      padding: 10px 12px;
      border-radius: 6px;
      overflow-x: auto;
      margin: 8px 0;
      font-family: Consolas, monospace;
      font-size: 13px;
      white-space: pre-wrap;
    }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { border-bottom: 1px solid var(--line); padding: 10px 8px; text-align: left; vertical-align: top; }
    th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
    a { color: #0b5d58; font-weight: 700; text-decoration: none; }
    .badge {
      display: inline-flex;
      padding: 4px 9px;
      border-radius: 999px;
      background: #e7f3f1;
      color: #0b5d58;
      font-weight: 700;
      font-size: 12px;
    }
    .badge.warn { background: #fff7ed; color: #9a3412; }
    @media (max-width: 980px) {
      header { padding: 22px; align-items: flex-start; flex-direction: column; }
      main { grid-template-columns: 1fr; padding: 18px; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Mandala HyperFrames Studio</h1>
      <p>上传图片或视频片段，输入剪辑提示词，Codex 生成 HyperFrames 视频工程。导出 MP4 后再用剪映人工精修。</p>
    </div>
    <button id="refresh" type="button">刷新</button>
  </header>
  <main>
    <aside class="stack">
      <section class="panel">
        <h2>推荐流程</h2>
        <ol>
          <li>GPT Image 2 生成商品图片。</li>
          <li>Kling 可灵把图片生成 3-5 秒视频片段。</li>
          <li>这里上传图片 / 视频片段 / 可选音乐，并输入剪辑要求。</li>
          <li>Codex 生成带节奏分段、转场、自动运镜和配乐轨的 HyperFrames 工程。</li>
          <li>直接 render 导出 MP4。</li>
          <li>剪映做最后人工微调。</li>
        </ol>
      </section>
      <section class="panel">
        <h2>环境状态</h2>
        <p id="env-status">正在检测...</p>
      </section>
      <section class="panel">
        <h2>提示词模板</h2>
        <p>剪成 15 秒 TikTok 竖版商品短视频。开头 2 秒用产品近景做 hook，中间展示佩戴和叠戴细节，自动加柔和转场、轻微闪白、慢推拉运镜和背景音乐。不要字幕、不要水印、不要品牌文字，文字后期在剪映里人工添加。</p>
      </section>
    </aside>
    <section class="stack">
      <div id="notice" class="notice"></div>
      <section class="panel">
        <h2>生成 HyperFrames 工程</h2>
        <form id="project-form">
          <label>
            项目名称
            <input name="project_name" placeholder="例如：Purple Bracelet TikTok Edit">
          </label>
          <label>
            上传素材
            <input name="media" type="file" accept="video/*,image/*,audio/*,.mp3,.wav,.m4a,.aac" multiple required>
          </label>
          <label>
            视频比例
            <select name="aspect_ratio">
              <option value="9:16">9:16 TikTok / Reels / Shorts</option>
              <option value="4:5">4:5 Instagram / Pinterest</option>
              <option value="1:1">1:1 Square</option>
              <option value="16:9">16:9 YouTube</option>
            </select>
          </label>
          <label>
            剪辑提示词
            <textarea name="prompt" placeholder="写你想要的节奏、时长、镜头顺序和转场。默认不添加字幕、水印、品牌文字或 CTA，方便后续在剪映调整。"></textarea>
          </label>
          <label>
            <span><input name="render_now" type="checkbox" value="1" checked style="width:auto"> 生成后直接渲染 MP4</span>
          </label>
          <button type="submit">生成并剪辑成片</button>
        </form>
        <div id="result" class="result"></div>
      </section>
      <section class="panel">
        <h2>已生成项目</h2>
        <div id="projects"></div>
      </section>
    </section>
  </main>
  <script>
    const noticeEl = document.getElementById("notice");
    const resultEl = document.getElementById("result");
    const projectsEl = document.getElementById("projects");
    const envEl = document.getElementById("env-status");

    function showNotice(message, isError = false) {
      noticeEl.textContent = message;
      noticeEl.style.display = "block";
      noticeEl.style.background = isError ? "#fef2f2" : "#ecfdf5";
      noticeEl.style.color = isError ? "#991b1b" : "#065f46";
    }

    function link(path) {
      return `<a href="/download?path=${encodeURIComponent(path)}">${path}</a>`;
    }

    function renderStatus(payload) {
      const env = payload.environment;
      envEl.innerHTML = env.ready
        ? `<span class="badge">Node / npx 可用</span>`
        : `<span class="badge warn">缺少 Node 或 npx</span>`;
      if (!payload.projects.length) {
        projectsEl.innerHTML = "<p>还没有生成 HyperFrames 工程。</p>";
        return;
      }
      projectsEl.innerHTML = `
        <table>
          <thead><tr><th>项目</th><th>目录</th><th>MP4</th><th>操作</th><th>更新时间</th></tr></thead>
          <tbody>
            ${payload.projects.map(project => `
              <tr>
                <td>${project.title}</td>
                <td>${project.path}</td>
                <td>${project.output_video ? link(project.output_video) : "未渲染"}</td>
                <td><button type="button" data-render="${project.id}">渲染 MP4</button></td>
                <td>${project.updated}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
      document.querySelectorAll("[data-render]").forEach(button => {
        button.addEventListener("click", () => renderProject(button.dataset.render, button));
      });
    }

    async function refresh() {
      const response = await fetch("/api/status");
      renderStatus(await response.json());
    }

    async function createProject(event) {
      event.preventDefault();
      const form = event.currentTarget;
      const button = form.querySelector("button");
      const original = button.textContent;
      const formData = new FormData(form);
      button.disabled = true;
      button.textContent = "生成中";
      showNotice("正在生成 HyperFrames 工程...");
      resultEl.style.display = "none";
      try {
        const response = await fetch("/api/create-project", { method: "POST", body: formData });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "生成失败");
        resultEl.style.display = "block";
        const renderBlock = payload.render_result
          ? `<br>渲染状态：${payload.render_result.status}<br>${payload.render_result.output_video ? "成片：" + link(payload.render_result.output_video) : ""}${payload.render_result.log ? "<br>日志：" + link(payload.render_result.log) : ""}`
          : "";
        resultEl.innerHTML = `
          <strong>${payload.message}</strong><br>
          工程目录：${payload.project_dir}<br>
          Composition：${link(payload.files.composition)}<br>
          说明：${link(payload.files.readme)}
          <span class="code">${payload.commands.preview}</span>
          <span class="code">${payload.commands.render}</span>
          ${renderBlock}
        `;
        showNotice(payload.render_result ? payload.render_result.message : "HyperFrames 工程已生成。可以继续点击渲染 MP4。");
        refresh();
      } catch (error) {
        showNotice(error.message, true);
      } finally {
        button.disabled = false;
        button.textContent = original;
      }
    }

    async function renderProject(projectId, button) {
      const original = button.textContent;
      button.disabled = true;
      button.textContent = "渲染中";
      showNotice("正在调用 HyperFrames 渲染 MP4，首次运行可能需要等待 npm 下载依赖...");
      try {
        const response = await fetch("/api/render-project", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ project_id: projectId })
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "渲染失败");
        resultEl.style.display = "block";
        resultEl.innerHTML = `
          <strong>${payload.message}</strong><br>
          状态：${payload.status}<br>
          ${payload.output_video ? "成片：" + link(payload.output_video) + "<br>" : ""}
          ${payload.log ? "日志：" + link(payload.log) : ""}
        `;
        showNotice(payload.message);
        refresh();
      } catch (error) {
        showNotice(error.message, true);
      } finally {
        button.disabled = false;
        button.textContent = original;
      }
    }

    document.getElementById("project-form").addEventListener("submit", createProject);
    document.getElementById("refresh").addEventListener("click", refresh);
    refresh();
  </script>
</body>
</html>"""


class HyperFramesStudioHandler(BaseHTTPRequestHandler):
    server: "HyperFramesStudioServer"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_text(render_hyperframes_studio(), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/status":
            self.send_json(
                {
                    "environment": hyperframes_available(),
                    "projects": list_hyperframes_projects(self.server.repo_root),
                }
            )
            return
        if parsed.path == "/download":
            self.send_download(parsed.query)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/create-project":
                self.send_json(self.create_project_from_form())
                return
            if parsed.path == "/api/render-project":
                payload = self.read_json()
                self.send_json(render_hyperframes_project(self.server.repo_root, str(payload.get("project_id", ""))))
                return
            self.send_error(404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=400)

    def read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def create_project_from_form(self) -> dict[str, object]:
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
            },
        )
        prompt = form.getfirst("prompt", "")
        project_name = form.getfirst("project_name", "")
        aspect_ratio = form.getfirst("aspect_ratio", "9:16")
        render_now = form.getfirst("render_now", "") == "1"
        raw_media = form["media"] if "media" in form else []
        if not isinstance(raw_media, list):
            raw_media = [raw_media]
        uploads = [
            UploadedMedia(filename=item.filename or "asset", content=item.file.read())
            for item in raw_media
            if getattr(item, "filename", "")
        ]
        result = create_hyperframes_project(self.server.repo_root, uploads, prompt, project_name, aspect_ratio)
        if render_now:
            result["render_result"] = render_hyperframes_project(self.server.repo_root, str(result["project_id"]))
            result["message"] = "HyperFrames project created and render was attempted."
        return result

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
        if not requested.startswith("output/hyperframes_projects/"):
            self.send_error(403)
            return
        file_path = self.server.repo_root / requested
        if not file_path.exists() or file_path.is_dir():
            self.send_error(404)
            return
        body = file_path.read_bytes()
        content_type = "video/mp4" if file_path.suffix.lower() == ".mp4" else "text/plain; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class HyperFramesStudioServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], repo_root: Path):
        super().__init__(server_address, HyperFramesStudioHandler)
        self.repo_root = repo_root


def serve_hyperframes_studio(
    host: str = "127.0.0.1", port: int = 8792, open_browser: bool = True, root: Path | None = None
) -> None:
    repo_root = (root or Path.cwd()).resolve()
    server = HyperFramesStudioServer((host, port), repo_root)
    url = f"http://{host}:{server.server_port}/"
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    print(f"Mandala HyperFrames Studio running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
