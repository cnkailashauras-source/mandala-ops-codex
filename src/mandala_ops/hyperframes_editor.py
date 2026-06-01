from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import wave
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any


MEDIA_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".webm",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac"}


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
        if suffix in AUDIO_EXTENSIONS:
            media_type = "audio"
        elif suffix in VIDEO_EXTENSIONS:
            media_type = "video"
        else:
            media_type = "image"
        assets.append(
            {
                "filename": name,
                "path": f"assets/{name}",
                "type": media_type,
            }
        )
    if not [asset for asset in assets if asset["type"] in {"image", "video"}]:
        raise ValueError("Please upload at least one image or video asset.")
    return assets


def headline_from_prompt(prompt: str) -> str:
    text = " ".join(prompt.split())
    if not text:
        return "Mandala Jewels"
    first = re.split(r"[。.!?\n]", text)[0].strip()
    return first[:72] or "Mandala Jewels"


def visual_assets(assets: list[dict[str, str]]) -> list[dict[str, str]]:
    return [asset for asset in assets if asset["type"] in {"image", "video"}]


def audio_assets(assets: list[dict[str, str]]) -> list[dict[str, str]]:
    return [asset for asset in assets if asset["type"] == "audio"]


def wants_auto_music(prompt: str) -> bool:
    lowered = prompt.lower()
    blocked = ["不要音乐", "无音乐", "no music", "without music", "mute", "silent"]
    return not any(item in lowered for item in blocked)


def scene_count_for(duration: int, asset_count: int) -> int:
    target = max(5, min(9, round(duration / 2)))
    return max(target, min(asset_count, 9))


def scene_plan(assets: list[dict[str, str]], duration: int) -> list[dict[str, object]]:
    visuals = visual_assets(assets)
    count = scene_count_for(duration, len(visuals))
    overlap = 0.42
    base_slot = duration / count
    plan: list[dict[str, object]] = []
    for index in range(count):
        start = round(index * base_slot, 2)
        next_start = duration if index == count - 1 else (index + 1) * base_slot
        length = round(max(1.2, next_start - start + (overlap if index < count - 1 else 0)), 2)
        plan.append(
            {
                "index": index,
                "asset": visuals[index % len(visuals)],
                "start": start,
                "duration": min(length, round(duration - start, 2)),
                "entrance": ["soft", "slide-left", "slide-right", "push-in"][index % 4],
                "crop": index % 5,
            }
        )
    return plan


def media_tracks(assets: list[dict[str, str]], duration: int) -> str:
    tracks = []
    for item in scene_plan(assets, duration):
        index = int(item["index"])
        asset = item["asset"]
        start = item["start"]
        length = item["duration"]
        if length <= 0:
            continue
        classes = f'clip media media-{index % 3} crop-{item["crop"]} entrance-{item["entrance"]}'
        if asset["type"] == "video":
            tag = (
                f'<video id="media-{index + 1}" class="{classes}" src="{escape(asset["path"])}" '
                f'data-start="{start}" data-duration="{length}" data-track-index="{index}" autoplay muted playsinline></video>'
            )
        else:
            tag = (
                f'<img id="media-{index + 1}" class="{classes}" src="{escape(asset["path"])}" '
                f'data-start="{start}" data-duration="{length}" data-track-index="{index}" alt="">'
            )
        tracks.append(tag)
    return "\n      ".join(tracks)


def transition_tracks(duration: int, count: int) -> str:
    if count <= 1:
        return ""
    slot = duration / count
    tracks = []
    for index in range(1, count):
        start = round(max(0, index * slot - 0.24), 2)
        tracks.append(
            f'<div id="transition-{index}" class="clip transition transition-{index % 3}" '
            f'data-start="{start}" data-duration="0.5" data-track-index="{20 + index}"></div>'
        )
    return "\n      ".join(tracks)


def ambient_tracks(duration: int) -> str:
    return "\n      ".join(
        [
            f'<div id="grain" class="clip grain" data-start="0" data-duration="{duration}" data-track-index="30"></div>',
            f'<div id="light-leak" class="clip light-leak" data-start="0" data-duration="{duration}" data-track-index="31"></div>',
        ]
    )


def music_track(assets: list[dict[str, str]], duration: int) -> str:
    audios = audio_assets(assets)
    if not audios:
        return ""
    src = escape(audios[0]["path"])
    return (
        f'<audio id="bgm" class="clip bgm" src="{src}" data-start="0" '
        f'data-duration="{duration}" data-track-index="40" data-volume="0.22"></audio>'
    )


def timeline_script(duration: int, count: int) -> str:
    lines = [
        "const tl = gsap.timeline({ paused: true, defaults: { ease: 'power2.out' } });",
        'tl.set("#root", { opacity: 1 }, 0);',
    ]
    for index in range(count):
        selector = f"#media-{index + 1}"
        start = round(index * duration / count, 2)
        lines.append(f"tl.from('{selector}', {{ opacity: 0, scale: 1.08, duration: 0.32, ease: 'sine.out' }}, {start});")
        lines.append(
            f"tl.fromTo('{selector}', {{ scale: 1.04, xPercent: {[-2, 2, 0, -1][index % 4]} }}, "
            f"{{ scale: 1.14, xPercent: {[2, -2, 1, 0][index % 4]}, duration: {max(1.2, duration / count):.2f}, ease: 'none' }}, {start});"
        )
    for index in range(1, count):
        start = round(max(0, index * duration / count - 0.24), 2)
        lines.append(f"tl.fromTo('#transition-{index}', {{ opacity: 0 }}, {{ opacity: 0.72, duration: 0.16, ease: 'power1.out' }}, {start});")
        lines.append(f"tl.to('#transition-{index}', {{ opacity: 0, duration: 0.34, ease: 'sine.out' }}, {round(start + 0.16, 2)});")
    lines.append("tl.fromTo('#light-leak', { xPercent: -45, opacity: 0.08 }, { xPercent: 35, opacity: 0.2, duration: %.2f, ease: 'sine.inOut' }, 0);" % duration)
    lines.append(f"tl.to('#root', {{ opacity: 0.96, duration: 0.35, ease: 'sine.inOut' }}, {max(0, duration - 0.35):.2f});")
    lines.append(f"tl.to('#timeline-end', {{ opacity: 1, duration: 0.01 }}, {duration});")
    lines.append("window.__timelines = window.__timelines || {};")
    lines.append('window.__timelines["root"] = tl;')
    return "\n        ".join(lines)


def add_auto_music(project_dir: Path, assets: list[dict[str, str]], prompt: str, duration: int) -> list[dict[str, str]]:
    if audio_assets(assets) or not wants_auto_music(prompt):
        return assets
    assets_dir = project_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    music_path = assets_dir / "auto_soft_beat.wav"
    generate_soft_beat(music_path, duration)
    return assets + [{"filename": music_path.name, "path": f"assets/{music_path.name}", "type": "audio"}]


def generate_soft_beat(path: Path, duration: int) -> None:
    sample_rate = 44100
    total = int(duration * sample_rate)
    bpm = 92
    beat = sample_rate * 60 / bpm
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        for n in range(total):
            t = n / sample_rate
            chord = (
                0.20 * math.sin(2 * math.pi * 220 * t)
                + 0.12 * math.sin(2 * math.pi * 277.18 * t)
                + 0.10 * math.sin(2 * math.pi * 329.63 * t)
            )
            pulse_position = (n % int(beat)) / beat
            pulse = max(0.0, 1.0 - pulse_position * 9)
            shimmer = 0.04 * math.sin(2 * math.pi * 880 * t) * max(0.0, 1.0 - pulse_position * 16)
            envelope = min(1.0, t / 1.5, (duration - t) / 1.8 if duration - t < 1.8 else 1.0)
            sample = int(max(-1, min(1, (chord * 0.16 + pulse * 0.14 + shimmer) * envelope)) * 32767)
            frames += sample.to_bytes(2, byteorder="little", signed=True)
        handle.writeframes(frames)


def render_composition_html(
    assets: list[dict[str, str]],
    prompt: str,
    aspect_ratio: str,
    duration: int,
) -> str:
    width, height = resolution_for_aspect(aspect_ratio)
    scenes = scene_plan(assets, duration)
    count = len(scenes)
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
      will-change: transform, opacity, filter;
    }}
    .crop-1 {{ object-position: 45% 50%; }}
    .crop-2 {{ object-position: 55% 45%; }}
    .crop-3 {{ object-position: 50% 58%; }}
    .crop-4 {{ object-position: 48% 42%; }}
    .veil {{
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, rgba(5,12,10,.18), rgba(5,12,10,.04) 42%, rgba(5,12,10,.72));
      z-index: 20;
    }}
    .transition {{
      position: absolute;
      inset: 0;
      z-index: 35;
      opacity: 0;
      pointer-events: none;
      background: radial-gradient(circle at 35% 45%, rgba(255,255,255,.92), rgba(255,255,255,.18) 34%, rgba(255,255,255,0) 68%);
      mix-blend-mode: screen;
    }}
    .transition-1 {{ backdrop-filter: blur(10px); }}
    .transition-2 {{ background: linear-gradient(100deg, rgba(255,255,255,0), rgba(255,255,255,.72), rgba(255,255,255,0)); }}
    .grain {{
      position: absolute;
      inset: 0;
      z-index: 32;
      opacity: .08;
      pointer-events: none;
      background-image:
        radial-gradient(circle at 20% 30%, rgba(255,255,255,.24) 0 1px, rgba(255,255,255,0) 1px),
        radial-gradient(circle at 70% 65%, rgba(255,255,255,.18) 0 1px, rgba(255,255,255,0) 1px);
      background-size: 7px 7px, 11px 11px;
    }}
    .light-leak {{
      position: absolute;
      inset: -18% -35%;
      z-index: 33;
      opacity: .12;
      pointer-events: none;
      background:
        radial-gradient(circle at 20% 25%, rgba(219,177,124,.7), rgba(219,177,124,0) 32%),
        radial-gradient(circle at 70% 60%, rgba(152,115,255,.42), rgba(152,115,255,0) 26%);
      mix-blend-mode: screen;
    }}
  </style>
</head>
<body>
  <div id="root" class="composition" data-composition-id="root" data-start="0" data-width="{width}" data-height="{height}" data-fps="30">
      {media_tracks(assets, duration)}
      {transition_tracks(duration, count)}
      {ambient_tracks(duration)}
      {music_track(assets, duration)}
      <div id="veil" class="clip veil" data-start="0" data-duration="{duration}"></div>
      <div id="timeline-end" style="opacity:0; position:absolute; width:1px; height:1px;"></div>
      <script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
      <script>
        {timeline_script(duration, count)}
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
    assets = add_auto_music(project_dir, assets, prompt, duration)
    html = render_composition_html(assets, prompt, aspect_ratio, duration)
    (project_dir / "index.html").write_text(html, encoding="utf-8")
    legacy_comp = project_dir / "comp.html"
    if legacy_comp.exists():
        legacy_comp.unlink()

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
        "composition": (project_dir / "index.html").as_posix(),
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
