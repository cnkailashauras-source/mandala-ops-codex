from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any


MEDIA_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}


@dataclass(frozen=True)
class UploadedMedia:
    filename: str
    content: bytes


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return slug or "hyperframes-edit"


def target_seconds_from_prompt(prompt: str, default: int = 15) -> int:
    match = re.search(r"(\d{1,3})\s*(?:s|sec|second|seconds|秒)", prompt, flags=re.IGNORECASE)
    if not match:
        return default
    return max(5, min(120, int(match.group(1))))


def resolution_for_aspect(aspect_ratio: str) -> tuple[int, int]:
    if aspect_ratio == "1:1":
        return 1080, 1080
    if aspect_ratio == "4:5":
        return 1080, 1350
    if aspect_ratio == "16:9":
        return 1920, 1080
    return 1080, 1920


def safe_filename(filename: str, index: int) -> str:
    clean = re.sub(r"[^a-zA-Z0-9._-]+", "-", Path(filename).name).strip("-._")
    suffix = Path(clean).suffix.lower()
    if suffix not in MEDIA_EXTENSIONS:
        raise ValueError(f"Unsupported media file: {filename}")
    return f"{index:02d}_{clean or f'asset{suffix}'}"


def save_media(project_dir: Path, uploads: list[UploadedMedia]) -> list[dict[str, str]]:
    assets_dir = project_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    assets: list[dict[str, str]] = []
    for index, upload in enumerate(uploads, start=1):
        name = safe_filename(upload.filename, index)
        path = assets_dir / name
        path.write_bytes(upload.content)
        suffix = path.suffix.lower()
        assets.append(
            {
                "filename": name,
                "path": f"assets/{name}",
                "type": "video" if suffix in VIDEO_EXTENSIONS else "image",
            }
        )
    if not assets:
        raise ValueError("Please upload at least one image or video asset.")
    return assets


def headline_from_prompt(prompt: str) -> str:
    text = " ".join(prompt.split())
    if not text:
        return "Mandala Jewels"
    first = re.split(r"[。.!?\n]", text)[0].strip()
    return first[:72] or "Mandala Jewels"


def media_tracks(assets: list[dict[str, str]], duration: int) -> str:
    slot = max(2.5, duration / max(len(assets), 1))
    tracks = []
    for index, asset in enumerate(assets):
        start = round(index * slot, 2)
        length = round(min(slot + 0.35, duration - start), 2)
        if length <= 0:
            continue
        if asset["type"] == "video":
            tag = (
                f'<video id="media-{index + 1}" class="clip media media-{index % 3}" src="{escape(asset["path"])}" '
                f'data-start="{start}" data-duration="{length}" data-track-index="0" autoplay muted playsinline></video>'
            )
        else:
            tag = (
                f'<img id="media-{index + 1}" class="clip media media-{index % 3}" src="{escape(asset["path"])}" '
                f'data-start="{start}" data-duration="{length}" data-track-index="0" alt="">'
            )
        tracks.append(tag)
    return "\n      ".join(tracks)


def render_composition_html(
    assets: list[dict[str, str]],
    prompt: str,
    aspect_ratio: str,
    duration: int,
) -> str:
    width, height = resolution_for_aspect(aspect_ratio)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mandala HyperFrames Edit</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #071512; font-family: Arial, Helvetica, sans-serif; }}
    .composition {{
      position: relative;
      width: {width}px;
      height: {height}px;
      overflow: hidden;
      background: #071512;
      color: #fff;
    }}
    .media {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      filter: contrast(1.04) saturate(1.06);
      transform-origin: center;
      animation: slowZoom linear both;
    }}
    .media-1 {{ animation-name: driftLeft; }}
    .media-2 {{ animation-name: driftRight; }}
    .veil {{
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, rgba(5,12,10,.18), rgba(5,12,10,.04) 42%, rgba(5,12,10,.72));
      z-index: 20;
    }}
    @keyframes slowZoom {{
      from {{ transform: scale(1.02); }}
      to {{ transform: scale(1.12); }}
    }}
    @keyframes driftLeft {{
      from {{ transform: scale(1.12) translateX(2%); }}
      to {{ transform: scale(1.04) translateX(-2%); }}
    }}
    @keyframes driftRight {{
      from {{ transform: scale(1.04) translateX(-2%); }}
      to {{ transform: scale(1.12) translateX(2%); }}
    }}
  </style>
</head>
<body>
  <div id="root" class="composition" data-composition-id="root" data-start="0" data-width="{width}" data-height="{height}" data-fps="30">
      {media_tracks(assets, duration)}
      <div id="veil" class="clip veil" data-start="0" data-duration="{duration}"></div>
      <div id="timeline-end" style="opacity:0; position:absolute; width:1px; height:1px;"></div>
      <script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
      <script>
        const tl = gsap.timeline({{ paused: true }});
        tl.set("#root", {{ opacity: 1 }}, 0);
        tl.to("#timeline-end", {{ opacity: 1, duration: 0.01 }}, {duration});
        window.__timelines = window.__timelines || {{}};
        window.__timelines["root"] = tl;
      </script>
  </div>
</body>
</html>
"""


def write_project_files(
    project_dir: Path,
    project_name: str,
    assets: list[dict[str, str]],
    prompt: str,
    aspect_ratio: str,
    duration: int,
) -> dict[str, str]:
    html = render_composition_html(assets, prompt, aspect_ratio, duration)
    (project_dir / "comp.html").write_text(html, encoding="utf-8")
    (project_dir / "index.html").write_text(html, encoding="utf-8")

    package = {
        "scripts": {
            "preview": "npx --yes hyperframes preview .",
            "lint": "npx --yes hyperframes lint .",
            "render": "npx --yes hyperframes render . --output output.mp4",
        },
        "devDependencies": {"hyperframes": "latest"},
    }
    (project_dir / "package.json").write_text(json.dumps(package, indent=2), encoding="utf-8")

    manifest = {
        "project_name": project_name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "duration_seconds": duration,
        "assets": assets,
        "commands": package["scripts"],
    }
    (project_dir / "hyperframes_job.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (project_dir / "README.md").write_text(
        "\n".join(
            [
                f"# {project_name}",
                "",
                "This is a Codex-generated HyperFrames project for Mandala Jewels social video editing.",
                "",
                "## Preview",
                "",
                "```powershell",
                "npx --yes hyperframes preview .",
                "```",
                "",
                "## Render MP4",
                "",
                "```powershell",
                "npx --yes hyperframes render . --output output.mp4",
                "```",
                "",
                "## Editing Prompt",
                "",
                prompt or "No prompt provided.",
                "",
                "## Notes",
                "",
                "- Review all text and product appearance before publishing.",
                "- Exported MP4 can be opened in CapCut / Jianying for final manual polish.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "composition": (project_dir / "comp.html").as_posix(),
        "readme": (project_dir / "README.md").as_posix(),
        "manifest": (project_dir / "hyperframes_job.json").as_posix(),
        "package": (project_dir / "package.json").as_posix(),
    }


def create_hyperframes_project(
    root: Path,
    uploads: list[UploadedMedia],
    prompt: str,
    project_name: str = "",
    aspect_ratio: str = "9:16",
) -> dict[str, object]:
    name = project_name.strip() or headline_from_prompt(prompt) or "Mandala HyperFrames Edit"
    job_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{slugify(name)[:36]}"
    project_dir = root / "output/hyperframes_projects" / job_id
    project_dir.mkdir(parents=True, exist_ok=True)
    assets = save_media(project_dir, uploads)
    duration = target_seconds_from_prompt(prompt)
    files = write_project_files(project_dir, name, assets, prompt, aspect_ratio, duration)

    relative_project = project_dir.relative_to(root).as_posix()
    relative_files = {key: str(Path(path).relative_to(root).as_posix()) for key, path in files.items()}
    return {
        "project_id": job_id,
        "project_dir": relative_project,
        "message": "HyperFrames project created.",
        "files": relative_files,
        "commands": {
            "preview": f"cd {relative_project} && npx --yes hyperframes preview .",
            "render": f"cd {relative_project} && npx --yes hyperframes render . --output output.mp4",
            "lint": f"cd {relative_project} && npx --yes hyperframes lint .",
        },
    }


def project_dir_from_id(root: Path, project_id: str) -> Path:
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", project_id):
        raise ValueError("Invalid HyperFrames project id.")
    project_dir = root / "output/hyperframes_projects" / project_id
    if not project_dir.exists() or not project_dir.is_dir():
        raise ValueError(f"HyperFrames project not found: {project_id}")
    return project_dir


def render_hyperframes_project(root: Path, project_id: str, timeout_seconds: int = 600) -> dict[str, object]:
    project_dir = project_dir_from_id(root, project_id)
    refresh_project_files(project_dir)
    npx = shutil.which("npx")
    if not npx:
        return {
            "project_id": project_id,
            "status": "Missing npx",
            "message": "Node / npx is not available, so MP4 rendering cannot run.",
            "output_video": "",
        }
    output_path = project_dir / "output.mp4"
    log_path = project_dir / "render_log.txt"
    command = [npx, "--yes", "hyperframes", "render", ".", "--output", "output.mp4"]
    env = render_environment(root)
    try:
        completed = subprocess.run(
            command,
            cwd=project_dir,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_seconds,
            check=False,
        )
        log_path.write_text(render_log_header(command, project_dir, env) + (completed.stdout or ""), encoding="utf-8")
        if completed.returncode != 0 or not output_path.exists():
            return {
                "project_id": project_id,
                "status": "Render Failed",
                "message": "HyperFrames render failed. The project was saved, and the render log is available.",
                "output_video": "",
                "log": log_path.relative_to(root).as_posix(),
                "return_code": completed.returncode,
            }
        return {
            "project_id": project_id,
            "status": "Rendered",
            "message": "MP4 render completed.",
            "output_video": output_path.relative_to(root).as_posix(),
            "log": log_path.relative_to(root).as_posix(),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or "Render timed out."
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="ignore")
        log_path.write_text(render_log_header(command, project_dir, env) + stdout, encoding="utf-8")
        return {
            "project_id": project_id,
            "status": "Render Timeout",
            "message": "HyperFrames render timed out. Try rendering this project manually from the terminal.",
            "output_video": "",
            "log": log_path.relative_to(root).as_posix(),
        }


def refresh_project_files(project_dir: Path) -> None:
    manifest_path = project_dir / "hyperframes_job.json"
    if not manifest_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    assets = manifest.get("assets") or []
    if not isinstance(assets, list):
        return
    write_project_files(
        project_dir,
        str(manifest.get("project_name") or project_dir.name),
        assets,
        str(manifest.get("prompt") or ""),
        str(manifest.get("aspect_ratio") or "9:16"),
        int(manifest.get("duration_seconds") or 15),
    )


def list_hyperframes_projects(root: Path) -> list[dict[str, str]]:
    base = root / "output/hyperframes_projects"
    if not base.exists():
        return []
    projects = []
    for path in sorted(base.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_dir():
            continue
        manifest_path = path / "hyperframes_job.json"
        title = path.name
        if manifest_path.exists():
            try:
                title = json.loads(manifest_path.read_text(encoding="utf-8")).get("project_name", title)
            except json.JSONDecodeError:
                pass
        projects.append(
            {
                "id": path.name,
                "title": title,
                "path": path.relative_to(root).as_posix(),
                "output_video": (path / "output.mp4").relative_to(root).as_posix() if (path / "output.mp4").exists() else "",
                "render_log": (path / "render_log.txt").relative_to(root).as_posix()
                if (path / "render_log.txt").exists()
                else "",
                "updated": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            }
        )
    return projects


def hyperframes_available() -> dict[str, str | bool]:
    node = shutil.which("node")
    npx = shutil.which("npx")
    ffmpeg = find_ffmpeg()
    ffprobe = find_ffprobe()
    return {
        "node": node or "",
        "npx": npx or "",
        "ffmpeg": ffmpeg or "",
        "ffprobe": ffprobe or "",
        "ready": bool(node and npx and ffmpeg and ffprobe),
    }


def find_ffmpeg() -> str | None:
    ffmpeg = find_executable("ffmpeg.exe")
    if ffmpeg:
        return ffmpeg
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def find_ffprobe() -> str | None:
    return find_executable("ffprobe.exe")


def find_executable(name: str) -> str | None:
    command = shutil.which(Path(name).stem)
    if command:
        return command
    local = __import__("os").environ.get("LOCALAPPDATA")
    if not local:
        return None
    packages = Path(local) / "Microsoft/WinGet/Packages"
    if not packages.exists():
        return None
    matches = sorted(packages.glob(f"**/{name}"), key=lambda path: path.stat().st_mtime, reverse=True)
    return str(matches[0]) if matches else None


def render_environment(root: Path | None = None) -> dict[str, str]:
    env = dict(__import__("os").environ)
    ffmpeg = find_ffmpeg()
    ffprobe = find_ffprobe()
    if ffprobe:
        env["PATH"] = str(Path(ffprobe).parent) + __import__("os").pathsep + env.get("PATH", "")
    if ffmpeg:
        ffmpeg_path = Path(ffmpeg)
        if not ffmpeg_path.exists():
            return env
        if ffmpeg_path.name.lower() != "ffmpeg.exe" and root:
            shim_dir = root / "output/runtime/ffmpeg"
            shim_dir.mkdir(parents=True, exist_ok=True)
            shim_path = shim_dir / "ffmpeg.exe"
            if not shim_path.exists() or shim_path.stat().st_size != ffmpeg_path.stat().st_size:
                shutil.copy2(ffmpeg_path, shim_path)
            ffmpeg_dir = str(shim_dir)
        else:
            ffmpeg_dir = str(ffmpeg_path.parent)
        env["PATH"] = ffmpeg_dir + __import__("os").pathsep + env.get("PATH", "")
    return env


def render_log_header(command: list[str], project_dir: Path, env: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Command: {' '.join(command)}",
            f"Working directory: {project_dir}",
            f"FFmpeg: {find_ffmpeg() or 'not found'}",
            f"FFprobe: {find_ffprobe() or 'not found'}",
            f"PATH begins: {env.get('PATH', '')[:300]}",
            "",
            "---- HyperFrames output ----",
            "",
        ]
    )
